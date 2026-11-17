# Template selection and drafting policy

## Authority order

Resolve one template in this order:

1. A template explicitly identified by the user for the current task.
2. An approved private overlay matching the organization and document type.
3. The bundled generic template matching the document type.
4. If none or more than one equally specific template remains, return `TEMPLATE_REQUIRED` and stop document generation.

Verify the selected file against its registered SHA-256 before use. Copy it to the matter workspace and preserve the source as read-only. Record the template ID, scope, source, hash, selection reason and output hash in the matter manifest.

For a complaint, application or answer, resolve the requested template alone by default. When the user requests a catalogue or verified procedure requires it, pass `--with-evidence-catalog` to resolve and integrity-check that template too. An absent, ambiguous or corrupt catalogue blocks the requested combined selection. Legacy `paired_document_type` metadata does not require catalogue generation. Public litigation entries with an explicit status and any entry with an explicit approval_state must be approved. Legacy non-litigation status handling remains compatible with existing callers, without granting approval or expanding this change to their workflows. Private entries require explicit approval. Every registered selected file must match its valid registered SHA-256.

## Fixed shell, flexible body

The template controls visual identity, minimum functional sections and placement of formal elements. Preserve page geometry, orientation, styles, heading hierarchy, letterhead, headers/footers, drawings, tables, signature blocks and imprint lines unless the selected template expressly permits a variant.

The template does not cap legal or factual analysis. Expand, split or add body paragraphs, numbered subparts, issue headings, calculations and attachments when the actual matter requires them. A sample sentence is not a maximum content rule. Do not compress a complex demand, pleading or response into placeholder prose merely to keep the original paragraph count.

Expansion remains source-locked:

- add only facts supported by current matter material;
- verify current law before citing it;
- distinguish contractual remedies, legally supported consequences, discretionary relief and unresolved risk;
- do not turn possible fees, preservation measures, enforcement consequences or litigation outcomes into certain threats;
- keep internal strategy out of an external version.

## Fidelity gate

Before release, compare template and output for:

- section geometry and orientation;
- required East Asian fonts, sizes and heading hierarchy;
- headers, footers, letterhead, drawings and signature/imprint areas;
- required tables and table headers;
- unresolved placeholders or template-control notes;
- source-file findings for text, tables, numbering, headers/footers, tracked changes, comments, styles, font and paragraph properties, and preservation of unchanged content.

Structural fidelity and substantive quality are separate gates. Passing one never substitutes for the other.

For pleading bundles, apply the litigation workflow’s evidence-source chapter rule and check consistency among the actual requested artifacts. An incomplete requested catalogue remains `待补证 / 内部草稿`. Keep the internal evidence index regardless of delivery scope. A catalogue outside the requested or procedurally required scope is not a missing artifact.
