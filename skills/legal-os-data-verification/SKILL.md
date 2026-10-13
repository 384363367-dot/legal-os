---
name: legal-os-data-verification
description: Source-locked amount, payment, deadline-node, and data-gap verification for Chinese legal work. Use when reviewing contract or dispute figures, reconciling invoices/payments, building a calculation ledger, checking date nodes, or recording source conflicts and missing evidence before a legal deliverable.
---

# Legal OS Data Verification

## Overview

Build a traceable verification ledger that keeps source values, derived calculations, and human conclusions separate. The workflow is an evidence and arithmetic control layer; it does not itself establish legal liability, a current-law deadline, entitlement, admission, waiver, settlement, or an external communication.

## Workflow

### 1. Route the task

- Use this skill for numerical, date-node, reconciliation, and source-gap work.
- Pair with `legal-os-contract` for contract interpretation/redline work and `legal-os-litigation` for procedure, strategy, and evidence mapping. Current Chinese law requires an available authoritative research capability. Use `legal-quality-gate` for final review and release control; external sending, filing, signing or publishing still requires separate human authorization.
- If the user provides a workbook, inspect the existing workbook before changing it; preserve its structure unless a targeted change is requested.

### 2. Lock the source layer

Capture, at minimum: record ID, source file/page or other locator, item, date, currency, unit, quantity, unit price, tax rate, tax basis, source amount, paid/received amount, evidence status, and note. Use blank or `待核` when the source does not support a value. Never fill a missing value by inference and never overwrite the source amount with a calculated amount.

Use typed numbers and dates in spreadsheets. Keep currencies separate unless an explicit, source-backed conversion rate and conversion date are supplied. Record the source URL or file locator in a dedicated source field when applicable.

### 3. Recalculate amounts

For each valid record, show source amount, calculation base, tax, calculated total, variance, verification status, evidence status, and expected balance in separate columns.

Use simple auditable formulas. For the standard two-way demo schema:

- `不含税`: quantity × untaxed unit price × (1 + tax rate)
- `含税`: quantity × untaxed unit price
- variance: source amount − calculated total
- status: blank ID → blank; blank source amount → `缺原始金额`; absolute variance below the stated tolerance → `一致`; otherwise `不一致`

Do not silently apply rounding, tax inclusion, or a currency conversion. Make the rounding/tolerance rule visible and pause when the source uses a different formula structure. A numerical match is not proof of legal entitlement.

For a multi-step claim or contract amount, keep one traceable chain from the source amount through each adjustment to the reported balance. Preserve the original amount and record, for every adjustment, its evidence-based `factor_id`, source locator, nature, explicit calculation basis, rate or fixed amount, deduction, and resulting remaining balance. The basis reference may identify the original amount or an earlier adjustment result; calculate the deduction from that stated basis, then subtract it from the immediately preceding remaining balance. This supports distinct sequential factors that use different agreed bases while keeping each balance auditable. Record factors already included in the starting amount. Reuse the same factor identity across adjustments, payments, and offsets so a factor already included or applied cannot be deducted again. A matching percentage or label alone does not prove that two factors are the same: distinct source-backed factors may apply sequentially, including on different stated bases, when their nature and source are recorded.

When any source amount or basis changes, recalculate every dependent deduction, adjusted gross amount, payment total, offset total, net balance, and conclusion. The existing release gate can verify the recorded arithmetic chain and its hash-bound sign-off, including stated bases, rates/fixed deductions, remaining balance, payments, offsets, rollups, and the reviewer’s confirmation that final artifact amounts and conclusions were reconciled (`artifact_amounts_reconciled=true` with a `conclusion_review`). It does not decide whether a deduction is legally available or whether the selected basis is contractually correct. If a required source, evidence status, or calculation basis is missing or conflicting, record `unable-to-verify` and stop the formal amount conclusion instead of substituting zero or a default `PASS`.

