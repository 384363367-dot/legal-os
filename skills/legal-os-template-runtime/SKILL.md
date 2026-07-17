---
name: legal-os-template-runtime
description: Deterministic LegalOS template discovery, priority resolution, SHA-256 integrity checking, and DOCX fixed-shell fidelity auditing. Use whenever a LegalOS workflow creates a pleading, evidence catalog, formal letter, business communication artifact, verification workbook, delivery index, report, presentation outline, intake form, or matter-memory document from an approved template; also use when the user supplies a template or an organization-specific private overlay may apply.
---

# LegalOS Template Runtime

Resolve and verify templates before generating a formal file. Keep substantive drafting in the selected primary workflow; this Skill controls template authority and fidelity only.

## Required workflow

1. Identify one exact `document_type` from the current primary route.
2. Read `references/template-selection-policy.md`.
3. Resolve the template with `scripts/template_runtime.py resolve`. Supply the private overlay catalog when the controlled workspace has one; supply `--explicit-template` when the user identifies a current-task template.
4. Require `status=SELECTED`. Stop on `TEMPLATE_REQUIRED`, `TEMPLATE_AMBIGUOUS` or `TEMPLATE_INTEGRITY_FAIL`; do not create a substitute layout from a blank document.
5. Copy the selected template to the matter workspace. Preserve the source and record the template ID, scope, path, SHA-256, selection reason and font profile.
6. Draft with a fixed shell and flexible body. Preserve visual identity and minimum functional sections while expanding factual, legal and risk content to the depth required by the actual matter.
7. Run the primary workflow's substantive quality gate.
8. Run `scripts/template_runtime.py audit-docx` for DOCX output. Allow placeholders only for an explicitly labelled internal draft.
9. Perform the platform-approved native visual check and record findings. Template fidelity does not authorize sending, filing, signing or publication.

## Commands

Resolve a bundled template:

```bash
python scripts/template_runtime.py resolve --document-type civil-complaint --skills-root /path/to/skills
```

Resolve a private organization overlay:

```bash
python scripts/template_runtime.py resolve --document-type payment-performance-notice --organization "Example Organization" --skills-root /path/to/skills --private-catalog /path/to/private-template-catalog.json
```

Audit a derived DOCX:

```bash
python scripts/template_runtime.py audit-docx --template /path/to/template.docx --output /path/to/output.docx
```

## Boundaries

- Treat the template as a format and minimum-structure authority, not a content ceiling.
- Do not use template wording to fill missing facts, evidence or law.
- Do not preserve placeholder brevity when the matter requires fuller chronology, claims, defences, consequences, risk warnings, calculations or attachments.
- Do not state discretionary remedies or possible costs as certain outcomes.
- Keep private templates and organization identifiers outside the public package. A private catalog is an overlay, not a public asset.
- Follow the active native-office inspection policy; do not revive a retired renderer path.

## Resources

- `references/template-catalog.json` is the hash-bound public generic catalog.
- `references/template-selection-policy.md` defines authority order and fixed-shell/flexible-body drafting.
- `scripts/template_runtime.py` resolves templates and audits DOCX fidelity using the Python standard library.
