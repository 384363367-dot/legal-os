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

Higher priority wins within the same document type and scope. Equal-priority matches are ambiguous and stop. A missing template returns `TEMPLATE_REQUIRED`; a hash mismatch returns `TEMPLATE_HASH_MISMATCH`. Formal output must not silently fall back to a newly designed blank document.

## Verification

The bundled audit checks structural fidelity without comparing body length or requiring literal sample wording. It checks section geometry, header/footer relationships, drawings, tables, required East Asian fonts, file integrity, and unresolved placeholders. Drafts may retain marked placeholders; final artifacts may not.

Use structured OOXML checks first, then native macOS Quick Look for visual inspection. A targeted inspection in an approved native Office application may be used when Chinese font substitution, pagination, tables, tracked changes, or print layout remain uncertain.

## Public/private boundary

The public catalog contains generic, sanitized, hash-bound assets. Organization letterhead and other identity-bearing templates belong in a private catalog. A private overlay may outrank the public template, but it must be registered and auditable; it must never be copied into the public repository.
