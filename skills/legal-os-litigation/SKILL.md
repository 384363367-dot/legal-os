---
name: legal-os-litigation
description: Source-locked Chinese litigation workflow covering litigation analysis, evidence mapping, legal research, and quality-gated pleading documents. Use when reviewing a litigation matter, organizing facts and evidence, checking current legal authority, drafting a complaint/defence/arbitration document, building an evidence catalogue, or preparing a source-traceable internal review package.
---

# Legal OS Litigation

Route a Chinese litigation matter through the private Legal OS workspaces in a fixed order. Keep the public skill generic and keep case facts, private evidence, internal strategy, and unverified legal propositions in the matter workspace only.

## Workflow

1. **Intake and role** — identify the procedural posture, party represented, requested outcome, deadlines, and the materials actually supplied. Do not invent missing facts.
2. **Litigation analysis** — build the issues, claims/defences, elements, disputed facts, procedural risks, and decision points. Separate facts from hypotheses and strategy.
3. **Evidence mapping** — map each material fact or proposition to an evidence item, source location, authentication/availability note, and gap status. Mark contradictions and missing originals.
4. **Legal research** — verify current law and authority from the appropriate source. Record jurisdiction, effective status, article/paragraph, source URL or document identifier, and the proposition supported. Do not use a remembered rule as a citation.
5. **Paired pleading assembly** — use `legal-os-template-runtime` to resolve and hash-check the exact pleading template and its paired evidence-catalog template. For every complaint, application or answer, create both artifacts in the same drafting run. Preserve the fixed visual shell, but expand facts, claims/defences, legal grounds, calculations and subsections to the depth required by the matter. Keep evidence names, numbers, page ranges and proof purposes in the separate evidence catalogue, not in a standalone pleading section. Keep internal analysis out of the external version.
6. **Quality gate** — check fact–evidence–authority–relief/defence alignment, party identity, jurisdiction, amount, dates, case number, procedural posture, numbering, A4 layout, page numbers, evidence-table headers, cross-artifact numbering and template fidelity.
7. **Release boundary** — label outputs as draft, internal review, or final clean version. Filing, service, sending, signing, or other external action requires separate user authorization.

## Stop conditions

Stop and surface a review item when any material party identity, amount, date, case number, forum, legal relationship, requested relief, or core evidence is missing or contradictory. Stop when a legal proposition cannot be tied to a current verified source. Never fill a gap with a template, old memory, or inference.

## Document controls

- Support civil complaints and answers, commercial arbitration applications and answers, labour/personnel arbitration applications and answers, and evidence catalogues.
- Classify `procedure_type`, `pleading_role` and `document_variant` before resolving a template. Do not use the commercial-arbitration template for a labour/personnel arbitration matter.
- Every complaint, application or answer has `paired_evidence_catalog_required=true`. Generate the independent evidence catalogue even when evidence is incomplete; label it `待补证 / 内部草稿` rather than omitting it.
- Do not create an independent “证据和证据来源” or equivalent evidence-source chapter inside a complaint, application or answer. Court, tribunal or institution evidence requirements are satisfied through the paired evidence catalogue and evidence materials.
- Labour/personnel arbitration templates must not request arbitration costs from the opposing party. Article 53 of the PRC Labour Dispute Mediation and Arbitration Law states that labour-dispute arbitration is free of charge.
- Treat template sections as minimum functions, not a content ceiling. Never compress a complex pleading into sample placeholder prose merely to preserve the original paragraph count.
- Stop with `TEMPLATE_REQUIRED` if `legal-os-template-runtime` cannot select exactly one approved template; do not design a replacement from a blank document.
- Preserve traceability from each material statement to supplied material and, for legal propositions, to verified authority.
- Keep internal strategy and risk ratings in the internal package; remove them from any external-facing document.
- Use minimal, granular edits when editing an existing document; preserve wording unless the material is unsupported or a necessary protection is missing.
- Run structured DOCX and accessibility checks, then inspect through the operating system's native preview. Use WPS or another approved native application only for targeted Chinese-font, pagination, table or print-layout concerns, and record material findings. Do not substitute another renderer without explicit user authorization.

## References

- For the module contract and artifact boundaries, read `references/workspace-contract.md`.
- For the reusable R1–R12 complaint/application/answer method, read `references/pleading-drafting-rules.md`.
- For the pleading quality gate and release labels, read `references/pleading-quality-gate.md`.
- For the verified legal basis of the labour-arbitration cost exclusion, read `references/labor-arbitration-authority.md`.
