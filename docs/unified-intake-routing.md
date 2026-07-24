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

## Routing output contract

Before workflow content, return the complete routing header defined in [`routing-output-contract.schema.json`](../skills/legal-os-unified-intake/references/routing-output-contract.schema.json). The header is machine-readable and must include the execution mode, one primary route, unique auxiliary routes, risk and gap levels, status, decision-interview record, confirmed and missing facts, blocker codes, expected deliverable and next action. Do not omit keys; use an empty array, `null`, or an empty string when a value is not applicable.

Use stable route codes (`T-01` through `T-12`) and lowercase kebab-case blocker codes. `G3` takes status priority and returns `stopped`. An external-action request adds an authorization blocker but does not by itself raise R2 to R3. Do not infer a template, authority, privacy, or other blocker solely from the document category.

The [risk-question ladder](../skills/legal-os-unified-intake/references/risk-question-ladder.md) counts only unresolved user decisions. Requests for facts, files, or authority verification do not consume the decision budget.

For T-02, the single primary route is retained. The router records `procedure_type`, `pleading_role`, `document_variant` and `paired_evidence_catalog_required=true` so the litigation workflow can distinguish civil litigation, commercial arbitration and labour/personnel arbitration without creating competing primary routes. Complaints, applications and answers resolve together with an independent evidence-catalog template.

In the v0.4.0 public pre-release, evidence mapping is a phase in `legal-os-litigation`; `cn-case-hub` provides official-source case research, while legislation and current-law verification require an available authoritative research capability selected for the jurisdiction. These are declared boundaries. The machine-readable contract is [legalos.manifest.json](../legalos.manifest.json); see also [capability-matrix.md](capability-matrix.md).
