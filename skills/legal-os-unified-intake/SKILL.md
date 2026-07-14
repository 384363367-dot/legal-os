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

- `T-01` contract review/redline → `legal-os-contract`; add evidence/data/Word QA only as needed.
- `T-02` pleadings and `T-04` litigation strategy → litigation workflow; add evidence and current-law research as needed.
- `T-03` evidence register/proof mapping → evidence workflow; route procedure questions separately.
- `T-05` current laws, regulations, cases → legal research workflow; do not use memory or third-party summaries as authority.
- `T-06` lawyer letters, payment/performance notices, replies, situation statements → formal correspondence workflow.
- `T-07` business chat, email, oral or leadership wording → communication workflow; check audience and commitment boundaries.
- `T-08` amounts, payments, interest, formulas, dates and data conflicts → `legal-os-data-verification`; keep raw and derived values separate.
- `T-09` Word/PDF conversion, packaging and archive → document/file-delivery workflow; verify version and privacy boundary.
- `T-10` reports, summaries and presentations → reporting workflow; verify facts and metrics before polishing.
- `T-11` named matter/project background → load only the relevant private case memory as a lead; current facts still require current-material verification.
- `T-12` user correction or system failure → classify as Router, Workflow, Rule, Memory, QC or Tool before changing long-term behaviour.

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
