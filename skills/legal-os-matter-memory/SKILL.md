---
name: legal-os-matter-memory
description: Lean, source-locked Chinese legal matter-memory workflow for classifying, retrieving, updating, reviewing, slimming, and archiving matter clues, dynamic facts, long-term rules, templates, Skills, and temporary context. Use when the user says remember this, save the project background, optimize or clean memories, review a long-term rule, create a memory candidate, or migrate repeated work into a Skill/template; never treat memory as current legal authority or current fact.
---

# Legal OS Matter Memory

Use T-11 to keep matter memory useful without making it a second case file or an uncontrolled global rule store. Record the smallest traceable item, classify it, remove unnecessary sensitive data, and route it to the narrowest correct location.

## Intake and classification

For every candidate record source event, matter identity, date, scope, sensitivity, verification status, retention period, target location, and user-confirmation state. Classify it as:

- **L1 core rule** — durable cross-task boundary or working standard;
- **L2 specialized rule** — stable contract, litigation, delivery, research, communication, or data method;
- **L3 Skill/template/workflow** — repeatable operation or fixed form;
- **L4 matter clue** — party relationship, material index, historical issue, or project context;
- **L5 dynamic fact** — amount, date, payment, hearing, case status, policy, market or progress item;
- **L6 temporary context** — draft, guess, tool log, one-off path, or unconfirmed chat detail.

Use L1-L3 only when the item is stable and reusable. Keep L4 in the relevant matter/project memory. Keep L5 in a dated, source-linked verification record. Do not retain L6 as long-term memory.

## Workflow

1. Capture the smallest source-linked observation.
2. Classify L1-L6 and determine the narrowest target location.
3. Search existing rules, Skills, templates, matter records, and Frozen versions for semantic duplicates or conflicts.
4. Minimize names, amounts, dates, paths, strategy, privilege and personal data; create a generic version before any public sync.
5. Record source, verification date, status, scope and expiry/refresh trigger for dynamic facts.
6. Choose `Keep`, `Merge`, `Downgrade`, `Convert`, `Archive`, or `Skip`.
7. Generate a candidate diff and obtain user confirmation before changing long-term rules, matter memory, Skills, templates, or automations. Preserve old Frozen versions and a rollback path.
8. Review for stale, duplicate, unsupported or over-broad content and produce a slimming list.
9. When producing a standard DOCX matter card, dynamic-fact record or candidate-diff artifact, use `legal-os-template-runtime` to resolve and hash-check the registered template. Preserve the fixed shell, add rows or sections as needed, and keep case-specific content in the private workspace.

## Retrieval rules

Use trigger-based loading: current materials first, the named matter's L4/L5 records next, then only the L1-L3 rules or Skills required by the task. Old memory is a clue, not proof. If current material conflicts with memory, current material controls and the conflict is recorded.

## Route boundaries

- Reusable observations, corrections, defects or learning candidates → T-12 Learning Engine.
- Contract, litigation, evidence, research, correspondence, communication or data substance → relevant primary workflow.
- File conversion, privacy cleaning, indexing or archiving → T-09 file delivery.
- Reporting or presentation output → T-10 reporting/presentation.

## Hard stops

Pause when a case-specific fact is proposed for L1 or public Skill; a dynamic amount/date/status lacks a source or conflicts; personal data, commercial secrets, internal strategy or privileged material has no clear boundary; “remember this” lacks scope or retention; or an update would overwrite/delete/alter a Frozen asset without confirmation.

## Output contract

Report the candidate, classification, current coverage, target location, source and verification status, sensitivity decision, retention/refresh rule, proposed action, risks, rollback, and whether user confirmation is required. Do not expose private paths, client identifiers, dynamic facts or internal strategy in a public/copyable package.
