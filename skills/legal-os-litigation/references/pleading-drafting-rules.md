# Pleading drafting rules

Apply these rules when generating or substantively reviewing a complaint, arbitration application, civil answer or arbitration answer.

## R1 — Resolve the procedure variant first

Classify `procedure_type`, `pleading_role` and `document_variant` before template resolution. Civil litigation, commercial arbitration, labour/personnel arbitration and other procedures do not share identical requests, cost rules or mandatory fields. Stop with `PROCEDURE_VARIANT_REQUIRED` when the variant cannot be established from current material.

## R2 — Analyse broadly, plead through a controlled route

The internal work product may identify all reasonable claims, defences, alternatives and risks. The external pleading should use the strongest compatible route that covers the requested outcome without unnecessary admissions or exposure. Add an alternative position only when the primary route is incomplete and the alternative is factually and legally compatible.

## R3 — Applications must establish each requested remedy

For every claim, connect:

`executable relief and calculation → legal elements → material facts → evidence → jurisdiction, limitation and required procedure → verified current authority`

Do not replace facts with abstract legal conclusions or omit an element merely to keep the document short.

## R4 — Answers use an issue-scope gate

Respond to the opposing party's actual claims, alleged facts and legal grounds. Do not volunteer a new claim basis, admit an unproved fact, open an unnecessary adverse exception, or disclose internal fallback strategy. Screen possible defences in this order only as applicable: dispositive procedure; prior agreement, satisfaction or extinguishment; missing elements; amount/calculation; compatible alternative defence.

## R5 — Use conclusion-led headings

Each substantive heading should state a conclusion a decision-maker could adopt. Use the unit:

`conclusion → material facts → evidence anchor → necessary legal evaluation → effect on the claim or defence`

Avoid empty headings such as “relevant circumstances” and repeated conclusory adjectives.

## R6 — Cite authority by function

Before placing authority in the external pleading, ask whether it decides the issue, is needed to complete the claim or defence, responds to an argument actually raised, and whether its proviso or exception would unnecessarily enlarge an adverse issue. Verify current status and an official or otherwise authoritative source. Keep nonessential or contingency authority in the internal authority package.

## R7 — Do not exceed the evidence

Prefer complete originals and signed records to screenshots, OCR or recollection. Keep ambiguous handwriting, amounts, dates or identities unverified. A payment record proves only the parties, time, amount and displayed purpose shown on it; do not infer an unsupported allocation or full settlement. Separate fact, inference and legal evaluation in the internal work product.

## R8 — Generate the pleading and evidence catalogue as a pair

Every complaint, application or answer has `paired_evidence_catalog_required=true`. Only a request limited to strategy, outline or isolated wording falls outside this rule. If evidence is incomplete, create a `待补证 / 内部草稿` catalogue rather than omitting the paired artifact.

## R9 — No independent evidence-source chapter

Do not create an independent “证据和证据来源” or equivalent chapter inside a complaint, application or answer. Use concise evidence anchors in the relevant factual paragraph when useful. Put evidence number, name, page range and proof purpose in the independent evidence catalogue.

## R10 — Keep the external catalogue lean and the internal map complete

The external catalogue normally uses `编号 | 证据名称 | 页码 | 证明事项`. A proof purpose must identify the claim, element, material fact or defence it supports. The private fact–evidence map additionally records source, formation date, original status, authenticity/completeness risk, corresponding proposition, gaps and review state.

## R11 — Test alternative defences for compatibility

Place an alternative defence in the external answer only if the primary defence does not fully cover the claim, it does not negate a key primary fact or reasonably read as an admission, it has evidence and verified law, and disclosure does not materially expand the opposing party's attack path. Otherwise keep it in the internal hearing plan.

## R12 — The template controls the shell, not the adjudication path

The template controls visual identity, minimum functional sections and signature placement. It does not control paragraph count, create an unraised issue, supply a missing fact/evidence/authority, preserve a procedure-inapplicable cost request, or restore an evidence-source chapter. If the selected variant conflicts with the matter, stop with `TEMPLATE_VARIANT_REQUIRED` rather than silently converting it into a final document.

## Pair consistency gate

- Every pleading evidence reference must resolve to one catalogue item.
- Every catalogue item must support at least one claim, element, material fact or defence.
- Renumbering, renaming or changing a proof purpose requires synchronized updates across both artifacts.
- Unknown page ranges remain `待编页`; never invent pagination.
- Distinguish evidence submitted by the represented party from material filed by another party.
