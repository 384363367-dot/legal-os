---
name: legal-os-unified-intake
description: Source-locked intake and task routing for ambiguous or cross-domain Chinese legal work. Use only when the request could reasonably belong to more than one primary LegalOS workflow, spans multiple legal workstreams without a clear lead, or asks for routing itself. Do not use when the user has clearly requested a contract, litigation, correspondence, research, data, file-delivery, reporting, communication, or memory task; invoke that primary skill directly.
---

# Legal OS Unified Intake

## Purpose

Resolve only genuinely ambiguous or cross-domain requests to one primary workflow. A clearly named contract, litigation, correspondence, research, data, file-delivery, reporting, communication, or memory task bypasses this router and invokes its primary skill directly. This router does not prove that a downstream capability is implemented or validated.

## Invocation boundary

- Use this router when the primary workstream is genuinely unclear, multiple workstreams compete for ownership, or the user asks for classification.
- Do not invoke it merely because a legal task has attached files, professional risk, missing facts, or auxiliary checks.
- Do not emit a routing header for a task that bypasses this router.

## Office source-file acceptance

Read [office-source-policy.md](references/office-source-policy.md) before loading any document or spreadsheet helper. For LegalOS legal Word/DOCX and ordinary editable Excel deliverables, inspect the editable source artifact itself. For DOCX, check OOXML, text, tables, tracked changes, comments, styles and font inheritance. For Excel, check workbook structure, formulas, values and errors. Preserve the supplied source format and do not rebuild a structurally valid artifact without a task-specific reason. Determine the internal `visual_check_mode` from the shared policy before loading helpers. Editable-source QA is always primary. Ordinary and formal DOCX both default to conditional visual QA: no visual check is run unless the user explicitly requests it, the deliverable is inherently visual, or source inspection identifies a concrete layout risk.

## Intake sequence

1. Read the user request and every attached file that is in scope. Do not ask the user to repeat information already present in the files.
2. Record the minimum intake: matter name/identifier, roles, objective, files/versions/attachments, key dates, expected output, audience, internal/external boundary, and known conflicts or gaps.
3. Classify risk: R0 ordinary, R1 professional, R2 formal legal, R3 major/high-impact. An internal preliminary scan that will not create an adoptable or external version is normally R1; an adoptable formal output is normally R2. Raise the level when the output may affect payment, liability, admission, waiver, settlement, termination, filing, qualification, or external rights.
4. Apply the risk-calibrated decision-question ladder in [references/risk-question-ladder.md](references/risk-question-ladder.md). Count only unresolved choices that require the user to decide: R0 normally 0, R1 0–1, R2 normally 1–2, and R3 typically 3–8 in stages. Questions about missing facts/materials and authority verification do not consume this budget. If two R2 decision questions leave a material branch unresolved, reclassify as R3. Use `grill-me` when available; otherwise apply the ladder directly.
5. Select exactly one primary route. Load only the necessary auxiliary routes and workflow quality gate.
6. If the expected output is a templated formal file, identify the exact `document_type` and load `legal-os-template-runtime` as an auxiliary. For T-02 pleadings, also record `procedure_type`, `pleading_role`, `document_variant` and `paired_evidence_catalog_required=true`; the resolver must return the pleading template and paired evidence-catalog template.
7. Check subject, date, amount, legal relationship, evidence, file version and authority conflicts. Mark G1 minor gap, G2 important gap, or G3 core gap.
8. Select an execution mode. Use `route-only` when the user asks only for classification, the next workflow requires a missing external capability, or execution authority is not established. Use `route-and-run` when the route is clear and the selected workflow may proceed in the same task.
9. If the route is clear, no G3 or authorization stop applies, and the mode is `route-and-run`, continue into the selected workflow. Otherwise return the routing decision, focused questions, or a clearly labelled pending-verification version.

## Execution contract

- `route-only`: return the complete routing decision and next action; do not load or execute the primary workflow.
- `route-and-run`: return the routing decision, then load the primary workflow only if all stop and authorization gates pass.
- Apply [office-source-policy.md](references/office-source-policy.md) before loading a document, spreadsheet or template helper. A helper's default rendering instruction never changes the active policy or its `visual_check_mode`; an explicit user instruction not to render is a hard stop.
- Every decision must contain exactly one `primary_route`. Additional capabilities are `auxiliary_routes`; they never become competing primary routes.
- A route identifies the workstream. It does not guarantee that every required connector, source, or external service is bundled.
- `G3` always returns `stopped`. Sending, filing, signing, publishing, pushing, settling, waiving, releasing, terminating, or making another external commitment returns `awaiting-authorization` until separately authorized.
- `TEMPLATE_REQUIRED`, `TEMPLATE_AMBIGUOUS`, and `TEMPLATE_INTEGRITY_FAIL` stop file generation. They do not prevent source analysis or a clearly labelled text-only internal draft when that remains useful.
- A requested external action adds an authorization blocker but does not by itself raise R2 to R3.
- Add a blocker only when the request or available materials establish it; do not infer blockers solely from the document category.

