# Public release verification

**BoxReply 1.0.0 was publicly released and independently verified on 15 October 2026.** The [release](https://github.com/waxwingfactor/boxreply/releases/tag/v1.0.0) contains the installable wheel, source distribution, SHA-256 checksums, build provenance and the three public-verification reports. The initial four release assets were preserved unchanged after verification.

The immutable release tag resolves to source commit `7d470cdb70273ab60436ac0212ba93c68fef8cb8`, tree `0e29a135898bbeb216ea031ec984b02bd5ae47f3`. The reviewed PR head has the identical tree. [PR #3](https://github.com/waxwingfactor/boxreply/pull/3) records independent AI-agent reviews and their fixes; it was merged through protected main after required CI passed, without bypassing the gate.

## Actual public artifacts

A separate AI QA agent anonymously downloaded the actual published wheel, source archive, checksums and provenance. Each download returned HTTP 200. GitHub asset digests, published SHA-256 checksums and installed artifact origins matched. An anonymously downloaded exact-commit source archive and recursive Git tree matched all 23 tracked source-file hashes and Git blob IDs; 21 packaged tracked source files and all five wheel Python modules matched the public source. The verifier was extracted from the downloaded source archive and hash-checked, rather than taken from the development checkout.

Each downloaded artifact was installed in its own fresh environment outside the checkout on **macOS arm64 / CPython 3.12.14**. Dependencies were acquired first; installation then used a local wheelhouse with `--no-index`, `--find-links` and `--no-cache-dir`. Isolated interpreter probes verified the non-editable module origin inside the fresh environment and the original artifact SHA-256 in installation metadata.

**Wheel: 34/34 acceptance checks passed. Source distribution: 34/34 passed.** Checks exercised complete and partial review rounds, exception precedence with pending reviewers, correction blocking, changed-source and duplicate-return rejection, deterministic delayed replay, source removal and packet relocation, and both ordinary hash tampering and rewritten-receipt result tampering. Python socket connections and DNS resolution were disabled in every application subprocess; this was not an operating-system network namespace.

| Public artifact | SHA-256 |
| --- | --- |
| `boxreply-1.0.0-py3-none-any.whl` | `4cc7e3d1bf538e10e29c7400863909b6a8c95dddfa5ad68829c6f69ec811b1e0` |
| `boxreply-1.0.0.tar.gz` | `fb73df8f214640345e87b751ae617b8b74891b7ef8d8a7203f9f900ddc1a050b` |

Machine-readable records: [aggregate](verification/public-verification.json), [wheel](verification/public-wheel-verification.json), [source](verification/public-sdist-verification.json). Identical copies and `PUBLIC-VERIFICATION-SHA256SUMS` are attached to the release. The build-time source archive necessarily predates these post-publication records; it points to the release evidence rather than claiming a future check had already happened.

## CI, independent review and upper-bound check

[Merged-source CI](https://github.com/waxwingfactor/boxreply/actions/runs/38803152606) passed on Python 3.10, 3.12 and 3.14 across Linux, macOS and Windows: each of nine environments reported **123 passed, one optional native-editor check skipped**. A separate package job passed 34 fresh wheel checks and 34 fresh source-distribution checks on Linux. These source/CI runs are distinct from the actual public-artifact installation runs above. The local full suite passed all **124 tests**, including optional native LibreOffice resave and XML-backend equivalence.

Independent AI quality review found and the lead corrected save-time timestamps that broke delayed replay, worksheet limits tied to conventional part names, formula-like metadata text, serializer-dependent output, renamed external-workbook links and repeated worksheet scans. Regression cases cover the fixes. A separate agent that authored none of the implementation reviewed core/CLI/contracts/packaging and exhaustively checked 125 three-reviewer state combinations. These records are AI reviews, not human approval or an independent organization's certification.

A final synthetic short-field boundary run used **10,000 boxes, five reviewers and 50,000 required decisions** on macOS arm64 / Python 3.12.14. Preparation succeeded in 26.896 seconds; no-return reconciliation produced the expected incomplete packet with exit 3 in 62.275 seconds; standalone verification passed in 28.122 seconds. Every box and expected reviewer pair survived; completion and readiness remained false. The packet was 21,834,183 bytes and observed peak child RSS was 449.5 MiB. These are one environment's measurements, not general performance guarantees or a test of every combination of maximum field/file sizes.

## Workbook observations and limits

A synthetic reviewer workbook was opened in Microsoft Excel for macOS, edited through keyboard navigation with declared name/date and two explicit decisions, saved as XLSX, and accepted by BoxReply. Missing reviewers remained pending. Instructions and Review were inspected at desktop size; Excel exposed worksheet labels, Go To navigation, formula-bar values and an “Accessibility: Good to go” status. That status is an editor observation, not a complete assistive-technology audit. A real LibreOfficeDev 26.8.0.0.alpha0 resave preserved the review contract; reviewer and coordinator PDF renderings were visually inspected, and print layout defects were corrected. Mobile editing is unsupported.

Public-artifact acceptance used synthetic data and programmatic workbook edits; it did not repeat a native office-application visual inspection. It established behavior on the stated local host only. Hashes establish consistency with the observed GitHub release and source, not publisher authentication against account compromise or wholesale packet replacement. No customer adoption, production deployment, measured time savings or legally effective authorization is claimed. Eligibility, actual signatures and disposition actions remain the organization's responsibility.
