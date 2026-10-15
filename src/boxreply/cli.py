"""Transactional local commands and portable, independently replayable evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

from . import __version__
from .core import BoxReplyError, prepare, reconcile, validate_manifest
from .xlsx import coordinator_bytes, read_response, review_bytes

MAX_JSON = 20 * 1024 * 1024
MAX_PACKET = 250 * 1024 * 1024


def _json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _load(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_JSON:
        raise BoxReplyError(f"Expected a regular JSON file of at most 20 MiB: {path.name}")
    try:
        def unique(pairs):
            obj = {}
            for k, v in pairs:
                if k in obj:
                    raise BoxReplyError("Duplicate JSON object key")
                obj[k] = v
            return obj
        return json.loads(path.read_bytes(), object_pairs_hook=unique)
    except (ValueError, UnicodeError, RecursionError) as e:
        raise BoxReplyError(f"Invalid JSON: {path.name}") from e


def _hash(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def _inventory(root):
    if root.is_symlink() or not root.is_dir():
        raise BoxReplyError("Evidence must be a regular local directory")
    found = {}
    size = 0
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise BoxReplyError("Symlinks are unsupported in evidence directories")
        if path.is_file():
            size += path.stat().st_size
            if size > MAX_PACKET or len(found) >= 500:
                raise BoxReplyError("Evidence exceeds 250 MiB or 500 files")
            found[path.relative_to(root).as_posix()] = _hash(path)
        elif not path.is_dir():
            raise BoxReplyError("Special files are unsupported in evidence")
    return found


@contextmanager
def _new_directory(destination):
    # An exclusive reservation avoids clobbering another process's output.
    destination = destination.absolute()
    if destination.exists() or destination.is_symlink():
        raise BoxReplyError("Output already exists; choose a new output directory")
    if not destination.parent.is_dir():
        raise BoxReplyError("Output parent directory must already exist")
    lock = destination.with_name(destination.name + ".boxreply-lock")
    try:
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as e:
        raise BoxReplyError("Output is reserved by another run; see operations recovery") from e
    os.close(fd)
    temporary = None
    try:
        temporary = Path(tempfile.mkdtemp(prefix=".boxreply-", dir=destination.parent))
        yield temporary
        if destination.exists() or destination.is_symlink():
            raise BoxReplyError("Output appeared during processing; refusing to replace it")
        temporary.rename(destination)
        temporary = None
    finally:
        if temporary is not None:
            shutil.rmtree(temporary)
        lock.unlink(missing_ok=True)


def _validate_round(root):
    files = _inventory(root)
    manifest = _load(root / "manifest.json")
    validate_manifest(manifest)
    expected = {"manifest.json", "boxes.csv", "reviewers.csv"} | {
        f"reviews/{i:03d}-{r['reviewer_id']}.xlsx" for i, r in enumerate(manifest["reviewers"], 1)
    }
    if set(files) != expected:
        raise BoxReplyError("Round contains missing or unexpected files")
    regenerated = prepare(root / "boxes.csv", root / "reviewers.csv", manifest["round_id"])
    if regenerated != manifest:
        raise BoxReplyError("Round source CSVs do not match the frozen manifest")
    # Validate original templates as blank responses, including immutable rows.
    responses = [read_response(root / "reviews" / f"{i:03d}-{r['reviewer_id']}.xlsx") for i, r in enumerate(manifest["reviewers"], 1)]
    if any(d["decision"] or d["reason"] for r in responses for d in r["rows"]):
        raise BoxReplyError("Original round templates contain decisions; use separate returned copies")
    if any(r["submitted_by"] or r["submitted_on"] for r in responses):
        raise BoxReplyError("Original round templates contain submission data")
    reconcile(manifest, responses)
    return manifest


def prepare_command(args):
    with _new_directory(args.out) as out:
        # Freeze bytes before parsing, avoiding source mutation during preparation.
        for source, name in [(args.boxes, "boxes.csv"), (args.reviewers, "reviewers.csv")]:
            if source.is_symlink() or not source.is_file() or source.stat().st_size > 5 * 1024 * 1024:
                raise BoxReplyError("CSV input must be a regular file of at most 5 MiB")
            (out / name).write_bytes(source.read_bytes())
        manifest = prepare(out / "boxes.csv", out / "reviewers.csv", args.round_id)
        (out / "manifest.json").write_bytes(_json_bytes(manifest))
        (out / "reviews").mkdir()
        for i, reviewer in enumerate(manifest["reviewers"], 1):
            (out / "reviews" / f"{i:03d}-{reviewer['reviewer_id']}.xlsx").write_bytes(review_bytes(manifest, reviewer))
        _validate_round(out)
    print(f"Prepared {len(manifest['boxes'])} boxes for {len(manifest['reviewers'])} reviewers: {args.out}")
    return 0


def reconcile_command(args):
    if args.out.resolve().is_relative_to(args.round.resolve()):
        raise BoxReplyError("Output must be outside the source round directory")
    _validate_round(args.round)
    if len(args.returns) > 100:
        raise BoxReplyError("At most 100 return workbooks are supported")
    if sum(p.stat().st_size for p in args.returns) > 100 * 1024 * 1024:
        raise BoxReplyError("Return workbooks exceed 100 MiB total")
    with _new_directory(args.out) as out:
        evidence = out / "evidence"
        evidence.mkdir()
        shutil.copytree(args.round, evidence / "round", symlinks=True)
        manifest = _validate_round(evidence / "round")
        returns = evidence / "returns"
        returns.mkdir()
        paths = []
        for i, path in enumerate(args.returns):
            if path.is_symlink() or not path.is_file() or path.stat().st_size > 10 * 1024 * 1024:
                raise BoxReplyError("Return must be a regular .xlsx file of at most 10 MiB")
            dest = returns / f"{i + 1:03d}.xlsx"
            dest.write_bytes(path.read_bytes())
            paths.append(dest)
        result = reconcile(manifest, [read_response(p) for p in paths])
        (out / "results.json").write_bytes(_json_bytes(result))
        (out / "coordinator.xlsx").write_bytes(coordinator_bytes(result))
        receipt = {"schema": 1, "product": "boxreply", "version": __version__,
                   "round_id": manifest["round_id"], "files": _inventory(out)}
        (out / "receipt.json").write_bytes(_json_bytes(receipt))
        verify_packet(out)
    print(f"Packet written: {args.out}; counts: {json.dumps(result['counts'], sort_keys=True)}")
    return 0 if result["ready_for_coordinator_review"] else 3


def verify_packet(root):
    actual = _inventory(root)
    receipt = _load(root / "receipt.json")
    if not isinstance(receipt, dict) or set(receipt) != {"schema","product","version","round_id","files"}:
        raise BoxReplyError("Invalid packet receipt")
    if type(receipt["schema"]) is not int or receipt["schema"] != 1 or receipt["product"] != "boxreply" or receipt["version"] != __version__:
        raise BoxReplyError("Unsupported packet product, schema or version")
    actual.pop("receipt.json", None)
    if receipt["files"] != actual:
        raise BoxReplyError("Packet files do not match the receipt hashes")
    manifest = _validate_round(root / "evidence" / "round")
    returns_dir = root / "evidence" / "returns"
    if not returns_dir.is_dir() or returns_dir.is_symlink():
        raise BoxReplyError("Missing packet return directory")
    paths = sorted(returns_dir.iterdir())
    if len(paths) > 100 or any(p.name != f"{i+1:03d}.xlsx" for i,p in enumerate(paths)):
        raise BoxReplyError("Invalid packet return inventory")
    result = reconcile(manifest, [read_response(p) for p in paths])
    expected = {"results.json", "coordinator.xlsx"} | {
        "evidence/round/" + name for name in _inventory(root / "evidence" / "round")
    } | {"evidence/returns/" + p.name for p in paths}
    if set(actual) != expected or receipt["round_id"] != result["round_id"]:
        raise BoxReplyError("Packet contains unexpected files or a different round")
    if (root / "results.json").read_bytes() != _json_bytes(result):
        raise BoxReplyError("Results do not match replayed evidence")
    if (root / "coordinator.xlsx").read_bytes() != coordinator_bytes(result):
        raise BoxReplyError("Coordinator workbook does not match replayed evidence")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="Reconcile offline physical-box review returns. No disposition is authorized or executed.")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("prepare", help="Freeze a round and create reviewer workbooks")
    p.add_argument("--boxes", type=Path, required=True)
    p.add_argument("--reviewers", type=Path, required=True)
    p.add_argument("--round-id", required=True)
    p.add_argument("--out", type=Path, required=True)
    p.set_defaults(run=prepare_command)
    p = commands.add_parser("reconcile", help="Produce a coordinator packet from separate returned copies")
    p.add_argument("--round", type=Path, required=True)
    p.add_argument("--returns", type=Path, nargs="*", default=[])
    p.add_argument("--out", type=Path, required=True)
    p.set_defaults(run=reconcile_command)
    p = commands.add_parser("verify", help="Check hashes and replay a portable evidence packet")
    p.add_argument("--packet", type=Path, required=True)
    p.set_defaults(run=lambda a: (verify_packet(a.packet), print("Verified packet hashes and independent replay"), 0)[-1])
    args = parser.parse_args(argv)
    try:
        return args.run(args)
    except (BoxReplyError, OSError, UnicodeError, RecursionError) as e:
        print(f"boxreply: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
