# Native Office Quality Gate

Legal OS treats the requested DOCX source as the formal Office deliverable. Source correctness and structured file inspection are the default quality path; for DOCX, OOXML/package structure, text, revisions, styles, numbering, tables and formatting preservation take priority. PDF, PNG and visual inspection are auxiliary and must use the operating system's native preview or an approved native Office application when triggered. An unapproved headless office converter is not part of the default or fallback chain.

## Required order

1. Preserve the source and create a separately named derived file.
2. Run format-specific structural checks: package integrity, text presence, styles, fonts, tables, numbering, headers/footers, comments, revisions, formulas, metadata and accessibility as applicable.
3. Trigger auxiliary PDF/PNG rendering or visual inspection only when the user explicitly requests a PDF, requests final layout or print checking, the document contains complex visual elements, or a structural check identifies a concrete objective pagination/layout risk such as changed tables or merged cells, section structure, headers/footers, images, fonts/numbering, or tracked-change/comment display boundaries.
4. When triggered, use Quick Look or WPS Office/another approved native application for a targeted spot check of the affected pages or views. After finalization, perform at most one final render. Use ordinary 120-second and complex 300-second timeouts, with one corrective retry only after identifying a concrete cause; do not render repeatedly when no trigger exists.
5. If Chinese-font, renderer, sandbox or native-inspection failure occurs while structural checks pass, report `ENVIRONMENT_LIMITATION` and do not set Draft/Hold solely for that reason. Reserve Draft/Hold for a real source-content, source-structure, privacy or authorization blocker. Do not change formal fonts, rebuild Word, or substitute renderers repeatedly; explicit user authorization is required for any renderer substitution.

## Release rule

Do not treat extracted text, package validity or a first-page thumbnail as proof that every page is visually correct. A formal external DOCX deliverable passes the source/structural, content, privacy and authorization gates. When a visual trigger applies, the reviewer records the inspected file hash, application/path used, pages or views checked, findings and authorization state; an environment-limited render or native inspection is not a standalone reason to withhold a structurally verified DOCX.
