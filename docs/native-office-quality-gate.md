# Native Office Quality Gate

Legal OS uses structured file inspection as the default Office-document quality path. Visual inspection must use the operating system's native preview or an approved native Office application; an unapproved headless office converter is not part of the default or fallback chain.

## Required order

1. Preserve the source and create a separately named derived file.
2. Run format-specific structural checks: package integrity, text presence, styles, fonts, tables, numbering, headers/footers, comments, revisions, formulas, metadata and accessibility as applicable.
3. Trigger visual inspection only when a structural check identifies an objective risk: changed tables or merged cells, pagination or section structure, headers/footers, images, fonts/numbering, or tracked-change/comment display boundaries.
4. When triggered, use Quick Look or WPS Office/another approved native application for a targeted spot check of the affected pages or views; do not perform full-page rendering when no trigger exists.
5. If a required native inspection is unavailable or fails, report the tool limitation and keep the output at Draft/Hold. Do not substitute a different office renderer without explicit user authorization.

## Release rule

Do not treat extracted text, package validity or a first-page thumbnail as proof that every page is visually correct. A formal external deliverable passes only when the risk-proportionate native-app inspection is complete and the reviewer records the inspected file hash, application/path used, pages or views checked, findings and authorization state.
