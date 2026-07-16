---
name: legal-os-unified-intake
description: Source-locked intake and task routing for Chinese legal work. Use when a request or file could belong to contracts, litigation, evidence, legal research, formal correspondence, business communication, data verification, file delivery, reporting, memory, or rule review and the correct primary workflow must be selected before execution.
---

# Legal OS Unified Intake

## Purpose

Identify the user's real task, role, risk, materials, output audience, and missing information before loading a specialist workflow. Keep facts, rules, evidence, calculations, legal authorities, and delivery QC separate.

## Intake sequence

1. Read the user request and every attached file that is in scope. Do not ask the user to repeat information already present in the files.
2. Record the minimum intake: matter name/identifier, user and counterparty roles, objective, files/versions/attachments, key dates, expected output, audience, internal/external boundary, and known conflicts or gaps.
3. Classify risk: R0 ordinary, R1 professional, R2 formal legal, R3 major/high-impact. Raise the level when the output may affect payment, liability, admission, waiver, settlement, termination, filing, qualification, or external rights.
4. Select exactly one primary route. Load only the necessary secondary routes and output quality gate.
5. Check subject, date, amount, legal relationship, evidence, file version and authority conflicts. Mark G1 minor gap, G2 important gap, or G3 core gap.
6. If the route is clear and no G3 stop applies, continue into the selected workflow. If not, return the minimum focused questions or a clearly labelled pending-verification version.

## Route map

- `T-01` contract review/redline → `legal-os-contract`; add data and document QA only as needed.
- `T-02` pleadings and `T-04` litigation strategy → `legal-os-litigation`; use its evidence-mapping and legal-research phases as needed.
- `T-03` evidence register/proof mapping → the evidence-mapping phase in `legal-os-litigation`; do not infer authenticity, admissibility, or weight.
- `T-05` current laws, regulations, cases → keep the substantive primary Skill and use an available authoritative research capability; do not use memory or third-party summaries as authority.
- `T-06` lawyer letters, payment/performance notices, replies, situation statements → `legal-os-correspondence`.
- `T-07` business chat, email, oral or leadership wording → `legal-os-business-communication`; check audience and commitment boundaries.
- `T-08` amounts, payments, interest, formulas, dates and data conflicts → `legal-os-data-verification`; keep raw and derived values separate.
- `T-09` Word/PDF conversion, packaging and archive → `legal-os-file-delivery`; verify version and privacy boundary.
- `T-10` reports, summaries and presentations → `legal-os-reporting-presentation`; verify facts and metrics before polishing.
- `T-11` named matter/project background → `legal-os-matter-memory`; treat private memory as a lead and re-verify current facts.
- `T-12` user correction or system failure → classify the observation here, then use `legal-os-matter-memory` to record a candidate without automatically changing global behavior.

## Hard stops

Pause and state the exact blocker when:

- core subjects, dates, amounts, contract/case identity, legal relationship or key evidence conflict;
- a formal deliverable lacks support for a core assertion;
- the output could admit liability, waive a right, settle, release, terminate, or make an external commitment;
- current law or procedural authority is required but has not been verified;
- privacy, confidentiality, personal information, public-repository or permission boundaries are unclear.

Do not resolve a core conflict by guessing, silently selecting one version, or treating an old memory as current fact.

## Loading rule

Run `Kernel + one primary workflow + necessary auxiliaries + the corresponding deliverable QC`. The intake skill is a router, not a substitute for the selected legal workflow. Do not load all modules just because they exist.

## Output contract

Report the selected primary route, any auxiliary routes, risk level, confirmed facts, missing facts, stop/continue status, expected deliverable, and the next action. Keep internal reasoning and strategy out of formal external text. External sending, filing, signing, publishing, repository pushing and other state-changing actions require separate authorization.

## Public/private boundary

Keep public Skills generic. Never copy real client names, contract titles, matter facts, private paths, credentials, or unverified conclusions into the Skill or public repository.
