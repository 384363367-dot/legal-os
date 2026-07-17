# Native Office Quality Gate

Legal OS uses structured file inspection as the default Office-document quality path. Visual inspection must use the operating system's native preview or an approved native Office application; an unapproved headless office converter is not part of the default or fallback chain.

## Required order

1. Preserve the source and create a separately named derived file.
2. Run format-specific structural checks: package integrity, text presence, styles, fonts, tables, numbering, headers/footers, comments, revisions, formulas, metadata and accessibility as applicable.
3. On macOS, use Quick Look for a native first-pass preview.
4. Use WPS Office or another approved native application only as a targeted spot check when Chinese fonts, pagination, tables, tracked changes, images or print layout remain uncertain.
5. If native inspection is unavailable or fails, report the tool limitation and keep the output at Draft/Hold. Do not substitute a different office renderer without explicit user authorization.

## Release rule

Do not treat extracted text, package validity or a first-page thumbnail as proof that every page is visually correct. A formal external deliverable passes only when the risk-proportionate native-app inspection is complete and the reviewer records the inspected file hash, application/path used, pages or views checked, findings and authorization state.