## Route map

- `T-01` contract review/redline → `legal-os-contract`; add data and document QA only as needed.
- `T-02` pleadings and `T-04` litigation strategy → `legal-os-litigation`; use its evidence-mapping and legal-research phases as needed. T-02 remains one primary route while `procedure_type`, `pleading_role` and `document_variant` select the correct civil, commercial-arbitration or labour/personnel-arbitration variant. A complaint, application or answer requires a paired evidence catalogue.
- `T-03` evidence register/proof mapping → the evidence-mapping phase in `legal-os-litigation`; do not infer authenticity, admissibility, or weight.
- `T-05` legal research → use `cn-law-hub` for laws, regulations, rules, judicial interpretations, treaties and article-level current-status verification; use `cn-case-hub` for cases, guiding cases, typical cases, case-number verification and adjudicative viewpoints. Treat both as research auxiliaries to the substantive primary workflow. Every formal proposition must enter the authority package with an actually accessed official source, access date, pinpoint and verified status; memory, model knowledge, search snippets and third-party summaries are leads only.
- `T-06` lawyer letters, payment/performance notices, replies, situation statements → `legal-os-correspondence`.
- `T-07` business chat, email, oral or leadership wording → `legal-os-business-communication`; check audience and commitment boundaries.
- `T-08` amounts, payments, interest, formulas, dates and data conflicts → `legal-os-data-verification`; keep raw and derived values separate.
- `T-09` Word/PDF conversion, packaging and archive → `legal-os-file-delivery`; verify version and privacy boundary.
- `T-10` reports, summaries and presentations → `legal-os-reporting-presentation`; verify facts and metrics before polishing.
- `T-11` named matter/project background → `legal-os-matter-memory`; treat private memory as a lead and re-verify current facts.
- `T-12` reusable user correction or system failure → `legal-os-learning-maintenance`; retain only a net-new rule delta after semantic deduplication. Ordinary tasks do not load the maintenance Skill merely to restate existing coverage.

## Hard stops

Pause and state the exact blocker when:

- core subjects, dates, amounts, contract/case identity, legal relationship or key evidence conflict;
- a formal deliverable lacks support for a core assertion;
- the output could admit liability, waive a right, settle, release, terminate, or make an external commitment;
- current law or procedural authority is required but has not been verified;
- privacy, confidentiality, personal information, public-repository or permission boundaries are unclear.

Do not resolve a core conflict by guessing, silently selecting one version, or treating an old memory as current fact.

## Loading rule

Run `Kernel + one primary workflow + necessary auxiliaries + the corresponding deliverable QC`; add `legal-quality-gate` only for formal or high-risk final delivery. The intake skill is a router, not a substitute for the selected legal workflow. Do not load all modules just because they exist.

The public Kernel inventory, route definitions, profiles, and invocation policy are declared in `legalos.manifest.json`. If explanatory documentation conflicts with that manifest, stop and report a repository-consistency issue instead of silently choosing one version.

## Output contract

Return a routing header before any workflow content. Every key in [references/routing-output-contract.schema.json](references/routing-output-contract.schema.json) is mandatory; use `[]`, `null`, or an empty string instead of omitting a key:

```json
{
  "mode": "route-only | route-and-run",
  "primary_route": "T-01 ... T-12",
  "auxiliary_routes": [],
  "risk": "R0 | R1 | R2 | R3",
  "gap": "G0 | G1 | G2 | G3",
  "status": "routed | ready | stopped | awaiting-authorization",
  "decision_interview": {"mode": "none | ladder", "questions_used": []},
  "confirmed_facts": [],
  "missing_facts": [],
  "blockers": [],
  "expected_deliverable": "",
  "next_action": ""
}
```

Use route codes only in route fields and stable kebab-case blocker codes in `blockers`; put explanations in `missing_facts` or `next_action`. `G3` has status priority and must return `stopped`; preserve any separate authorization issue in `blockers`. For `route-only`, this header is the complete response. For `route-and-run`, emit it first and continue only when no stop applies. When a decision interview is used, create a record conforming to [references/decision-interview.schema.json](references/decision-interview.schema.json). External sending, filing, signing, publishing, repository pushing and other state-changing actions require separate authorization.

## Public/private boundary

Keep public Skills generic. Never copy real client names, contract titles, matter facts, private paths, credentials, or unverified conclusions into the Skill or public repository.
