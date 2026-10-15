# BoxReply

Reconcile departmental box-review spreadsheets before preparing the official disposition reply.

BoxReply is a local command-line tool for a records officer who already circulates physical-box candidate lists through spreadsheets. It freezes a candidate list, creates reviewer workbooks, reconciles explicit responses, and produces a coordinator packet with the original input evidence. Blank or missing responses never become “no exception reported.”

**Supported scope:** one frozen review round, up to 10,000 boxes, 100 named reviewers and 50,000 required box/reviewer decisions, using UTF-8 CSV inputs and BoxReply-generated `.xlsx` returns. Multiple reviewers may cover a department; any reported exception remains visible even when another reviewer reports no exception. Sorting complete rows is supported. Editing source values or deleting rows is rejected.

The organization supplies the candidate list and reviewer assignments. BoxReply does not calculate retention dates, interpret hold rules, authenticate a typed name, collect legally effective signatures, update a records system, or authorize or execute disposal. Use your existing authorization procedure after reviewing the packet.

## Install

Python 3.10 or later is required. Download the wheel from the [public release](https://github.com/waxwingfactor/boxreply/releases/latest), then install it in a virtual environment:

```sh
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install ./boxreply-1.0.0-py3-none-any.whl
boxreply --help
```

The source distribution also installs with `python -m pip install ./boxreply-1.0.0.tar.gz`. Internet access is needed for dependencies unless you have prepared a local wheelhouse; the installed application makes no network calls. See [offline installation](docs/operations.md).

## Run a round

Download the source distribution for the synthetic `examples/` files, or create CSVs using the exact contracts below.

```sh
boxreply prepare --boxes examples/boxes.csv --reviewers examples/reviewers.csv \
  --round-id demo-2026 --out demo-round
```

Send each generated file in `demo-round/reviews/` to its designated reviewer through your approved channel. In a spreadsheet editor, the reviewer fills the blue **Submitted by** and **Submitted on** cells on `Instructions`, and the **decision** and **reason** columns on `Review`. Use:

| Decision | Meaning |
| --- | --- |
| `no_exception` | This reviewer reports no exception to the proposed action. |
| `exception` | This reviewer reports a reason to prevent the proposed action. An explanation is required. |
| `needs_correction` | The source list or review needs correction. An explanation is required. |
| blank | Unanswered; it remains incomplete. |

Save as `.xlsx` and return the file. Keep original signed or authenticated approvals through your ordinary process; the workbook contains declared identity only. On the coordinator machine:

```sh
boxreply reconcile --round demo-round \
  --returns returns/alex.xlsx returns/sam.xlsx --out demo-packet
boxreply verify --packet demo-packet
```

With no returns, omit `--returns` to produce an incomplete progress packet. Every reconciliation uses a **new output directory**. A corrected return replaces the previous file in your next invocation; do not provide both versions. Duplicate submissions are rejected instead of choosing a winner.

The packet includes `coordinator.xlsx`, `results.json`, the complete original round and received return bytes under `evidence/`, and `receipt.json` with SHA-256 hashes. `verify` replays the reconciliation from the preserved evidence, compares the result and regenerated coordinator workbook, and checks all file hashes. Move the entire packet together. Hashes detect changes relative to a receipt; they are not signatures and do not establish authenticity against someone who can replace the receipt and evidence together.

## Input contracts

`boxes.csv` has exactly these columns in this order:

```csv
box_id,department,record_series,description,proposed_action,proposed_date
BX001,Finance,FIN-01,Supply invoices,destroy,2026-12-31
BX002,Planning,PLAN-07,Historic plans,transfer,2026-12-31
```

Use globally unique box IDs, not a department-local box number. IDs and the round name use 1–80 ASCII letters/digits/`_`/`.`/`-`, starting with a letter or digit. Preserve leading zeros as text. All source fields are required. Dates are `YYYY-MM-DD`; proposed actions are `destroy` or `transfer`. These values are human-supplied proposals. Include context in description and record_series; the tool does not infer or verify them.

`reviewers.csv` has exactly:

```csv
department,reviewer_id,reviewer_name
Finance,alex,Alex Reviewer
Planning,sam,Sam Reviewer
```

Repeat a department for each required reviewer. A reviewer can cover several departments; repeat the same ID and name. Every department must have a reviewer, and unused departments or duplicate assignments are errors. Reviewer names and department names are exact, case-sensitive text. Source input fields have no surrounding whitespace or control characters. Maximum field length is 5,000 characters; each input CSV is at most 5 MiB.

## Results and failures

The coordinator workbook contains a summary, every box, and every expected reviewer decision. For each box the display precedence is `exception`, `needs_correction`, `incomplete`, then `no_exception`. Pending reviewers remain separately listed even if an exception takes precedence. Status totals count each box exactly once; decision totals count all assignments.

- Exit `0`: valid preparation/verification, or reconciliation with all decisions answered and no correction request. Exceptions may still be present and require human handling.
- Exit `3`: a progress packet was written, but a decision is missing or a correction is requested.
- Exit `2`: invalid/unsupported input, changed evidence, unsafe output path or an I/O error; no completed output packet is published.

“Ready for coordinator review” describes response completeness, never permission to destroy or transfer. A proposed action may become stale after a round is frozen. If the source list or assignments change, start a new round with a new ID and recollect responses; BoxReply does not import responses into a changed list.

See [the full contract](docs/contract.md), [operations and recovery](docs/operations.md), [research and alternatives](docs/research.md), [positioning and constructed scenarios](docs/positioning.md), and [release verification](docs/release-verification.md).

## Development

```sh
python -m pip install -e '.[test]'
python -m pytest
python -m build
```

Tests cover conservative aggregation, source and round identity, malformed workbooks, duplicate and missing returns, transactional output, relocation, offline replay, and tamper detection. CI tests supported Python versions on Linux, macOS and Windows. This project was built and independently reviewed by AI agents; public review records distinguish those reviews from human approval. No customer adoption or measured savings are claimed.
