# Legal OS File Delivery and Archive Workspace

This is a generic, source-locked workflow for preparing document deliverables and archives. It does not make legal conclusions and it does not replace the workflow responsible for substantive content.

## What it does

- Inventory every source file and record its type, page count, version, relationship, and intended output.
- Choose the requested operation: convert, merge, split, print, clean, index, package, or archive.
- Preserve semantic content, source originals, version relationships, and an auditable manifest.
- Use the statuses `SOURCE`, `WORKING`, `DERIVED`, `CLEAN`, `SUBMISSION`, and `ARCHIVED`.
- For a Word/DOCX deliverable, treat the DOCX itself as the formal deliverable. Prioritize OOXML/package structure, text, revisions, styles, numbering, tables and formatting preservation.
- Treat PDF, PNG and visual inspection as auxiliary. Trigger them only when the user explicitly requests a PDF, requests final layout or print checking, the document contains complex visual elements, or there is a concrete pagination/layout risk. After finalization, perform at most one final render; use ordinary 120-second and complex 300-second timeouts, with one corrective retry only after identifying a concrete cause.
- If a Chinese-font, renderer or sandbox failure occurs while structural checks pass, record an environment limitation and do not set Draft/Hold solely for it. Do not change formal fonts, switch renderers repeatedly, or rebuild Word; reserve Draft/Hold for real source-content, source-structure, privacy or authorization blockers.

## Routing boundaries

Requests that change legal or business substance route to the corresponding contract, litigation, evidence, correspondence, or communication workflow. Amounts and dates route to data verification. Formal submissions and reporting packages require the responsible primary workflow before file packaging.

## Hard stops

Pause when a source is missing or corrupt, version relationships conflict, tracked changes or clean-version status is unclear, conversion fidelity differs, privacy or public/private boundaries are unresolved, or the request would delete or overwrite an original. Sending, submitting, signing, publishing, or pushing to an external repository requires separate authorization.

A rendering or native-inspection failure alone is not a hard stop when the structural checks pass.

## Delivery standard

Every released package contains a version map, delivery checklist, manifest, quality-gate result, and archive record. Public repositories contain only generic, reusable material with no client identifiers, private paths, confidential content, or case-specific hashes.

The mandatory Office-file inspection order and hold conditions are defined in [native-office-quality-gate.md](native-office-quality-gate.md).
