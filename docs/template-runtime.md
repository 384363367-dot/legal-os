# Template runtime

`legal-os-template-runtime` is the cross-cutting template selector and DOCX fidelity gate for formal Legal OS artifacts.

An approved template controls the fixed shell (page geometry, headers/footers, fonts, styles, numbering, signature blocks and minimum section skeleton) but is not a content ceiling.

Resolution order: explicit approved user template → approved private organization overlay → approved public generic template. Missing template returns `TEMPLATE_REQUIRED`; hash mismatch returns `TEMPLATE_INTEGRITY_FAIL`; ambiguous equal-priority matches stop. Complaints/applications/answers resolve together with the paired evidence-catalog template.

v0.7.0 restores all **24** public generic template registrations and SHA-256 bindings, including `memory-update-candidate-diff`.

Structured OOXML checks are primary. Visual inspection is auxiliary and runtime-aware under the shared Office policy.
