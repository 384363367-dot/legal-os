---
name: legal-os-matter-memory
description: Lean, source-locked Chinese legal matter-memory workflow for classifying, retrieving, updating, reviewing, slimming, and archiving matter clues, dynamic facts, and temporary context. Use when the user says remember this, save the project background, update or clean matter memory, or review a matter-specific memory item. Reusable system-rule or Skill optimization belongs to legal-os-learning-maintenance.
---

# Legal OS Matter Memory

Use T-11 to keep matter memory useful without making it a second case file or an uncontrolled global rule store. Record the smallest traceable matter item, remove unnecessary sensitive data, and keep current materials above memory.

For standard DOCX memory artifacts, apply [the shared Office source policy](../legal-os-unified-intake/references/office-source-policy.md) before loading any document helper; source inspection is primary and visual QA follows the runtime-aware mode selected by that policy.

## Intake and classification

Classify only matter-memory content:

- **L4 matter clue** — party relationship, material index, historical issue, or project context;
- **L5 dynamic fact** — amount, date, payment, hearing, case status, policy, market or progress item;
- **L6 temporary context** — draft, guess, tool log, one-off path, or unconfirmed chat detail.

Reusable corrections, defects, rules, templates, workflows, or Skill improvements are not matter memory. Route them to `legal-os-learning-maintenance`; do not duplicate them here.

For every retained L4/L5 item, record source event, matter identity, date, scope, sensitivity, verification status, retention period, target location, and user-confirmation state. Do not retain L6 as long-term memory.

## Workflow

1. Capture the smallest source-linked matter item.
2. Classify it as L4, L5, or L6.
3. Search the named matter memory for semantic duplicates or conflicts.
4. Minimize names, amounts, dates, paths, strategy, privilege and personal data; create a generic version before any public sync.
5. Record source, verification date, status, scope and expiry/refresh trigger for dynamic facts.
6. Choose `Keep`, `Merge`, `Archive`, or `Skip`.
7. Obtain user confirmation before changing or deleting retained matter memory when the change is material or would overwrite a previously confirmed item.
8. Review for stale, duplicate, unsupported or over-broad content and slim it.
9. When producing a standard DOCX matter card or dynamic-fact record, use `legal-os-template-runtime` to resolve and hash-check the registered template. Preserve the fixed shell, keep case-specific content in the private workspace, and check the resulting DOCX source structure, content and format properties.

## Retrieval rules

Use trigger-based loading: current materials first, then only the named matter's L4/L5 records needed for the task. Old memory is a clue, not proof. If current material conflicts with memory, current material controls and the conflict is recorded.

## Route boundaries

- Reusable observations, corrections, defects, rules, templates, workflow or Skill improvements → `legal-os-learning-maintenance`.
- Contract, litigation, evidence, research, correspondence, communication or data substance → relevant primary workflow.
- File conversion, privacy cleaning, indexing or archiving → T-09 file delivery.
- Reporting or presentation output → T-10 reporting/presentation.

## Hard stops

Pause when a case-specific fact is proposed as a reusable system rule; a dynamic amount/date/status lacks a source or conflicts; personal data, commercial secrets, internal strategy or privileged material has no clear boundary; “remember this” lacks scope or retention; or an update would overwrite/delete a confirmed matter item without authorization.

## Output contract

Report only the retained or changed matter-memory item, source/verification status, sensitivity or expiry issue when material, and any unresolved conflict. Do not produce duplicate “already covered” learning summaries and do not expose private paths, client identifiers, dynamic facts or internal strategy in a public/copyable package.
