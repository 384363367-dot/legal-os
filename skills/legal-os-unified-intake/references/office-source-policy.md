# Office Source-First Policy

This policy is authoritative for LegalOS legal DOCX and ordinary editable Excel workflows. Downstream workflows must not override it with a helper's default rendering rule.

## Default gate

- Set `visual_check_required=false` for legal DOCX and ordinary editable Excel. Prioritize source content, OOXML/package structure, tracked changes, comments, styles, numbering, tables, inherited run formatting, formulas and error scans.
- Do not call a generic document-rendering helper, a headless office converter, PDF/PNG conversion, page-by-page screenshots or other visual preview by default. Do not change formal fonts, rebuild a structurally valid source, or delay delivery for that reason.
- An explicit user instruction not to render is a hard stop; a downstream Skill or helper cannot override it.

## Targeted checks

Set `visual_check_required=true` only when the user explicitly requests PDF, final layout, print or font QA; the deliverable is inherently visual; the file contains complex visual elements; or a structural check identifies a concrete objective pagination/layout risk. After finalization, perform at most one targeted check of the affected pages or views, with one corrective retry only after identifying a concrete cause.

PPT and PDF tasks remain governed by their dedicated visual-deliverable workflows.

## Environment findings

When source structure and content pass, missing Chinese fonts, renderer, sandbox or native-preview failures are `ENVIRONMENT_LIMITATION`; they do not alone set Draft/Hold. Do not switch renderers repeatedly, change formal fonts or rebuild the source. Reserve Draft/Hold for a real source-content, source-structure, privacy or authorization blocker.

## Authority

The user's current instruction wins. This policy and the unified intake rule outrank downstream helper defaults. Runtime Skills load the policy from the shared source/projection rather than maintaining divergent copies.
