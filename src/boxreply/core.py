"""Offline, conservative reconciliation of departmental box-review returns.

Hashes bind a review to its source snapshot. They provide integrity checking,
not identity verification or authorization to dispose of records.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any


class BoxReplyError(ValueError):
    """An input violates the supported review-round contract."""


BOX_FIELDS = (
    "box_id", "department", "record_series", "description",
    "proposed_action", "proposed_date",
)
REVIEWER_FIELDS = ("department", "reviewer_id", "reviewer_name")
MAX_INPUT_BYTES = 5 * 1024 * 1024
MAX_BOXES = 10_000
MAX_REVIEWERS = 100
MAX_ASSIGNMENTS = 10_000
MAX_REQUIRED_DECISIONS = 50_000
MAX_FIELD_CHARS = 5_000
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}\Z", re.ASCII)
_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z", re.ASCII)
_HASH = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
_DECISIONS = {"", "no_exception", "exception", "needs_correction"}
_MANIFEST_KEYS = {
    "schema", "round_id", "boxes", "reviewers", "sources", "manifest_sha256",
}
_RESPONSE_KEYS = {
    "round_id", "manifest_sha256", "reviewer_id", "reviewer_name",
    "submitted_by", "submitted_on", "rows",
}


def _object(value: Any, keys: set[str], label: str) -> dict:
    if type(value) is not dict or set(value) != keys:
        raise BoxReplyError(f"{label} must have exactly these fields: {', '.join(sorted(keys))}")
    return value


def _text(value: Any, label: str, *, blank: bool = False) -> str:
    if type(value) is not str:
        raise BoxReplyError(f"{label} must be text")
    if len(value) > MAX_FIELD_CHARS:
        raise BoxReplyError(f"{label} exceeds {MAX_FIELD_CHARS} characters")
    if (not value and not blank) or value != value.strip():
        raise BoxReplyError(f"{label} must {'be nonempty and ' if not blank else ''}have no surrounding whitespace")
    if any(unicodedata.category(ch) in {"Cc", "Cf", "Cs"} for ch in value):
        raise BoxReplyError(f"{label} contains a control, format, or surrogate character")
    return value


def _identifier(value: Any, label: str) -> str:
    _text(value, label)
    if not _ID.fullmatch(value):
        raise BoxReplyError(f"{label} must match [A-Za-z0-9][A-Za-z0-9_.-]{{0,79}}")
    return value


def _date(value: Any, label: str, *, blank: bool = False) -> str:
    _text(value, label, blank=blank)
    if blank and not value:
        return value
    if not _DATE.fullmatch(value):
        raise BoxReplyError(f"{label} must be an ISO date YYYY-MM-DD")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise BoxReplyError(f"{label} is not a valid calendar date") from exc
    return value


def _hash(value: Any, label: str) -> str:
    if type(value) is not str or not _HASH.fullmatch(value):
        raise BoxReplyError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _box(value: Any, label: str) -> dict:
    _object(value, set(BOX_FIELDS), label)
    for field in BOX_FIELDS:
        _text(value[field], f"{label}.{field}")
    _identifier(value["box_id"], f"{label}.box_id")
    _date(value["proposed_date"], f"{label}.proposed_date")
    if value["proposed_action"] not in {"destroy", "transfer"}:
        raise BoxReplyError(f"{label}.proposed_action must be destroy or transfer")
    return value


def _csv(path: Path, fields: tuple[str, ...], max_rows: int, label: str) -> tuple[list[dict], str]:
    if not isinstance(path, (str, Path)):
        raise BoxReplyError(f"{label} path must be a path or string")
    try:
        with Path(path).open("rb") as stream:
            raw = stream.read(MAX_INPUT_BYTES + 1)
    except (OSError, ValueError) as exc:
        raise BoxReplyError(f"Cannot read {label} CSV: {exc}") from exc
    if len(raw) > MAX_INPUT_BYTES:
        raise BoxReplyError(f"{label} CSV exceeds {MAX_INPUT_BYTES} bytes")
    try:
        content = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise BoxReplyError(f"{label} CSV must be UTF-8, with an optional leading BOM") from exc
    rows: list[dict] = []
    try:
        reader = csv.reader(io.StringIO(content, newline=""), strict=True)
        if next(reader, None) != list(fields):
            raise BoxReplyError(f"{label} CSV header must be exactly: {','.join(fields)}")
        for number, values in enumerate(reader, start=2):
            if len(rows) >= max_rows:
                raise BoxReplyError(f"{label} CSV exceeds {max_rows} data rows")
            if len(values) != len(fields):
                raise BoxReplyError(f"{label} CSV row {number} has the wrong number of columns")
            for field, value in zip(fields, values):
                _text(value, f"{label} CSV row {number}.{field}")
            rows.append(dict(zip(fields, values)))
    except csv.Error as exc:
        raise BoxReplyError(f"Malformed {label} CSV: {exc}") from exc
    if not rows:
        raise BoxReplyError(f"{label} CSV must contain at least one data row")
    return rows, hashlib.sha256(raw).hexdigest()


def _digest(manifest: dict) -> str:
    body = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    encoded = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def prepare(boxes_path: Path, reviewers_path: Path, round_id: str) -> dict:
    """Read fixed-contract CSV files and return a canonical frozen manifest."""
    _identifier(round_id, "round_id")
    boxes, boxes_sha = _csv(boxes_path, BOX_FIELDS, MAX_BOXES, "boxes")
    assignments, reviewers_sha = _csv(reviewers_path, REVIEWER_FIELDS, MAX_ASSIGNMENTS, "reviewers")
    grouped: dict[str, dict] = {}
    pairs: set[tuple[str, str]] = set()
    for number, row in enumerate(assignments, start=2):
        reviewer_id = _identifier(row["reviewer_id"], f"reviewers CSV row {number}.reviewer_id")
        pair = (row["department"], reviewer_id)
        if pair in pairs:
            raise BoxReplyError(f"Duplicate department/reviewer assignment: {pair[0]} / {pair[1]}")
        pairs.add(pair)
        if reviewer_id not in grouped:
            grouped[reviewer_id] = {
                "reviewer_id": reviewer_id,
                "reviewer_name": row["reviewer_name"],
                "departments": [],
            }
        elif grouped[reviewer_id]["reviewer_name"] != row["reviewer_name"]:
            raise BoxReplyError(f"Reviewer {reviewer_id} has inconsistent names")
        grouped[reviewer_id]["departments"].append(row["department"])
    for reviewer in grouped.values():
        reviewer["departments"].sort()
    manifest = {
        "schema": 1,
        "round_id": round_id,
        "boxes": sorted(boxes, key=lambda row: row["box_id"]),
        "reviewers": [grouped[key] for key in sorted(grouped)],
        "sources": {"boxes_sha256": boxes_sha, "reviewers_sha256": reviewers_sha},
    }
    manifest["manifest_sha256"] = _digest(manifest)
    validate_manifest(manifest)
    return manifest


def validate_manifest(manifest: Any) -> None:
    """Reject malformed, noncanonical, internally inconsistent or changed manifests."""
    _object(manifest, _MANIFEST_KEYS, "manifest")
    if type(manifest["schema"]) is not int or manifest["schema"] != 1:
        raise BoxReplyError("manifest.schema must be 1")
    _identifier(manifest["round_id"], "manifest.round_id")
    _hash(manifest["manifest_sha256"], "manifest.manifest_sha256")
    sources = _object(manifest["sources"], {"boxes_sha256", "reviewers_sha256"}, "manifest.sources")
    for name, value in sources.items():
        _hash(value, f"manifest.sources.{name}")
    boxes = manifest["boxes"]
    if type(boxes) is not list or not 1 <= len(boxes) <= MAX_BOXES:
        raise BoxReplyError(f"manifest.boxes must contain 1 to {MAX_BOXES} boxes")
    ids = []
    departments = set()
    for number, box in enumerate(boxes):
        _box(box, f"manifest.boxes[{number}]")
        ids.append(box["box_id"])
        departments.add(box["department"])
    if len(set(ids)) != len(ids):
        raise BoxReplyError("manifest contains duplicate box IDs")
    if ids != sorted(ids):
        raise BoxReplyError("manifest boxes must be sorted by box_id")
    reviewers = manifest["reviewers"]
    if type(reviewers) is not list or not 1 <= len(reviewers) <= MAX_REVIEWERS:
        raise BoxReplyError(f"manifest.reviewers must contain 1 to {MAX_REVIEWERS} reviewers")
    reviewer_ids = []
    assigned_departments = set()
    assignment_count = 0
    for number, reviewer in enumerate(reviewers):
        label = f"manifest.reviewers[{number}]"
        _object(reviewer, {"reviewer_id", "reviewer_name", "departments"}, label)
        reviewer_ids.append(_identifier(reviewer["reviewer_id"], f"{label}.reviewer_id"))
        _text(reviewer["reviewer_name"], f"{label}.reviewer_name")
        assigned = reviewer["departments"]
        if type(assigned) is not list or not 1 <= len(assigned) <= MAX_ASSIGNMENTS:
            raise BoxReplyError(f"{label}.departments must be a nonempty list")
        for department in assigned:
            _text(department, f"{label}.departments")
        if len(set(assigned)) != len(assigned) or assigned != sorted(assigned):
            raise BoxReplyError(f"{label}.departments must be unique and sorted")
        assignment_count += len(assigned)
        assigned_departments.update(assigned)
    if assignment_count > MAX_ASSIGNMENTS:
        raise BoxReplyError(f"manifest exceeds {MAX_ASSIGNMENTS} department/reviewer assignments")
    if len(set(reviewer_ids)) != len(reviewer_ids):
        raise BoxReplyError("manifest contains duplicate reviewer IDs")
    if reviewer_ids != sorted(reviewer_ids):
        raise BoxReplyError("manifest reviewers must be sorted by reviewer_id")
    if departments != assigned_departments:
        raise BoxReplyError("Every box department must have reviewers, with no extra assigned departments")
    reviewer_counts = {department: 0 for department in departments}
    for reviewer in reviewers:
        for department in reviewer["departments"]:
            reviewer_counts[department] += 1
    if sum(reviewer_counts[box["department"]] for box in boxes) > MAX_REQUIRED_DECISIONS:
        raise BoxReplyError(f"manifest exceeds {MAX_REQUIRED_DECISIONS} required box/reviewer decisions")
    if _digest(manifest) != manifest["manifest_sha256"]:
        raise BoxReplyError("Manifest digest mismatch: the review snapshot has changed")


def expected_boxes(manifest: dict, reviewer_id: str) -> list[dict]:
    """Return independent copies of the boxes assigned to one known reviewer."""
    validate_manifest(manifest)
    _identifier(reviewer_id, "reviewer_id")
    reviewer = next((item for item in manifest["reviewers"] if item["reviewer_id"] == reviewer_id), None)
    if reviewer is None:
        raise BoxReplyError(f"Unknown reviewer_id: {reviewer_id}")
    departments = set(reviewer["departments"])
    return [dict(box) for box in manifest["boxes"] if box["department"] in departments]


def reconcile(manifest: dict, responses: list[dict]) -> dict:
    """Reconcile complete return files; missing/blank decisions remain incomplete.

    A no_exception result reports reviewer statements, never legal approval.
    An exception takes status precedence, without hiding outstanding replies.
    """
    validate_manifest(manifest)
    if type(responses) is not list or len(responses) > MAX_REVIEWERS:
        raise BoxReplyError(f"responses must be a list of at most {MAX_REVIEWERS} returns")
    reviewers = {reviewer["reviewer_id"]: reviewer for reviewer in manifest["reviewers"]}
    reviewer_departments = {reviewer_id: set(reviewer["departments"])
                            for reviewer_id, reviewer in reviewers.items()}
    source_boxes = {box["box_id"]: box for box in manifest["boxes"]}
    returned: dict[str, dict] = {}
    decisions: dict[tuple[str, str], dict] = {}
    for number, response in enumerate(responses):
        label = f"responses[{number}]"
        _object(response, _RESPONSE_KEYS, label)
        if type(response["round_id"]) is not str or response["round_id"] != manifest["round_id"]:
            raise BoxReplyError(f"{label} belongs to a different round")
        if type(response["manifest_sha256"]) is not str or response["manifest_sha256"] != manifest["manifest_sha256"]:
            raise BoxReplyError(f"{label} belongs to a different manifest snapshot")
        reviewer_id = _identifier(response["reviewer_id"], f"{label}.reviewer_id")
        if reviewer_id not in reviewers:
            raise BoxReplyError(f"{label} has an unknown reviewer_id")
        if reviewer_id in returned:
            raise BoxReplyError(f"Duplicate submission for reviewer {reviewer_id}; select one return explicitly")
        reviewer = reviewers[reviewer_id]
        if type(response["reviewer_name"]) is not str or response["reviewer_name"] != reviewer["reviewer_name"]:
            raise BoxReplyError(f"{label}.reviewer_name differs from the assigned reviewer name")
        _text(response["submitted_by"], f"{label}.submitted_by", blank=True)
        _date(response["submitted_on"], f"{label}.submitted_on", blank=True)
        if bool(response["submitted_by"]) != bool(response["submitted_on"]):
            raise BoxReplyError(f"{label} must supply submitted_by and submitted_on together")
        rows = response["rows"]
        if type(rows) is not list or len(rows) > MAX_BOXES:
            raise BoxReplyError(f"{label}.rows must be a list of at most {MAX_BOXES} boxes")
        assigned = {box_id for box_id, box in source_boxes.items()
                    if box["department"] in reviewer_departments[reviewer_id]}
        seen = set()
        answered = False
        for row_number, row in enumerate(rows):
            row_label = f"{label}.rows[{row_number}]"
            _object(row, set(BOX_FIELDS) | {"decision", "reason"}, row_label)
            box_id = _identifier(row["box_id"], f"{row_label}.box_id")
            if box_id not in assigned:
                raise BoxReplyError(f"{row_label} contains a box not assigned to this reviewer: {box_id}")
            if box_id in seen:
                raise BoxReplyError(f"{label} contains duplicate box_id: {box_id}")
            seen.add(box_id)
            for field in BOX_FIELDS:
                if type(row[field]) is not str or row[field] != source_boxes[box_id][field]:
                    raise BoxReplyError(f"{row_label}.{field} differs from the original snapshot")
            decision = _text(row["decision"], f"{row_label}.decision", blank=True)
            reason = _text(row["reason"], f"{row_label}.reason", blank=True)
            if decision not in _DECISIONS:
                raise BoxReplyError(f"{row_label}.decision must be blank, no_exception, exception, or needs_correction")
            if decision in {"exception", "needs_correction"} and not reason:
                raise BoxReplyError(f"{row_label}.reason is required for {decision}")
            if not decision and reason:
                raise BoxReplyError(f"{row_label} has a reason without a decision")
            answered = answered or bool(decision)
            decisions[(reviewer_id, box_id)] = row
        if seen != assigned:
            raise BoxReplyError(f"{label} must contain every assigned box exactly once; missing {len(assigned - seen)}")
        if answered and not response["submitted_by"]:
            raise BoxReplyError(f"{label} needs submitted_by and submitted_on when any decision is present")
        returned[reviewer_id] = response

    output_rows = []
    counts = {"boxes": len(source_boxes), "no_exception": 0, "exception": 0,
              "needs_correction": 0, "incomplete": 0, "required_decisions": 0,
              "answered_decisions": 0, "returned_reviewers": len(returned),
              "required_reviewers": len(reviewers)}
    for box in manifest["boxes"]:
        box_decisions = []
        pending = []
        corrections = []
        statuses = set()
        for reviewer_id, reviewer in reviewers.items():
            if box["department"] not in reviewer_departments[reviewer_id]:
                continue
            response = returned.get(reviewer_id)
            row = decisions.get((reviewer_id, box["box_id"]))
            decision = row["decision"] if row else ""
            reason = row["reason"] if row else ""
            box_decisions.append({
                "reviewer_id": reviewer_id, "reviewer_name": reviewer["reviewer_name"],
                "returned": response is not None,
                "submitted_by": response["submitted_by"] if response else "",
                "submitted_on": response["submitted_on"] if response else "",
                "decision": decision, "reason": reason,
            })
            counts["required_decisions"] += 1
            if decision:
                counts["answered_decisions"] += 1
                statuses.add(decision)
            else:
                pending.append(reviewer_id)
            if decision == "needs_correction":
                corrections.append(reviewer_id)
        status = ("exception" if "exception" in statuses else
                  "needs_correction" if corrections else
                  "incomplete" if pending else "no_exception")
        counts[status] += 1
        output_rows.append({**box, "status": status,
                            "reported_no_exception": not pending and statuses == {"no_exception"},
                            "decisions": box_decisions, "pending_reviewers": pending,
                            "correction_reviewers": corrections})
    complete = counts["answered_decisions"] == counts["required_decisions"]
    return {"schema": 1, "round_id": manifest["round_id"],
            "manifest_sha256": manifest["manifest_sha256"], "rows": output_rows,
            "counts": counts, "complete": complete,
            "ready_for_coordinator_review": complete and not any(row["correction_reviewers"] for row in output_rows)}
