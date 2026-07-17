---
name: legal-os-correspondence
description: Source-locked Chinese formal-correspondence workflow for lawyer letters, payment or performance notices, reply letters, and situation statements. Use when drafting, reviewing, or quality-checking a formal external letter, demand, default notice, government/court explanation, or internal-to-external correspondence package that may affect payment, liability, rights, deadlines, litigation position, or company communications.
---

# Legal OS Correspondence

Route formal correspondence through a source-locked workflow. Keep the public Skill generic; keep case facts, private evidence, internal strategy, and sending records in the private matter workspace.

## Workflow

1. **Identify purpose and audience** — determine the sender, recipient, role, procedural or commercial context, purpose, desired response, deadline, delivery method, and whether the text is internal or external.
2. **Collect source material** — read the relevant contract, notices, correspondence, delivery/payment/acceptance records, evidence register, litigation analysis, and current legal research. Do not infer missing facts.
3. **Build the fact and deadline ledger** — record each material fact, amount, date, obligation, breach/status, deadline, calculation basis, and source location. Distinguish confirmed, user-stated, document-stated, inferred, and unresolved items.
4. **Choose the document type and template** — identify lawyer letter, payment/performance notice, reply letter, or situation statement. Use `legal-os-template-runtime` to resolve and hash-check one approved template. Stop with `TEMPLATE_REQUIRED` rather than inventing a layout.
5. **Draft the external text** — preserve the fixed visual shell, but expand the body to match the actual chronology, breach, demand, response options, contractual remedies, verified legal consequences, dispute route, costs, preservation measures and rights reservation. Include only necessary, supportable material; do not turn possible or discretionary consequences into certain threats.
6. **Run the quality gate** — verify facts, evidence, current law when cited, recipient and service information, deadline computation, attachments, expression boundaries, template fidelity, formatting, and authorization states.
7. **Release by authorization** — label draft, internal review, or external clean version. Drafting does not authorize sending, service, filing, signing, or contacting a counterparty.

## Stop conditions

Stop for review when sender, recipient, contract/project, amount, date, obligation, deadline, delivery method, legal relationship, or core evidence is missing or contradictory. Stop when the text may admit liability, waive a right, create a settlement/termination effect, or rely on unverified current law. Stop when external-action authorization is absent.

## Document controls

- Keep internal analysis, negotiation posture, escalation options, and risk ratings out of the external version.
- Map each material assertion and demand to supplied material; legal propositions must cite current verified authority when used.
- Treat deadline, delivery, attachment, and recipient details as substantive controls, not formatting details.
- Do not use a template or old memory to fill a factual or legal gap.
- Treat template wording as a minimum functional example, not a content ceiling. Add numbered subparts, risk warnings, calculations and attachments when the matter requires them.
- Run DOCX structural and accessibility audits, then inspect through the operating system's native preview. Use WPS or another approved native application only for targeted Chinese-font, pagination, table or print-layout concerns. Do not substitute another renderer without explicit user authorization.

## References

- Read `references/workspace-contract.md` for inputs, outputs, and boundary states.
- Read `references/correspondence-quality-gate.md` for the mandatory release checks.
