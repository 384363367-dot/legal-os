---
name: legal-os-file-delivery
description: Source-locked Chinese legal file-delivery and archive workflow for converting, merging, splitting, printing, indexing, privacy-cleaning, hashing, packaging, and quality-checking Word, PDF, spreadsheet, image, and evidence files. Use when the user asks to convert or combine files, make a clean or submission package, organize evidence or attachments, build a version index, prepare an archive, or verify delivery formatting; route content changes, legal conclusions, amount checks, formal notices, and presentations to the corresponding Legal OS workflow.
---

# Legal OS File Delivery

Use T-09 for file form, version, packaging, privacy and traceability. Do not use it to silently rewrite legal content or replace the substantive quality gate of the primary workflow.

For legal DOCX and ordinary editable Excel, apply `legal-os-unified-intake/references/office-source-policy.md` before loading any conversion or preview helper; PDF and visual deliverables remain conditional.

## Intake and inventory

Read every in-scope file and record:

- source name, type, page/sheet count, size, date, version and source relationship;
- target output, order, naming convention, audience, internal/external boundary and permission;
- attachments, tracked changes, comments, signatures, images, tables, sensitive information and known gaps.

Do not ask the user to repeat information already present in the files.

## Workflow

1. Inventory and test that every source opens; record missing or damaged files.
2. Build source → derived → attachment → submission/archive relationships.
3. Choose the smallest action: convert, merge, split, print, clean metadata, redact a public copy, index or archive.
4. Preserve text, numbering, tables, headers/footers, page order, images, comments and tracked changes unless an authorized task explicitly changes them.
5. Mark file status: `SOURCE`, `WORKING`, `DERIVED`, `CLEAN`, `SUBMISSION`, or `ARCHIVED`.
6. For a legal DOCX, treat the DOCX itself as the formal delivery artifact. Content, OOXML/package structure, tracked changes and formatting preservation are the primary acceptance checks; PDF/PNG rendering and visual preview are not prerequisites. Trigger one targeted auxiliary visual check only when the user explicitly requests PDF, layout, print or font QA; the deliverable is inherently visual; the file contains complex visual elements; or there is a concrete pagination/layout defect. Use ordinary 120-second and complex 300-second timeouts, with one corrective retry only after identifying a concrete cause. If a renderer, sandbox or missing-font environment produces missing glyphs, boxes, blank pages, font substitution or abnormal wrapping while structural checks pass, record an environment limitation; do not set Draft/Hold solely for that, switch renderers repeatedly, change formal fonts or rebuild the source.
7. Generate a manifest with filenames, source relationships, processing notes, hashes when available, QC status and archive boundary.
8. When generating the standard delivery checklist or version index, use `legal-os-template-runtime` to resolve and hash-check the registered template. Preserve the table and version-control structure while adding rows as needed; stop with `TEMPLATE_REQUIRED` if no approved template resolves.

Use bundled structured document/PDF/spreadsheet helpers as technical auxiliaries, not as authority for legal content. A helper's default rendering instruction never overrides the user's approved native-office inspection policy.

## Route boundaries

- Content or clause changes → the relevant contract, litigation, evidence, correspondence or communication workflow.
- Amount, payment, date, formula or data conflicts → T-08 data verification.
- Formal submission or legal notice → the relevant formal workflow; T-09 only packages the approved content.
- Presentation or formal leadership report → T-10 reporting workflow.

## Hard stops

Pause when:

- source files, pages, attachments, versions or signatures conflict or are incomplete;
- accepting revisions, producing a clean copy, redacting, or removing comments could change legal meaning;
- the source file or an authorized conversion actually changes text, tables, pagination, images or tracked changes; renderer, sandbox or font-environment differences are recorded separately and do not alone block a structurally valid DOCX;
- privacy, confidentiality, public/private boundary or external submission permission is unclear;
- the user asks to delete or overwrite originals.

Preserve the original, create a new status-labelled file, and return focused questions or a clearly labelled pending package. Never silently choose a version or overwrite a source.

## Output contract

Report the primary route, auxiliary helpers, source inventory, version relation, processing action, file status, QC result, missing items, archive/public boundary and next action. Keep temporary paths, internal notes and AI/process traces out of a copyable external package.

## Public/private boundary

Keep this Skill generic. Never copy real client names, matter facts, source files, private paths, credentials, hashes tied to private files, or unverified legal conclusions into the Skill or a public repository.
