# Research and opportunity boundaries

Research date: **15 October 2026**. This is a bounded desk-research record, not a claim that BoxReply is unique or that its audience has adopted it.

## The problem selected

BoxReply serves a records officer who already has a human-selected list of physical boxes for a review round and must collect spreadsheet replies from departmental reviewers. The useful unit of work is the entire round: freeze the source, distribute reviewer workbooks, collect explicit replies, reconcile them without losing exceptions, and prepare a source-linked coordinator packet.

The hypothesis is that a small local companion can reduce the custom spreadsheet work needed for this external handoff. The sources below document the handoff and its failure modes. They do not establish demand for BoxReply, measured time savings, willingness to change workflows, or the causes of response delays.

## Primary evidence

| Source examined | Documented fact | What it does and does not support |
| --- | --- | --- |
| [Wisconsin records officer reference guide](https://doa.wi.gov/Legal/State%20of%20Wisconsin%20Records%20Management%20Reference%20Guide%20%20%20%20%20%20%20%20%20%20%20%20for%20State%20Agency%20Records%20Officers.pdf), historical guide, sample packet dated 2015, pp. 26–32 | Its sample process distributes spreadsheets to coordinators, requests box-specific exceptions and justification, requires an authorized signature and date, and then compiles the replies centrally. The sample includes records-center and agency box IDs, department, series, description, dates, retention and disposition. | Direct evidence for an external review round and the importance of stable box identifiers. It is historical; neither the guide's disputed edition metadata nor this sample establishes current Wisconsin procedures. BoxReply's schema is its own supported contract, not an official Wisconsin form. |
| [NARA AC 30.2025](https://www.archives.gov/records-mgmt/memos/ac-30-2025), 30 July 2025 | Federal Records Centers communicate eligible dispositions through individual forms, Excel for numerous transfers, or the ARCIS Customer Portal Disposition Module. For FY24 notices, NARA reports 19.85% concurrence, 6.35% declination and 73.8% nonresponse. | Recent evidence that spreadsheet notices remain part of a real workflow and response completion matters. The memo does not attribute nonresponse to consolidation errors or show that BoxReply would improve it. Native online approval already exists. |
| [University of Washington IT departmental scanning policy](https://finance.uw.edu/recmgt/sites/default/files/scanning/UW-IT%20Departmental%20Scanning%20Policy.pdf), p. 4 | Records Monitors identify candidates and compile lists for separate Destruction Approvers. The policy assigns people responsibility for identifying records subject to holds. | Supports separation between assembling a review and making a disposition decision. It is one institution's policy, not a general authorization rule. |
| [Lake County Clerk inspector-general follow-up on IT records management](https://www.lakecountyclerkfl.gov/wp-content/uploads/BCC-126_Follow_Up_Review_of_Audit_of_IT_Records_Management.pdf), p. 6, historical audit | The audit records inconsistencies among carton labels, dates and inventory spreadsheets, missing documentation and signatures, and recommends documenting justification for retention. | Evidence for concrete metadata and documentation failure modes. BoxReply checks its digital round against its source; it cannot inspect carton contents, authenticate signatures, or detect an incorrect original inventory. |

## Competition and the case against building another approval system

Feature checks used public product documentation reviewed on the research date. They were not authenticated product trials, exhaustive API audits, price comparisons, or proof that an undocumented feature is absent.

| Alternative | Capabilities verified in primary documentation | Implication for BoxReply |
| --- | --- | --- |
| [Gimmal Physical disposition decisions](https://docs.gimmal.com/gp/disposition-decisions) and [workflows](https://docs.gimmal.com/gp/workflows) | Gimmal supports batch decisions, reports and explicit sequential or parallel workflows. Its manual-options documentation describes emailed or printed reports followed by an administrator entering the returned approvals. | A strong complete records-system alternative. The documented external response handoff is the potential companion use case. BoxReply does not replace Gimmal's permissions, schedules or operational controls. |
| [RecordPoint disposal approval](https://help.recordpoint.com/hc/en-us/articles/5386119556879-Disposal-Approval-Record-Level) | A records manager assigns approvers; reviewers receive links, approve or reject assigned items, and supply comments for rejection. The records manager completes disposal afterward. | Native approval is already well supported. Use it when it fits the organization; do not introduce BoxReply merely to duplicate it. |
| [ARCIS Customer Portal Disposition Module, described by NARA](https://www.archives.gov/records-mgmt/memos/ac-30-2025) | Online disposition review and approval is an existing option for Federal Records Center customers. | Federal agencies are not automatically an underserved market. BoxReply is relevant only where the external spreadsheet review remains an actual requirement. |
| [Access Unify inventory and destruction procedure](https://unifyhelp.accesscorp.com/Content/Services%20Portal%20Help%20Topics/Inventory.htm) | The portal supports inventory reporting, destruction requests, signatures and order status. Its procedure tells users to secure internal approval before ordering destruction. | A service portal can handle execution while internal review remains a separate process. BoxReply produces neither an order nor proof of destruction. |
| [Microsoft Power Query merge](https://learn.microsoft.com/en-us/power-query/merge-queries-overview) and [append](https://learn.microsoft.com/en-us/power-query/append-queries) | Power Query joins tables using selected keys and combines tables by column names. | An experienced analyst can build reconciliation in Excel. BoxReply's proposed benefit is a maintained end-to-end contract with explicit unresolved states and evidence, not a novel join operation. |
| [OpenRefine project collaboration](https://openrefine.org/docs/manual/starting) and [exporting](https://openrefine.org/docs/manual/exporting) | OpenRefine offers local cleanup, exports and project histories. Its documented collaboration model passes project snapshots between users; a project is not simultaneously shared. | A useful open-source alternative for inspecting and cleaning input. BoxReply is narrowly about collecting separate reviewer returns against a frozen round, rather than general data cleanup. |

The checks covered three different alternatives: native records-system workflows, the spreadsheet tools already at hand, and general open-source data tools. Public web and GitHub searches also looked for records disposition, spreadsheet approval and return-consolidation projects. Search coverage was bounded; sparse search results are not evidence that no equivalent exists.

## What differentiation can honestly mean

BoxReply is justified only by the combination of an external spreadsheet handoff, multiple required reviewers, preservation of each original row and return, explicit unresolved states, and a verifiable coordinator packet. No individual component is novel. An organization with a functioning native approval workflow or a satisfactory maintained Excel process may have no reason to use it.

The supported input is an explicit human-selected CSV with `box_id`, `department`, `record_series`, `description`, `proposed_action` and `proposed_date`, plus explicit reviewer assignments. These values are carried through the round; BoxReply does not interpret a retention schedule or calculate eligibility. Reviewers receive individual XLSX workbooks and report `no_exception`, `exception` or `needs_correction`; exceptions and corrections require explanation, and submitter and date are declarations.

Every required reviewer must reply explicitly. Any exception blocks a no-exception summary for the box; a correction remains unresolved. A blank or absent reply is never consent. Malformed, foreign, changed-source and duplicate returns are rejected rather than silently merged. The coordinator receives a complete source-linked workbook, a machine-readable report and an evidence packet containing original bytes and hashes for independent verification.

These are workflow guarantees within the documented input contract. Hashes detect byte changes relative to the preserved manifest; they do not establish that a source is true, that a submitter is who they claim to be, or that the packet was signed by an authorized official. The complete packet remains a local data artifact requiring the organization's own access controls.

## Explicit exclusions

BoxReply provides no legal advice, disposition authorization, retention calculation, hold determination, identity authentication, electronic signature, delivery service, records-system update, box inspection or destruction operation. It does not certify statutory compliance or produce proof that any box was destroyed. The organization's authorized people retain those responsibilities.

## Research provenance and remaining uncertainty

Discovery and adversarial competition research were performed by separate AI agents and consolidated by the implementation lead. These were independent AI desk-research tasks, not human reviewers, customer interviews, reference customers or user acceptance studies. Sources were checked at the feature level where public documentation allowed it; no external people were contacted.

Unverified questions include how often the external handoff is mandatory today, whether intended users can install a local tool, whether their policies permit these workbooks, and whether their existing spreadsheet process is already adequate. Adoption and savings remain unmeasured. Release and installation verification must be established by the project's separate release evidence, not inferred from this research.
