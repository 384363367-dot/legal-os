# Native Office Quality Gate

Legal OS treats the requested editable Office source as the formal deliverable. Structured source inspection is primary; rendering/visual inspection is auxiliary and conditional.

## Required order

1. Preserve the source and create a separately named derived file.
2. Run format-specific structural checks: package integrity, text, revisions, styles, fonts, tables, numbering, headers/footers, comments, formulas, metadata and accessibility as applicable.
3. Select a visual mode: `off` or `conditional`. A visual check is triggered only by explicit user request, an inherently visual deliverable, complex visual elements, or a concrete layout/pagination risk. Formal, external or directly usable DOCX status alone is not a trigger. An explicit user instruction not to render is controlling.
4. When a reliable native/approved visual capability exists and a trigger applies, inspect only the affected pages/views and at most one final pass after finalization.
5. A font/renderer/sandbox limitation does not by itself invalidate a structurally verified DOCX/XLSX. Record `ENVIRONMENT_LIMITATION`; reserve Draft/Hold for actual content, structure, privacy or authorization blockers.

This v0.7.0 wording preserves the v0.6.2 source-first default while making the hard stop and conditional trigger boundary explicit.
