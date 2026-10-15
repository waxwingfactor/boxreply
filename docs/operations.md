# Operations and recovery

## Coordinator and reviewer workflow

Use a local working directory on a filesystem supporting ordinary atomic rename. Avoid running against live shared folders with concurrent editors. Keep the generated round unchanged; send copies of reviewer files and save returned copies separately. The ordinal filename prefix does not identify a reviewer: the workbook's frozen metadata does. Renaming a returned file is supported.

For a changed source list, create a new round ID. There is no override to reuse an old response against changed source values. To correct a returned decision, retain the previous response under your normal records policy and provide only the replacement to a new reconciliation invocation. BoxReply never silently chooses among conflicting versions. To inspect missing decisions, reconcile with the returns received so far; exit 3 indicates a usable progress packet.

Open `coordinator.xlsx` starting with Summary, then inspect Boxes and Decisions. Filter `exception`, `needs_correction` and pending reviewer fields. The Decisions sheet preserves explanations and submission declarations for every expected pair. Long text is preserved fully even if a spreadsheet's row height limits the visible preview; use its formula bar or expand the row to read it. Complete ordinary authorization, check that no new impediment exists, and prepare your official reply through the existing process. Do not submit the JSON or workbook as though it were an official destruction order.

`boxreply verify --packet PATH` checks both hashes and the meaning of the packet by replay. Preserve the complete directory; the coordinator workbook by itself cannot be independently verified. Verification needs the same BoxReply version recorded in `receipt.json`. Keep that release wheel and its dependency wheelhouse with long-lived packets if offline recovery is required.

## Offline installation

On a connected machine matching the target Python environment, download the release wheel and its dependencies:

```sh
python -m pip download --only-binary=:all: --dest wheelhouse ./boxreply-1.0.0-py3-none-any.whl
```

Copy the wheelhouse to the target machine, create a virtual environment, then:

```sh
python -m pip install --no-index --find-links wheelhouse boxreply==1.0.0
```

Once installed, all commands work without a network connection. The application contains no telemetry, service credentials or network client. Python packaging may access package indexes during installation unless `--no-index` is used.

## Interrupted output and errors

If a command fails normally, its temporary directory and reservation file are removed. A hard interruption or power failure may leave `.boxreply-*` and `NAME.boxreply-lock` siblings. Confirm no BoxReply process is writing that output, inspect and preserve anything needed, then remove only that stale reservation and temporary directory. Rerun using a new output name. A completed output directory is never overwritten. The reservation protects cooperating BoxReply processes, not hostile filesystem writers.

Exit 2 messages identify unsupported input or I/O failures. Do not bypass a failed source fingerprint check. Return to the original frozen round, request a corrected workbook, or start a new round. Report software defects with synthetic reproductions rather than confidential records metadata.

## Installation and support boundaries

The public release provides a universal Python wheel, source distribution, SHA-256 checksums, and source-revision provenance. The source distribution includes examples, tests, and documentation. CI exercises Python 3.10, 3.12 and 3.14 on Linux, macOS and Windows. The published artifacts receive separate fresh-environment installation checks; exact observed environments and results are recorded in release evidence.

The workbook interface is intended for desktop Excel or LibreOffice-compatible editing. Generated workbooks are formula-free; no recalculation engine is needed. Native editor compatibility observations are recorded honestly in release verification. There is no web application, service to deploy, account system or mobile UI.
