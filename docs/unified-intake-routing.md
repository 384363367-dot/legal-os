# Unified Matter Intake and Routing

The unified intake layer is the public-safe entry point for the Legal OS workflow family. It identifies the task, role, risk, materials, output audience, and gaps before loading one primary workflow.

## Route families

- Contract review and redlines
- Litigation pleadings and strategy
- Evidence register and proof-purpose mapping
- Current-law and case research
- Formal correspondence and situation statements
- Business communication and leadership wording
- Amount, payment, deadline-node, and data verification
- File conversion, delivery and archive
- Reports and presentations
- Matter-memory and rule-review governance

## Safety boundary

The public copy contains only generic routing logic. It does not contain client names, contract titles, case facts, private paths, credentials, current legal conclusions, or external-action permissions. Core conflicts, missing support, unclear authorization, and unverified current law must stop or return a pending-verification state.

## Runtime rule

Load `Kernel + one primary workflow + necessary auxiliaries + the matching quality gate`. The router does not replace specialist legal workflows, evidence checks, current-law research, or human authorization for sending, filing, signing, settling, waiving, terminating, publishing, or pushing changes.

Use `route-only` to return classification and next action without execution. Use `route-and-run` only when one primary route is clear and all stop and authorization gates pass. Every outcome has exactly one primary route; secondary capabilities remain auxiliary.

For T-02, the single primary route is retained. The router records `procedure_type`, `pleading_role`, `document_variant` and `paired_evidence_catalog_required=true` so the litigation workflow can distinguish civil litigation, commercial arbitration and labour/personnel arbitration without creating competing primary routes. Complaints, applications and answers resolve together with an independent evidence-catalog template.

In the v0.2.0 public pre-release, evidence mapping is a phase in `legal-os-litigation`, while current-law verification requires an available authoritative research capability selected for the jurisdiction. These are declared boundaries, not missing bundled Skills. The machine-readable contract is [legalos.manifest.json](../legalos.manifest.json); see also [capability-matrix.md](capability-matrix.md).
