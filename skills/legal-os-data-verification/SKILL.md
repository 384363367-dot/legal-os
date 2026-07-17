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
- Pair with `legal-os-contract` for contract interpretation/redline work and `legal-os-litigation` for procedure, strategy, and evidence mapping. Current Chinese law requires an available authoritative research capability, and formal external delivery requires the responsible organization's legal quality gate and approval process; neither dependency is bundled in this public package.
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
- external output, filing, settlement, admission, waiver, termination, or other high-impact action has separate authorization.

If any blocking condition remains, return `暂停交付` or `需复核`, state the exact gap, and stop rather than smoothing the result.

## Spreadsheet artifact requirements

When creating or editing `.xlsx`/`.csv` artifacts, use the `spreadsheets` skill and its bundled `@oai/artifact-tool` runtime. Keep an editable raw-input sheet, formula-driven calculation sheet, date-node sheet, conflict/gap ledger, and visible quality gate. Render every sheet, inspect key values and formulas, scan for `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?`, and `#N/A`, then export one final workbook. Do not use `openpyxl`, `pandas.ExcelWriter`, or alternate workbook authoring libraries unless the user explicitly requests them.

For a new standard workbook, use `legal-os-template-runtime` to resolve and hash-check the registered amount/date-node workbook before entering data. Use clearly labelled synthetic demo rows only when they help prove formulas; mark them as demo data and remove them before real case entry. Keep the workbook source-locked and user-editable. Stop with `TEMPLATE_REQUIRED` instead of silently building a different workbook layout when the registered template is unavailable.

## Boundaries

- Never place real client names, contract titles, case facts, private paths, credentials, or unverified legal conclusions in a public Skill or public repository.
- Do not use this Skill as a substitute for current-law research, evidence authentication, contract interpretation, or counsel judgment.
- Do not send, file, sign, publish, push, or otherwise execute an external action based solely on a workbook status.
