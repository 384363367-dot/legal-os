# Amount and Data Verification Workspace

This is a generic, source-locked verification layer for amount reconciliation, payment records, calendar date nodes, and source conflicts or missing evidence.

## What it contains

- an editable raw-record layer that preserves source values and locators;
- formula-driven amount recalculation with visible tax basis, variance, and verification status;
- a calendar-only date-node sheet that does not replace current-law deadline analysis;
- a conflict/gap ledger for missing pages, vouchers, unclear bases, and inconsistent sources;
- a delivery quality gate that defaults to `暂停交付` or `需复核` when blocking gaps remain.

## Public-safe scope

The repository copy contains only the generic workflow and public-safe field rules. The workbook demo rows are synthetic and are not legal advice, a case conclusion, or a substitute for evidence or current-law verification. No client names, contract titles, case facts, private paths, or credentials are included.

## Use with other modules

Use the data-verification Skill for arithmetic and source-gap control. Route contract meaning and redlines to the contract workflow, procedure, strategy, and evidence mapping to the litigation workflow, and current Chinese law to an available authoritative research capability. Run the responsible substantive workflow's quality gate before any external document or action.

## Safety boundary

The workbook status is an internal control signal. It does not authorize sending, filing, signing, publishing, settling, admitting, waiving, terminating, or otherwise taking an external action.
