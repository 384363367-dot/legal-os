# Unified Matter Intake and Routing

The unified intake layer is the public-safe entry point for the Legal OS workflow family. It identifies the task, role, risk, materials, output audience and gaps before loading one primary workflow.

## Runtime rule

Load `Kernel + one primary workflow + necessary auxiliaries + the matching quality gate`. Use `route-only` to return classification and next action without execution. Use `route-and-run` only when one primary route is clear and all stop and authorization gates pass. Every outcome has exactly one primary route; secondary capabilities remain auxiliary.

For legal DOCX and ordinary editable Excel, use the shared Office source policy: source structure/content/revisions/formulas are primary, while visual inspection is runtime-aware and conditional unless the user asks for it or a concrete layout risk exists.

## T-05 research dispatch in v0.7.0

- `current-law-research` → `cn-law-hub`;
- `case-research` → `cn-case-hub`.

When legal/case research is auxiliary to a contract or litigation matter, retain the substantive route as primary. Do not turn T-05 into a competing primary route merely because research is needed.

## T-12 learning maintenance

Reusable corrections and Legal OS maintenance route to `legal-os-learning-maintenance`. Ordinary matter work must not load maintenance rules merely because it produces an observation.

## Routing output contract

Return the complete routing header defined in [`routing-output-contract.schema.json`](../skills/legal-os-unified-intake/references/routing-output-contract.schema.json). Use stable route codes (`T-01` through `T-12`) and lowercase kebab-case blocker codes. `G3` has status priority and returns `stopped`. External sending, filing, signing, publishing and repository pushing require separate authorization.
