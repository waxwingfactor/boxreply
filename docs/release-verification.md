# Release verification

The implementation PR and public release assets are the authoritative records of checks for each exact revision. Public-artifact verification is a separate gate after publication; local tests alone do not establish it.

## Before the first release

On 15 October 2026, local development testing passed 103 acceptance and adversarial cases on macOS arm64 / Python 3.12.14. Subsequent review fixes are rechecked by CI before release.

Independent AI quality review found and the lead corrected:

- The spreadsheet library rewrote its modified timestamp during save. A delayed replay test now checks verification across a wall-clock second boundary.
- Worksheet limits originally depended on a conventional ZIP part path. All XML parts are now inspected regardless of relationship target names, before spreadsheet parsing.
- Formula-like reviewer names were not serialized literally in hidden metadata. All metadata source values are now literal strings.
- Optional XML backends generated different bytes for the same report. Canonical XML and fixed ZIP timestamps normalize those differences; runtime spreadsheet dependencies are pinned.

These are separate AI-agent reviews and tests, not human approval or an independent organization's certification. Review comments and exact checked commits are recorded in the implementation pull request.

## Native workbook observations

A synthetic reviewer workbook was opened in Microsoft Excel for macOS, edited through the keyboard with a declared name/date and two explicit decisions, saved as XLSX, and accepted by BoxReply. The resulting progress packet retained missing reviewers. Instructions and Review were inspected at desktop size; Excel exposed worksheet labels, Go To navigation, formula-bar values and an “Accessibility: Good to go” status. That status is an editor observation, not a full assistive-technology audit. A LibreOffice PDF rendering was also inspected; print setup was adjusted after an extra blank page was found. Mobile editing is unsupported.

## Required public-artifact check

For a release, download its actual public wheel and sdist into fresh directories outside the checkout, compare the published hashes and source revision, install each in a fresh virtual environment, check imported code comes from that environment, and exercise the workflow and failure cases. Source removal, packet relocation, offline replay and changed-evidence rejection are part of that check. The source distribution must include tests, examples, documentation and the verification harness.

At the time this document was first committed, public-artifact verification was pending. The release's `public-verification.json` and follow-up documentation record the observed result once completed; a prepared harness alone is not a passed check.
