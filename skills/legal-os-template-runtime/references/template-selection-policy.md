# Template selection and drafting policy

## Authority order

Resolve one template in this order:

1. A template explicitly identified by the user for the current task.
2. An approved private overlay matching the organization and document type.
3. The bundled generic template matching the document type.
4. If none or more than one equally specific template remains, return `TEMPLATE_REQUIRED` and stop document generation.

Verify the selected file against its registered SHA-256 before use. Copy it to the matter workspace and preserve the source as read-only. Record the template ID, scope, source, hash, selection reason and output hash in the matter manifest.

For any complaint, application or answer, the selected catalog entry must declare `paired_document_type=evidence-catalog`. The resolver must return and integrity-check both templates. Absence, ambiguity or hash failure of the paired template blocks the pleading output.

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
- native preview findings for overlap, clipping, pagination and print layout.

Structural fidelity and substantive quality are separate gates. Passing one never substitutes for the other.

For pleading bundles, fidelity also requires that the pleading omit any independent evidence-source chapter and that the evidence catalogue be generated in the same run. Incomplete evidence is represented as a `待补证 / 内部草稿` catalogue, not as a missing artifact.
