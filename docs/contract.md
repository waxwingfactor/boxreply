# Supported contract

BoxReply 1.x operates on physical-box review lists, not the boxes or their contents. Its six source fields and reviewer assignments are explicitly supplied by people. It never contacts a remote service or reads the documents inside a box.

## Limits and formats

- Python 3.10+, Linux, macOS or Windows. A desktop spreadsheet editor that preserves `.xlsx` text cells is needed by reviewers. Mobile editing and other workbook formats are outside the supported scope.
- UTF-8 CSV, optional BOM, exact ordered headers from README; at most 5 MiB each. No empty input, blank rows, duplicate IDs, extra columns, surrounding whitespace or Unicode control/format characters. Fields are at most 5,000 characters.
- 10,000 boxes, 100 reviewers, 10,000 department/reviewer assignments and **50,000 total box/reviewer decisions** per round. Combinations exceeding the decision limit are rejected.
- IDs are case-sensitive. Reviewer filenames have an ordinal prefix to remain distinct on case-insensitive filesystems and avoid Windows reserved filenames.
- Returns: at most 100 workbooks, 10 MiB compressed each, 100 MiB total; each ZIP expands to at most 50 MiB, contains at most 200 unique entries, and contains no encrypted member, macro/binary content, external workbook links or formulas. Real worksheet row/cell limits are checked before spreadsheet parsing. Corrupt or unsupported files fail clearly.
- A round or packet contains at most 500 regular files and 250 MiB. Symlinks and special files within evidence are rejected. Filesystems and input data are otherwise trusted local resources. Do not process untrusted content on a machine where hostile input must be isolated at the operating-system level.

Generated workbooks use literal string cells for all source text, including strings beginning with formula characters. They use no spreadsheet formulas. The list validation is a convenience; reconciliation validates values independently. The source date stays a human proposal. A calendar-valid date does not establish legal eligibility.

## Frozen identity and decisions

The canonical schema-1 manifest binds round ID, exact box values, exact reviewer assignments and original CSV byte hashes. Each generated workbook carries the round and manifest fingerprint. Review rows may be reordered, but each assigned box must occur exactly once with unchanged source fields. Copying an old decision into a new round is unsupported; collect a new response after a source change.

Submission name/date are required when any decision is present, and must be both blank or both supplied. Date text is `YYYY-MM-DD`; a native spreadsheet date without a time is also accepted. All other review values are text. `exception` and `needs_correction` require a reason. A blank decision cannot contain a reason. Reasons and declared names follow the same length, whitespace and character limits as source text. A reviewer must submit exactly one workbook per reconciliation invocation. Duplicate files are rejected, including byte-identical copies.

The result contains every source box exactly once and every expected reviewer/box pair exactly once. `no_exception` is reported only if every required reviewer explicitly reports it. An `exception` takes display precedence, followed by `needs_correction`, an incomplete response, and `no_exception`. Pending and correction reviewer IDs remain separate, so precedence cannot hide another unresolved condition. The `complete` flag describes whether all decisions are answered; `ready_for_coordinator_review` additionally requires no correction requests. Exceptions do not make a packet incomplete: they are explicit responses for a coordinator to handle.

## Failure, evidence and trust

Malformed or conflicting inputs produce no completed output directory. A valid but unfinished round produces a progress packet and exit 3. Output directories must be new, their parents must exist, and packet output must be outside the input round. Publication uses a temporary sibling directory and an exclusive reservation file. See operations for interrupted-process recovery.

Every successful reconciliation preserves the original round and exact returned workbook bytes, computes results, and writes a coordinator workbook plus a receipt. Verification checks the complete inventory, reparses original inputs, replays decisions, and regenerates a deterministic coordinator workbook. It supports relocation and offline verification with the same BoxReply version. Schema/version mismatches fail explicitly.

The receipt is an integrity record, not a signature. An actor who can replace the complete packet can also forge a new receipt and declared identity. BoxReply does not verify the original facts, reviewer authority, legal holds, signatures, whether a proposed action is still current, or official acceptance by a records center. Keep packets and original authorization evidence within organizational access and backup controls. Sensitive metadata and reviewer explanations may be present throughout the packet; filenames are neutral but contents are not anonymized.

No generated file is a disposal instruction, certificate of destruction, vendor upload or official form. Ordinary human authorization, records-system updates and physical operations follow outside BoxReply.
