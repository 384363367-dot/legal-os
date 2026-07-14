# Litigation Workspace

The Litigation Workspace separates intake and routing from merits, evidence and legal research.

## Initial runtime chain

1. Litigation Intake registers the request, represented client, procedural-position candidate, materials, permissions and urgency indicators.
2. Case Context builds source-linked actor, document, event, issue and evidence-indicator records without filling gaps.
3. Procedure Routing selects one primary workflow and triggers only the necessary Evidence and Legal Research tasks.
4. Intake Quality Gate independently checks identity, versions, source fidelity, permissions, urgency and routing.

## Hard boundaries

- Do not calculate a procedural deadline without source dates and a verified current rule.
- Do not treat a party's legal characterisation as a system conclusion.
- Do not decide evidence authenticity, admissibility or weight at intake.
- Separate drafting authority from filing, sending and irreversible external action.
- Keep civil, labour, arbitration, administrative, criminal and enforcement indicators distinct until verified.
- Keep dynamic matter facts outside generic runtime rules.
