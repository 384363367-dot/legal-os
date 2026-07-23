---
name: legal-quality-gate
description: "Source-locked final quality gate for formal Chinese legal work. Use before finalizing or releasing pleadings, legal opinions, evidence catalogs, court, arbitration or government materials, demands, notices, contract redlines, formal reports, external letters, or any legal deliverable affecting payment, liability, waiver, litigation, settlement, enforcement, qualification or organizational rights. Checks facts, evidence, current law, legal relationships, expression boundaries, privacy, human authorization and delivery format without treating memory or unsupported assertions as verified facts."
---

# Legal Quality Gate

## Core Rule

Use this skill as a final review layer before formal or high-risk legal delivery. It does not create legal facts or legal authorities. Verify facts against current materials and verify legal authorities against current effective Chinese law before treating them as final.

Read the current matter materials and any organization policy or approved template actually provided for the task. Do not assume a private rule library exists, invent missing policy, or embed organization names, personal paths, client data or matter-specific defaults in this Skill.

## Workflow

1. Identify use and audience: court, arbitration, government, leader, business unit, counterparty, external counsel, internal file.
2. Classify risk: if the output affects payment, liability, settlement, waiver, enforcement, qualification, contract rights, or litigation position, treat it as high-risk.
3. Separate formal text from internal analysis. Formal text must not contain strategy, risk notes, assumptions, temporary paths, OCR notes, or AI/process traces.
4. Verify facts: subject names, identities, amount, date, contract number, project, case number, court/arbitration body, procedural stage, payment, delivery, acceptance, invoice, breach, termination, limitation period.
5. Verify evidence: each key assertion must map to material evidence or be marked as unverified outside the formal text.
6. Verify law: current effective law, judicial interpretation, regulation, or authoritative rule. Do not use old memory, third-party skills, or uncited recollection as authority.
7. Review expression boundary: no unnecessary admission, waiver, concession, overstatement, emotional accusation, or exposure of backup arguments.
8. Review format and delivery: Word/table/page numbers/signature/date/attachments are clean and suitable for direct use.
9. Build the authority package for every material formal legal proposition. Laws and rules require current effective status; cases require an actually accessed, identifiable official/court source and `current_status=verified-source`. Model memory and secondary summaries are leads only.
10. Run the release lock. Final, filing, publishing, R2 and R3 outputs require a matter manifest and a sign-off whose matter ID, exact artifact path, SHA-256, risk level and permitted use match the current artifact. Contract Final also requires a matching `PASS` redline report.

## Machine release lock

Use `scripts/release_gate.py` and the schemas in `references/schemas/`. A failed gate means `BLOCKED`; a passing `internal-draft` means `DRAFT_ONLY`. Only a passing final intent returns `RELEASE`. Filenames, prior approvals, narrative explanations and old reports cannot override the exit code.

Publishing is permitted only for S0 material with `public_export_allowed=true`. When a public repository or export directory is relevant, pass each boundary with `--public-root`; S1—S3 matter outputs and S0 outputs lacking public-export approval cannot enter those roots. Sending, filing, signing, publishing or repository pushing still requires separate human authorization after the release gate.

For detailed checklist items, read `references/checklist.md`.

## Output Shape

When reporting the quality gate result, use this structure:

1. Pass / revise before delivery / blocked pending facts.
2. Must-fix issues.
3. Recommended refinements.
4. Facts or legal authorities still requiring verification.
5. Delivery-format checks.
6. Release decision (`BLOCKED`, `DRAFT_ONLY`, or `RELEASE`) and the exact missing control.

For simple low-risk text, keep the report short and only flag material issues.

## Hard Stops

Stop final delivery and ask for confirmation or evidence when:

- a core subject, amount, date, court, case number, contract, or legal relationship conflicts;
- a formal legal conclusion depends on unverified law or public information;
- the draft may admit liability, waive rights, accept a new condition, or expose strategy;
- the evidence cannot support a key claim;
- old memory conflicts with current material.
- an authority package, matter manifest or required sign-off is absent, stale, mismatched or unapproved;
- a case proposition lacks an actually accessed verified source;
- the release gate exits non-zero.
