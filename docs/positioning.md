# Positioning and supported whole product

Prepared **15 October 2026**. The target segment and usage scenarios below are constructed product decisions informed by desk research; they are not evidence of customer adoption.

## Original two-sentence positioning statement

For records officers coordinating physical-box review rounds through emailed spreadsheets and dissatisfied with manual Excel consolidation, BoxReply is an offline review reconciliation companion that turns explicit per-reviewer XLSX replies into a complete, source-linked coordinator packet while keeping unanswered and inconsistent items unresolved. Compared with adopting or extending native disposition workflows in Gimmal Physical or RecordPoint, BoxReply supplies frozen source rows, explicit reviewer assignments, exception-aware reconciliation, preserved original evidence and an independently verifiable hashed packet alongside the organization's existing export process.

## Narrow beachhead

The intended first user is a public-sector records officer responsible for a periodic physical-box review who already receives or prepares a candidate list, must circulate it to departmental coordinators outside a shared approval system, and must consolidate every required response before seeking the organization's separate authorization. The relevant constraint is the external spreadsheet round, not a particular jurisdiction, file extension or retention law.

This is an intended segment, not a claim of a proven market. Where all reviewers can use a suitable native approval system, that system is usually the appropriate alternative. BoxReply requires a coordinator able to run the installed local tool and reviewers able to edit its supported XLSX workbooks.

## Compelling reason to use it

A coordinator needs an answer to a concrete operational question: **Did every assigned reviewer explicitly respond to every assigned box, and can I account for every exception and correction against the same source list?** BoxReply addresses that question before a human authorization step. It does not answer whether a box may legally be disposed of.

The market alternative is manual Excel consolidation: distribute copies, track outstanding returns, compare rows, inspect exceptions and prepare a coordinator workbook. That can be entirely adequate. The product alternative is a native Gimmal Physical or RecordPoint disposition workflow with assigned approvers and system permissions; both offer substantial capabilities documented in the [research record](research.md). BoxReply is useful where the offline handoff remains a real constraint and the maintained packet workflow is preferable to custom spreadsheet logic.

## Constructed usage scenarios

These examples are invented to explain scope. They are not customer stories or measured outcomes.

1. **Two reviewers for one department.** A records officer assigns both a departmental coordinator and another designated reviewer to the same boxes. One reports `no_exception`; the other reports `exception` with an explanation. The coordinator packet preserves both replies and flags the box as having an exception. It does not average the responses or treat the first return as decisive.
2. **A date needs correction.** A reviewer sees that the source list's proposed date appears wrong and submits `needs_correction` with an explanation. The source value remains unchanged in the packet and the item remains unresolved. The records officer investigates through the organization's existing process; a substantive source change requires a new review round.
3. **An incomplete return.** A reviewer leaves one decision blank or never returns a workbook. The final report identifies the unanswered assignment. Neither a completed neighboring row nor the passage of a deadline supplies consent.
4. **A changed or duplicate workbook.** A workbook contains changed source metadata, belongs to another round, or repeats a reviewer return. BoxReply rejects it with an actionable error. The coordinator obtains a correct return rather than relying on an optimistic partial merge.

## The complete supported workflow

| Step | What the product supplies | What people must supply |
| --- | --- | --- |
| Prepare | A defined CSV contract and explicit assignment model | The selected candidate boxes, accurate source metadata and the required reviewers |
| Distribute | Frozen source rows and individual XLSX review workbooks | Approved distribution and storage channels |
| Review | Supported explicit decisions and explanation fields | Each reviewer's judgment, declared submitter and date; external authorization evidence where required |
| Reconcile | Coverage checks, rejected malformed returns, preserved exceptions and unresolved corrections | Correct returns and investigation of unresolved items |
| Hand off | A complete coordinator workbook, machine-readable report and original-byte evidence packet | Independent organizational approval and any subsequent system or physical action |
| Verify | A way to check preserved files against packet hashes independently | A trusted copy of the expected packet and the organization's own custody controls |

The source CSV fields are `box_id`, `department`, `record_series`, `description`, `proposed_action` and `proposed_date`. BoxReply carries the selected proposal through the review; it does not select candidates, interpret retention periods or alter source content. Multiple reviewers may be required for a department. Missing decisions block completion, and any exception prevents a no-exception summary for that box.

The supported whole product includes installation instructions, input contracts, synthetic examples, reviewer instructions, meaningful acceptance tests, clear failures, evidence verification and a release that can be installed independently of the development checkout. Its small scope is one local export-and-return workflow. It includes no server, notification delivery, access-management system, legal decision engine or disposal integration.

## Applying Crossing the Chasm selectively

[Geoffrey Moore's account](https://geoffreyamoore.com/book/crossing-the-chasm/) emphasizes a specific segment and use case, a compelling reason to act, and a complete solution. For BoxReply, that means finishing this constrained review round, including reviewer files, incomplete-return handling and a usable evidence packet, rather than expanding into general records management.

The [book's primary-site summary](https://crossingthechasmbymoore.com/book/) also emphasizes that pragmatic users seek evidence and a whole product. Here, constructed scenarios make the workflow inspectable; installation and acceptance evidence can establish software behavior. Neither substitutes for customer references. No reference customers, financial strategy, distribution partnership, adoption curve or claim that BoxReply has crossed a market chasm is asserted.

## Boundaries that belong in every explanation

`no_exception` means that a declared reviewer reported no exception in this round. It is not a legal authorization, authenticated signature, proof of identity, statement that all holds were found, or evidence of destruction. All legal determinations, actual approvals, records-system changes and physical handling remain with the organization's authorized people.
