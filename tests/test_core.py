"""Acceptance and hostile-input checks for the frozen review-round contract."""

import copy
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from boxreply.core import (
    BOX_FIELDS, MAX_INPUT_BYTES, BoxReplyError, expected_boxes,
    prepare, reconcile, validate_manifest,
)


class RoundTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.boxes = [
            {"box_id": "B-002", "department": "Planning", "record_series": "Plans",
             "description": "Site plans, 2004–2008", "proposed_action": "transfer",
             "proposed_date": "2026-10-15"},
            {"box_id": "B-001", "department": "Finance", "record_series": "Invoices",
             "description": "Paid invoices", "proposed_action": "destroy",
             "proposed_date": "2026-10-15"},
        ]
        self.assignments = [
            {"department": "Planning", "reviewer_id": "sam", "reviewer_name": "Sam O’Neil"},
            {"department": "Finance", "reviewer_id": "alex", "reviewer_name": "Alex Chen"},
            {"department": "Finance", "reviewer_id": "sam", "reviewer_name": "Sam O’Neil"},
        ]
        self.boxes_path = self.root / "boxes.csv"
        self.reviewers_path = self.root / "reviewers.csv"
        self.write_sources()
        self.manifest = prepare(self.boxes_path, self.reviewers_path, "annual-2026")

    def write_csv(self, path, fields, rows, encoding="utf-8"):
        with path.open("w", encoding=encoding, newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def write_sources(self):
        self.write_csv(self.boxes_path, BOX_FIELDS, self.boxes)
        self.write_csv(self.reviewers_path, ("department", "reviewer_id", "reviewer_name"), self.assignments)

    def response(self, reviewer_id="sam", decision="no_exception", reason=""):
        reviewer = next(row for row in self.manifest["reviewers"] if row["reviewer_id"] == reviewer_id)
        return {
            "round_id": self.manifest["round_id"],
            "manifest_sha256": self.manifest["manifest_sha256"],
            "reviewer_id": reviewer_id, "reviewer_name": reviewer["reviewer_name"],
            "submitted_by": reviewer["reviewer_name"] if decision else "",
            "submitted_on": "2026-10-15" if decision else "",
            "rows": [{**box, "decision": decision, "reason": reason}
                     for box in expected_boxes(self.manifest, reviewer_id)],
        }

    def signed_manifest(self, manifest):
        value = copy.deepcopy(manifest)
        body = {key: val for key, val in value.items() if key != "manifest_sha256"}
        value["manifest_sha256"] = hashlib.sha256(json.dumps(
            body, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")).hexdigest()
        return value

    def test_round_trip_all_required_reviews_and_reordered_returns(self):
        sam = self.response()
        sam["rows"].reverse()
        result = reconcile(self.manifest, [sam, self.response("alex")])
        self.assertTrue(result["complete"])
        self.assertTrue(result["ready_for_coordinator_review"])
        self.assertEqual([row["box_id"] for row in result["rows"]], ["B-001", "B-002"])
        self.assertTrue(all(row["reported_no_exception"] for row in result["rows"]))
        self.assertEqual(result["counts"], {
            "boxes": 2, "no_exception": 2, "exception": 0, "needs_correction": 0,
            "incomplete": 0, "required_decisions": 3, "answered_decisions": 3,
            "returned_reviewers": 2, "required_reviewers": 2,
        })
        self.assertEqual([row["reviewer_id"] for row in result["rows"][0]["decisions"]], ["alex", "sam"])
        self.assertEqual(json.loads(json.dumps(result)), result)

    def test_exception_never_hides_pending_reviewers(self):
        result = reconcile(self.manifest, [self.response("alex", "exception", "Still needed")])
        finance, planning = result["rows"]
        self.assertEqual(finance["status"], "exception")
        self.assertFalse(finance["reported_no_exception"])
        self.assertEqual(finance["pending_reviewers"], ["sam"])
        self.assertFalse(finance["decisions"][1]["returned"])
        self.assertEqual(planning["status"], "incomplete")
        self.assertFalse(result["complete"])
        self.assertFalse(result["ready_for_coordinator_review"])

    def test_exception_over_correction_over_incomplete(self):
        sam = self.response("sam", "needs_correction", "Check box description")
        result = reconcile(self.manifest, [sam])
        self.assertEqual(result["rows"][0]["status"], "needs_correction")
        self.assertEqual(result["rows"][0]["pending_reviewers"], ["alex"])
        result = reconcile(self.manifest, [sam, self.response("alex", "exception", "Hold review")])
        self.assertEqual(result["rows"][0]["status"], "exception")
        self.assertEqual(result["rows"][0]["correction_reviewers"], ["sam"])
        self.assertTrue(result["complete"])
        self.assertFalse(result["ready_for_coordinator_review"])

    def test_complete_exception_packet_is_ready_for_coordinator_review(self):
        result = reconcile(self.manifest, [self.response("sam"), self.response("alex", "exception", "Keep")])
        self.assertTrue(result["complete"])
        self.assertTrue(result["ready_for_coordinator_review"])
        self.assertFalse(result["rows"][0]["reported_no_exception"])

    def test_missing_and_blank_returns_are_distinct_and_incomplete(self):
        result = reconcile(self.manifest, [self.response("sam", "")])
        self.assertFalse(result["complete"])
        self.assertEqual(result["counts"]["answered_decisions"], 0)
        self.assertEqual(result["rows"][0]["pending_reviewers"], ["alex", "sam"])
        self.assertFalse(result["rows"][0]["decisions"][0]["returned"])
        self.assertTrue(result["rows"][0]["decisions"][1]["returned"])
        self.assertEqual(reconcile(self.manifest, [])["counts"]["incomplete"], 2)

    def test_partial_rows_are_rejected_even_if_all_supplied_rows_answered(self):
        response = self.response()
        response["rows"].pop()
        with self.assertRaisesRegex(BoxReplyError, "every assigned box"):
            reconcile(self.manifest, [response])

    def test_foreign_box_rejected(self):
        response = self.response("alex")
        response["rows"].append({**self.boxes[0], "decision": "no_exception", "reason": ""})
        with self.assertRaisesRegex(BoxReplyError, "not assigned"):
            reconcile(self.manifest, [response])

    def test_duplicate_rows_and_duplicate_submissions_rejected(self):
        response = self.response()
        with self.assertRaisesRegex(BoxReplyError, "Duplicate submission"):
            reconcile(self.manifest, [response, copy.deepcopy(response)])
        response["rows"].append(copy.deepcopy(response["rows"][0]))
        with self.assertRaisesRegex(BoxReplyError, "duplicate box_id"):
            reconcile(self.manifest, [response])

    def test_stale_round_digest_reviewer_and_name_rejected(self):
        changes = [("round_id", "old-round"), ("manifest_sha256", "0" * 64),
                   ("reviewer_id", "unknown"), ("reviewer_name", "Other Person")]
        for key, value in changes:
            with self.subTest(key=key):
                response = self.response()
                response[key] = value
                with self.assertRaises(BoxReplyError):
                    reconcile(self.manifest, [response])

    def test_every_source_field_is_immutable(self):
        for field in BOX_FIELDS:
            with self.subTest(field=field):
                response = self.response()
                response["rows"][0][field] += "changed"
                with self.assertRaises(BoxReplyError):
                    reconcile(self.manifest, [response])

    def test_decisions_and_required_reasons(self):
        for decision, reason in [("approve", ""), ("exception", ""), ("needs_correction", ""), ("", "orphan")]:
            with self.subTest(decision=decision, reason=reason):
                response = self.response(decision=decision, reason=reason)
                with self.assertRaises(BoxReplyError):
                    reconcile(self.manifest, [response])

    def test_submission_metadata_is_required_for_any_decision(self):
        for name, value in [("submitted_by", ""), ("submitted_on", ""), ("submitted_on", "2026-02-30"),
                            ("submitted_on", "2026-1-5"), ("submitted_on", "20261015")]:
            with self.subTest(name=name, value=value):
                response = self.response()
                response[name] = value
                with self.assertRaises(BoxReplyError):
                    reconcile(self.manifest, [response])
        response = self.response()
        response["submitted_by"] = response["submitted_on"] = ""
        with self.assertRaisesRegex(BoxReplyError, "when any decision"):
            reconcile(self.manifest, [response])

    def test_typed_submitter_is_a_declaration_not_forced_identity(self):
        response = self.response()
        response["submitted_by"] = "Acting departmental coordinator"
        result = reconcile(self.manifest, [response, self.response("alex")])
        self.assertEqual(result["rows"][0]["decisions"][1]["submitted_by"], response["submitted_by"])

    def test_manifest_integrity_and_strict_semantics_even_with_rehashed_data(self):
        changed = copy.deepcopy(self.manifest)
        changed["boxes"][0]["description"] = "Altered"
        with self.assertRaisesRegex(BoxReplyError, "digest mismatch"):
            validate_manifest(changed)
        bad_values = [
            ("schema", True), ("schema", 1.0), ("schema", "1"), ("boxes", {}),
            ("reviewers", None), ("round_id", "../unsafe"),
            ("sources", {"boxes_sha256": "0" * 64, "reviewers_sha256": "BAD"}),
        ]
        for key, value in bad_values:
            with self.subTest(key=key, value=value):
                manifest = copy.deepcopy(self.manifest)
                manifest[key] = value
                with self.assertRaises(BoxReplyError):
                    validate_manifest(self.signed_manifest(manifest))
        for change in [
            lambda m: m["boxes"].reverse(),
            lambda m: m["boxes"].append(copy.deepcopy(m["boxes"][0])),
            lambda m: m["reviewers"].reverse(),
            lambda m: m["reviewers"][0]["departments"].append("Other"),
            lambda m: m["reviewers"][1]["departments"].append("Finance"),
        ]:
            manifest = copy.deepcopy(self.manifest)
            change(manifest)
            with self.assertRaises(BoxReplyError):
                validate_manifest(self.signed_manifest(manifest))

    def test_manifest_response_and_row_keys_are_exact(self):
        for extra in [True, False]:
            manifest = copy.deepcopy(self.manifest)
            if extra:
                manifest["unknown"] = "x"
            else:
                del manifest["sources"]
            with self.assertRaises(BoxReplyError):
                validate_manifest(manifest)
            for level in ["response", "row"]:
                response = self.response()
                value = response if level == "response" else response["rows"][0]
                if extra:
                    value["unknown"] = "x"
                else:
                    del value["round_id" if level == "response" else "reason"]
                with self.assertRaises(BoxReplyError):
                    reconcile(self.manifest, [response])

    def test_malformed_primitive_types_raise_domain_error(self):
        for value in [None, True, 3, "text", [], {"schema": 1}]:
            with self.subTest(value=value):
                with self.assertRaises(BoxReplyError):
                    validate_manifest(value)
        for key, value in [("reviewer_id", []), ("reviewer_name", {}), ("submitted_by", []),
                           ("submitted_on", None), ("rows", {}), ("round_id", True),
                           ("manifest_sha256", [])]:
            response = self.response()
            response[key] = value
            with self.subTest(key=key):
                with self.assertRaises(BoxReplyError):
                    reconcile(self.manifest, [response])
        for key, value in [("box_id", []), ("department", {}), ("reason", []), ("decision", True)]:
            response = self.response()
            response["rows"][0][key] = value
            with self.subTest(key=key):
                with self.assertRaises(BoxReplyError):
                    reconcile(self.manifest, [response])
        for responses in [None, {}, "responses", [None]]:
            with self.assertRaises(BoxReplyError):
                reconcile(self.manifest, responses)

    def test_expected_boxes_returns_copies_and_rejects_unknown_reviewers(self):
        boxes = expected_boxes(self.manifest, "alex")
        self.assertEqual([box["box_id"] for box in boxes], ["B-001"])
        boxes[0]["description"] = "changed copy"
        validate_manifest(self.manifest)
        with self.assertRaises(BoxReplyError):
            expected_boxes(self.manifest, "other")

    def test_bom_supported_and_raw_source_hashes_bind_bytes(self):
        self.write_csv(self.boxes_path, BOX_FIELDS, self.boxes, "utf-8-sig")
        manifest = prepare(self.boxes_path, self.reviewers_path, "bom-round")
        self.assertEqual(manifest["sources"]["boxes_sha256"], hashlib.sha256(self.boxes_path.read_bytes()).hexdigest())
        self.assertEqual(manifest["boxes"], self.manifest["boxes"])

    def test_csv_formula_like_values_remain_literal_text(self):
        self.boxes[0]["description"] = '=HYPERLINK("https://invalid.example","literal")'
        self.boxes[1]["record_series"] = "+SUM(1,2)"
        self.assignments[0]["reviewer_name"] = "@literal name"
        self.assignments[2]["reviewer_name"] = "@literal name"
        self.write_sources()
        manifest = prepare(self.boxes_path, self.reviewers_path, "literal-round")
        self.assertEqual(manifest["boxes"][1]["description"], self.boxes[0]["description"])
        self.assertEqual(manifest["boxes"][0]["record_series"], "+SUM(1,2)")

    def test_csv_invalid_encoding_headers_width_quotes_and_empty_inputs(self):
        malformed = [b"\xff", b"box_id,department\nB1,Finance\n", b"",
                     (",".join(BOX_FIELDS) + "\n").encode(),
                     (",".join(BOX_FIELDS) + '\n"unclosed').encode(),
                     (",".join(BOX_FIELDS) + "\nB1,Finance,x,x,destroy,2026-10-15,extra\n").encode(),
                     (",".join(BOX_FIELDS) + "\n\n").encode()]
        for raw in malformed:
            with self.subTest(raw=raw[:100]):
                self.boxes_path.write_bytes(raw)
                with self.assertRaises(BoxReplyError):
                    prepare(self.boxes_path, self.reviewers_path, "round")

    def test_bad_source_values_are_rejected(self):
        bad = [("box_id", "../path"), ("box_id", "é"), ("description", " leading"),
               ("description", "trailing "), ("description", "line\nbreak"),
               ("description", "tab\tvalue"), ("description", "bidi\u202evalue"),
               ("description", ""), ("description", "x" * 5001),
               ("proposed_date", "2026-02-29"), ("proposed_date", "2026-1-01"),
               ("proposed_action", "delete")]
        for field, value in bad:
            with self.subTest(field=field, value=value[:50]):
                rows = copy.deepcopy(self.boxes)
                rows[0][field] = value
                self.write_csv(self.boxes_path, BOX_FIELDS, rows)
                with self.assertRaises(BoxReplyError):
                    prepare(self.boxes_path, self.reviewers_path, "round")

    def test_duplicate_sources_and_assignment_coverage_rejected(self):
        self.boxes.append(copy.deepcopy(self.boxes[0]))
        self.write_sources()
        with self.assertRaisesRegex(BoxReplyError, "duplicate box IDs"):
            prepare(self.boxes_path, self.reviewers_path, "round")
        self.boxes.pop()
        variants = [self.assignments + [copy.deepcopy(self.assignments[0])],
                    self.assignments[:1],
                    self.assignments + [{"department": "Other", "reviewer_id": "x", "reviewer_name": "X"}],
                    self.assignments + [{"department": "Planning", "reviewer_id": "alex", "reviewer_name": "Other Alex"}]]
        for assignments in variants:
            self.write_csv(self.boxes_path, BOX_FIELDS, self.boxes)
            self.write_csv(self.reviewers_path, ("department", "reviewer_id", "reviewer_name"), assignments)
            with self.assertRaises(BoxReplyError):
                prepare(self.boxes_path, self.reviewers_path, "round")

    def test_file_byte_limit_and_missing_file(self):
        self.boxes_path.write_bytes(b"x" * (MAX_INPUT_BYTES + 1))
        with self.assertRaisesRegex(BoxReplyError, "exceeds"):
            prepare(self.boxes_path, self.reviewers_path, "round")
        with self.assertRaises(BoxReplyError):
            prepare(self.root / "missing.csv", self.reviewers_path, "round")

    def test_box_limit(self):
        boxes = [{**self.boxes[0], "box_id": f"B{number:05d}"} for number in range(10001)]
        self.write_csv(self.boxes_path, BOX_FIELDS, boxes)
        with self.assertRaisesRegex(BoxReplyError, "10000"):
            prepare(self.boxes_path, self.reviewers_path, "round")

    def test_reviewer_limit(self):
        assignments = [{"department": "Planning", "reviewer_id": f"r{number:03d}", "reviewer_name": f"Reviewer {number}"}
                       for number in range(101)]
        assignments.append({"department": "Finance", "reviewer_id": "r000", "reviewer_name": "Reviewer 0"})
        self.write_csv(self.reviewers_path, ("department", "reviewer_id", "reviewer_name"), assignments)
        with self.assertRaisesRegex(BoxReplyError, "100 reviewers"):
            prepare(self.boxes_path, self.reviewers_path, "round")

    def test_required_decision_limit_is_enforced(self):
        boxes = [{**self.boxes[0], "box_id": f"B{number:05d}"} for number in range(1000)]
        assignments = [{"department": "Planning", "reviewer_id": f"r{number:03d}", "reviewer_name": f"Reviewer {number}"}
                       for number in range(51)]
        self.write_csv(self.boxes_path, BOX_FIELDS, boxes)
        self.write_csv(self.reviewers_path, ("department", "reviewer_id", "reviewer_name"), assignments)
        with self.assertRaisesRegex(BoxReplyError, "50000 required"):
            prepare(self.boxes_path, self.reviewers_path, "round")

    def test_exact_required_decision_limit_can_be_reconciled(self):
        boxes = [{**self.boxes[0], "box_id": f"B{number:05d}"} for number in range(1000)]
        assignments = [{"department": "Planning", "reviewer_id": f"r{number:03d}", "reviewer_name": f"Reviewer {number}"}
                       for number in range(50)]
        self.write_csv(self.boxes_path, BOX_FIELDS, boxes)
        self.write_csv(self.reviewers_path, ("department", "reviewer_id", "reviewer_name"), assignments)
        manifest = prepare(self.boxes_path, self.reviewers_path, "round")
        result = reconcile(manifest, [])
        self.assertEqual(result["counts"]["required_decisions"], 50000)
        self.assertEqual(result["counts"]["incomplete"], 1000)
        self.assertFalse(result["complete"])

    def test_leap_date_and_maximum_identifier_length(self):
        self.boxes[0]["proposed_date"] = "2024-02-29"
        self.boxes[0]["box_id"] = "B" * 80
        self.write_sources()
        manifest = prepare(self.boxes_path, self.reviewers_path, "R" * 80)
        validate_manifest(manifest)
        with self.assertRaises(BoxReplyError):
            prepare(self.boxes_path, self.reviewers_path, "R" * 81)


if __name__ == "__main__":
    unittest.main()
