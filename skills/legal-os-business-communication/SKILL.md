---
name: legal-os-business-communication
description: Source-locked Chinese business communication workflow for drafting and checking internal messages, business WeChat, emails, phone or meeting talking points. Use when the user asks for a business communication wording, leadership or project update, coordination message, counterparty working email, call script, or wants a draft checked for factual and commitment risk; route formal notices, legal authority, amounts, reporting/PPT, and file/archive work to the corresponding Legal OS workflow.
---

# Legal OS Business Communication

Use T-07 for non-formal business communication. Keep the message useful and short, but do not trade away fact accuracy, evidence traceability, authorization, or rights boundaries.

## Intake

Read every in-scope file first and record only the minimum needed:

- matter or project, audience, channel, objective, role, verified facts and sources;
- requested action, deadline, attachments, output shape, internal/external boundary;
- known conflicts, missing facts, and sending/approval permission.

Do not ask the user to repeat information already present in the files.

## Route and risk

Choose one primary T-07 path:

- leadership update or decision request;
- business/project coordination;
- internal cross-team message;
- ordinary counterparty working communication;
- phone or meeting talking points.

Use R0 for low-risk internal wording, R1 for ordinary business coordination, R2 for counterparty or payment/performance-adjacent communication, and R3 for rights-impacting or formal consequences.

Add only necessary auxiliaries:

- contract, litigation, evidence, or data modules when their facts are needed;
- T-05 legal research when the message asserts current law or procedure;
- T-06 formal correspondence when the message is a demand, default notice, lawyer letter, government/court explanation, or may serve formal notice;
- T-08 data verification when amounts, payments, interest, dates, or formulas conflict;
- T-10 reporting/PPT when the requested deliverable is a formal leadership report or presentation.

## Drafting sequence

1. Lock facts: separate verified material facts, user statements, inferences, and pending verification.
2. State the purpose in the first sentence.
3. Give only the facts needed for this audience.
4. State the requested action, owner, deadline, and reply method.
5. Scan for admissions, concessions, new prices, fixed deadlines, liability, settlement, waiver, release, termination, or unauthorized external commitments.
6. Match the channel: short and copyable for WeChat; subject/paragraph/action structure for email; opening goal, known facts, safe confirmations, and hold points for calls; issue/impact/options/recommendation/owner for internal notes.
7. Preserve a version and evidence/attachment trail when the communication matters.
8. When the requested deliverable is a standard DOCX communication artifact rather than copyable plain text, use `legal-os-template-runtime` to resolve and hash-check the channel template. Preserve its fixed shell while expanding the body for the actual audience and issue; stop with `TEMPLATE_REQUIRED` instead of creating an unrelated layout.

## Hard stops

Pause and state the exact blocker when:

- subjects, dates, amounts, contract/matter identity, legal relationship, or key evidence conflict;
- the draft would admit liability, accept a price or deadline, waive a right, settle, release, terminate, or create an external commitment;
- external sending permission, recipient, confidentiality, personal information, or attachment version is unclear;
- formal legal effect or unverified current law is required.

Return a clearly labelled internal draft or the minimum focused questions; do not guess or silently choose a version.

## Output contract

Report the primary route, auxiliary routes, risk level, confirmed facts, missing facts, stop/continue status, intended audience/channel, and the draft or next action. Keep internal strategy, process notes, paths, and AI traces out of any copyable external text.

## Public/private boundary

Keep this Skill generic. Never copy real client names, matter titles, contract text, private paths, credentials, or unverified legal conclusions into it or a public repository.
