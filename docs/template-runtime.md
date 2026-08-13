# Template runtime

`legal-os-template-runtime` is the cross-cutting template selector and DOCX fidelity gate for formal Legal OS artifacts.

## Fixed shell, flexible body

An approved template controls the document shell: page geometry, headers and footers, logos or seals, default East Asian fonts, paragraph and table styles, numbering conventions, signature blocks, and the minimum section skeleton. It is not a content ceiling.

The primary legal workflow remains responsible for expanding the body according to the current materials. For example, a payment notice may need separate treatment of the contract basis, performance and acceptance, invoices and payments, the overdue balance and calculation basis, a concrete deadline and method, default consequences, preservation of remedies, limitation or evidence risks, and a proportionate escalation path. Unsupported facts or legal threats must not be invented merely to make the document longer.

## Resolution order

The resolver selects one asset deterministically:

1. an explicitly approved template supplied for the task;
2. an approved private organization-specific overlay;
3. the approved public generic template.

Higher priority wins within the same document type and scope. Equal-priority matches are ambiguous and stop. A missing template returns `TEMPLATE_REQUIRED`; a hash mismatch returns `TEMPLATE_INTEGRITY_FAIL`. Formal output must not silently fall back to a newly designed blank document.

For a complaint, application or answer, resolution is bundled: the result includes the selected pleading template and the paired evidence-catalog template, with both IDs, paths and SHA-256 values. Failure to resolve or integrity-check either asset blocks formal DOCX generation.

## Verification

The bundled audit checks structural fidelity without comparing body length or requiring literal sample wording. It checks section geometry, header/footer relationships, drawings, tables, required East Asian fonts, file integrity, and unresolved placeholders. Drafts may retain marked placeholders; final artifacts may not.

Use structured OOXML checks as the default gate. Native preview is not required for an ordinary legal DOCX. Perform one targeted inspection in an approved native Office application only when the user requests visual, font, layout or print QA; the deliverable is inherently visual; the file contains complex visual elements; or a concrete pagination/layout defect is identified.

## Public/private boundary

The public catalog contains generic, sanitized, hash-bound assets. Organization letterhead and other identity-bearing templates belong in a private catalog. A private overlay may outrank the public template, but it must be registered and auditable; it must never be copied into the public repository.