For the registered amount workspace, record a calculation chain once in the existing `原始记录_输入` sheet; do not create a second amount ledger. Keep the original amount in J and paid/received amount in K. Use N:X for chain ID, row type, factor ID, calculation basis, factor type/value, initially included factors, rounding, and (only when an original row's K is non-zero) a separate payment locator and evidence status. Fixed adjustments and offsets use J; percentage adjustments use S as a decimal rate; dedicated payment rows use K. If the original row's K is non-zero, W:X are required because B/L may describe only the quoted or contractual amount, not proof of payment. Do not also enter that same payment as a second row.

When the exporter reads a numeric input marked `待核`, it writes a `null` calculation value and an unresolved gap; it does not treat the marker as zero. Other non-numeric input remains a blocking data error.

For an original ledger row, blank column K does not establish that no payment occurred. If K is blank and there are no dedicated payment rows, the export keeps payment and net totals `null` with an unresolved gap; enter an explicit `0` only after the source and human review confirm no payment. If dedicated payment rows are the chosen record path, K may remain blank and the exporter uses those rows once without adding a duplicate blank-K entry.

Generate the existing sign-off `amount_review` record with the bundled script:

```bash
python skills/legal-os-data-verification/scripts/export_amount_review.py \
  --workbook WORKSPACE.xlsx --artifact FINAL.docx \
  --signoff SIGNOFF.json --out-signoff SIGNOFF.amount.json
```

The script reads the existing ledger and writes a separate sign-off copy. It reuses an existing amount reviewer, time and conclusion only when the source/calculation chain exactly matches that already reviewed. It never invents source locators, legal bases or approval. Missing payment proof, incomplete source fields, or a changed chain stays `unable-to-verify`; a changed chain is marked as requiring affected review even when the deliverable file hash did not change. Final release still requires a human-reviewed `verified` record and the ordinary release gate.

### 4. Check date nodes

Record trigger date, due date, source-stated days, date basis, calendar status, and human review note. A `TODAY()`-style calendar flag may say `已到期`, `今日到期`, `未到期`, or `待核`, but it must be labelled as a calendar prompt only. Do not call it a statutory deadline, limitation period, procedural period, or waiver date without current-law and source verification.

### 5. Track conflicts and gaps

Open a ledger row for a missing page, missing voucher, conflicting amount, unclear tax basis, inconsistent payment record, ambiguous date, or unsupported assumption. Record related ID, description, source A/B, severity, status (`待处理`/`处理中`/`已解决`/`不适用`), owner, and review note.

### 6. Apply the quality gate

Before delivery, verify:

- every effective record has a source locator;
- every derived amount is still a formula and has no formula error;
- every source/derived variance is labelled;
- evidence status is not silently treated as confirmed;
- all conflicts and gaps are resolved or explicitly escalated;
- dates and calculation bases are source-backed;
- when a formal deliverable relies on multi-step calculated amounts, its human sign-off includes the hash-bound `amount_review` record and the existing release gate is run with `--amount-review-required`; arithmetic verification does not replace review of the legal nature or claim basis;
- external output, filing, settlement, admission, waiver, termination, or other high-impact action has separate authorization.

If any blocking condition remains, return `暂停交付` or `需复核`, state the exact gap, and stop rather than smoothing the result.

## Spreadsheet artifact requirements

For ordinary editable Excel, apply [the shared Office source policy](../legal-os-unified-intake/references/office-source-policy.md) before loading any helper. Do not render by default; the policy's explicit user instruction not to render is a hard stop.

When creating or editing `.xlsx`/`.csv` artifacts, use the `spreadsheets` skill and its bundled `@oai/artifact-tool` runtime. Keep an editable raw-input sheet, formula-driven calculation sheet, date-node sheet, conflict/gap ledger, and visible quality gate. Inspect workbook structure, key values, formulas and `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?`, and `#N/A` errors before export. Do not render every sheet by default: visual rendering is only an auxiliary check when the user explicitly requests it or a concrete layout/print concern exists, and it must not block a structurally valid workbook. Do not use `openpyxl`, `pandas.ExcelWriter`, or alternate workbook authoring libraries unless the user explicitly requests them.

For a new standard workbook, use `legal-os-template-runtime` to resolve and hash-check the registered amount/date-node workbook before entering data. Use clearly labelled synthetic demo rows only when they help prove formulas; mark them as demo data and remove them before real case entry. Keep the workbook source-locked and user-editable. Stop with `TEMPLATE_REQUIRED` instead of silently building a different workbook layout when the registered template is unavailable.

## Boundaries

- Never place real client names, contract titles, case facts, private paths, credentials, or unverified legal conclusions in a public Skill or public repository.
- Do not use this Skill as a substitute for current-law research, evidence authentication, contract interpretation, or counsel judgment.
- Do not send, file, sign, publish, push, or otherwise execute an external action based solely on a workbook status.
