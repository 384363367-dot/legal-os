# Amount and Data Verification Workspace

Generic source-locked verification for amount reconciliation, payment records, date nodes and source conflicts.

- preserve source values/locators;
- separate formulas/derived calculations from legal conclusions;
- maintain a conflict/gap ledger;
- route contract meaning to contract, procedure/strategy/evidence to litigation, and current law to the T-05 default `cn-legal-research` adapter;
- do not let arithmetic status authorize external action.

## One-entry amount chain

For the registered amount workbook, enter each amount-chain row once on the existing `原始记录_输入` sheet. Existing fields remain the source layer: A record ID, B source locator, C item/nature, E currency, J source amount, K paid/received amount, and L evidence status. The template adds N:X for the chain ID, row type, factor ID, calculation basis, factor kind/value, initially included factors, rounding rule, and payment source/evidence when a non-zero payment is already present in K. No second amount ledger is created.

Use an explicit `无` in T when the starting amount includes no prior factors; a blank inventory stays unresolved. Fixed adjustments and offsets use J once; percentage adjustments use S as a decimal rate. Dedicated payment rows use K. When the original row already has a non-zero K amount, keep that amount there and complete W:X with its separate payment locator and evidence status; B/L do not by themselves prove payment. Non-zero J/K rows without a chain type are reported as gaps rather than silently omitted.

The bundled `skills/legal-os-data-verification/scripts/export_amount_review.py` reads the workbook without rewriting it and writes a copy of the existing sign-off JSON containing derived chain records and hash metadata. It can reuse a prior human amount conclusion only when the artifact and generated source/calculation chains still match that reviewed record. Missing sources or evidence produce an `unable-to-verify` warning; changed chains require affected review even if the deliverable file did not change. The exporter never supplies legal bases, source evidence, or human approval. Final still requires an independently human-reviewed `verified` amount record and the ordinary release gate.

For numeric inputs, a literal `待核` is exported as `null` with a review gap rather than as zero; malformed numeric text remains blocked.

For an original record, blank K is not evidence of no payment: without dedicated payment rows, export a null payment/paid total/net total and review gap. Use an explicit `0` only when the source and human review support no payment. When dedicated payment rows are used, K may stay blank; the exporter totals those rows once and does not add a duplicate blank-K payment.
