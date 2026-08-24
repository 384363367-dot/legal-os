---
name: legal-os-learning-maintenance
description: Lean maintenance workflow for Legal OS continuous improvement. Use only when the user asks to review, optimize, update, promote, merge, simplify, delete, or weekly-maintain reusable Legal OS rules/Skills/workflows, or when a critical runtime defect requires an immediate hotfix. Ordinary legal tasks do not load this Skill.
---

# Legal OS Learning Maintenance

Maintain Legal OS by promoting only net-new, reusable improvements back into the single canonical Skill, Reference, Template, Script, or Gate that owns the behavior. Do not build a parallel rule stack.

## Invocation boundary

Use this Skill only for:
- the scheduled weekly Legal OS optimization review;
- an explicit user request to optimize or update Legal OS;
- a critical defect that can materially cause wrong legal output, source-file corruption, loss of tracked changes, fabricated facts/authorities, use of invalid authority, or failed formal delivery.

Do not load this Skill during ordinary contract, litigation, research, correspondence, data, reporting, memory, or file-delivery work merely because those tasks may generate observations.

## Net-new-only rule

Before a learning candidate is retained, compare it semantically with the narrowest likely canonical target.

- If the current target already covers the behavior adequately, discard the observation. Do not record “already covered”, duplicate summaries, or restatements.
- Retain only a proposed `ADD`, `REPLACE`, `TIGHTEN`, `SIMPLIFY/MERGE`, or `DELETE`.
- A candidate must state only the new delta needed, not re-describe the existing Skill.
- Matter facts, client-specific positions, one-off negotiation choices, changing legal authority, amounts, dates, paths, tool logs, and unverified guesses are not reusable learning candidates.

## Minimal candidate

A retained pending candidate should contain only:
- candidate id and date;
- source workflow or defect event;
- proposed action: `ADD`, `REPLACE`, `TIGHTEN`, `SIMPLIFY/MERGE`, or `DELETE`;
- narrow canonical target;
- proposed rule delta;
- short reason or reproducible failure evidence.

Do not create a DOCX or long report for routine candidates. Pending candidates are maintenance input, not runtime authority, and ordinary workflows must not read them.

## Weekly maintenance

Default cadence is one consolidated review per week.

Cadence is a review target, not proof that an automatic scheduler exists or has been configured.

- State that a review will run automatically only when the current runtime actually exposes scheduling/automation capability and that capability has been configured for this maintenance task.
- If no scheduler is available, or a scheduled cycle was not actually executed, the next explicit maintenance invocation must perform a catch-up review for the most recent unreviewed cycle before continuing with the current cycle.
- A planned review time must never be reported as a completed review. Completion exists only after the candidate search/review has actually run and the outcome is recorded as either an applied maintenance change or `本周无需更新`.
- For catch-up review, use candidate `event_date` and the existing recent-search window to handle delayed uploads without inventing a prior completion record.

1. Load only the pending candidates and the specific canonical targets they name. Do not load all Legal OS Skills.
2. Re-check semantic duplication and scope. If already covered, discard immediately.
3. Reject matter-specific, unstable, unsupported, privacy-sensitive, or overfitted proposals.
4. Choose the smallest effective action: `ADD`, `REPLACE`, `TIGHTEN`, `SIMPLIFY/MERGE`, or `DELETE`.
5. Edit the existing canonical target directly. Do not create a lasting overlay, patch file, “new rules” companion, or competing version in the runtime path.
6. Prefer replacement, merge, simplification, or deletion when they can strengthen behavior without increasing rule volume.
7. Run the target workflow's existing tests, scripts, Quality Gate, and any new regression test required by the change.
8. If the change affects routing, Skill inventory, template registration, package metadata, or machine gates, update the Runtime Index / manifest / affected registry in the same maintenance release.
9. Release a new package snapshot only after checks pass. Keep the previous package outside the active runtime as rollback material.
10. Remove processed candidates from the pending set. Historical diffs or old packages are audit/rollback material only and are never loaded as current rules.

## Critical hotfix

Do not wait for the weekly cycle when a confirmed defect can materially cause:
- an incorrect legal conclusion or fabricated fact/authority;
- source-file corruption or loss/acceptance/rejection of tracked changes without authorization;
- use of invalid or unverified current authority in a formal conclusion;
- a formal deliverable that cannot pass its required release gate.

Apply the same net-new, canonical-target, minimal-diff, test, release, and rollback rules. A hotfix is an accelerated weekly-maintenance cycle, not a bypass.

## Canonical-source rule

For every behavior there must be one current runtime authority.

- Business rules stay in the owning business Skill or its canonical Reference/Script/Gate.
- Cross-workflow shared behavior stays in the existing shared canonical policy when one exists.
- This Skill governs how improvements are promoted; it does not become a warehouse of contract, litigation, research, Office, or other business rules.
- Old package versions, diffs, changelogs, pending candidates, and archived material never override the current canonical target.

## Release standard

A maintenance change passes only when:
- it adds net capability or corrects/removes a real defect without duplicating existing text;
- the target and scope are the narrowest appropriate;
- affected tests/gates pass;
- current Runtime Index and package manifest are internally consistent;
- rollback is possible from the previous package snapshot.

The preferred outcome is stronger behavior with the same or fewer runtime rules.
