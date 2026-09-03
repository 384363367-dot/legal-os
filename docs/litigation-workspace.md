# Litigation Workspace

The Litigation Workspace separates intake/routing from merits, evidence and legal research.

## Initial runtime chain

1. Litigation Intake registers the request, represented party, procedural position, materials, permissions and urgency.
2. Case Context builds source-linked actor, document, event, issue and evidence-indicator records without filling gaps.
3. Procedure Routing selects one primary litigation workflow and triggers only necessary Evidence, Current-Law and Case-Research tasks.
4. Verified `cn-case-hub` outputs are converted into a decision-fork action matrix before drafting.
5. Intake/quality gates independently check identity, versions, source fidelity, permissions, urgency and routing.

## v0.7.0 research handoff

`cn-case-hub` supplies verified core cases, dual-axis grades and decision-fork variables. The T-05 default `cn-legal-research` adapter supplies current-law search, version/effect/time-applicability source material and article-level retrieval. `cn-law-hub` is a compatibility path for legacy metadata/query plans and authority records. `legal-os-litigation` maps those outputs to the matter's confirmed/disputed facts, evidence, gaps, opponent attacks and concrete litigation actions. High-relevance adverse cases must be distinguished or carried as risk.

## Hard boundaries

- Do not calculate a procedural deadline without source dates and verified current rules.
- Do not treat a party's legal characterisation as a system conclusion.
- Do not decide evidence authenticity, admissibility or weight at intake.
- Separate drafting authority from filing/sending/irreversible external action.
- Keep civil, labour, arbitration, administrative, criminal and enforcement indicators distinct until verified.
- Keep dynamic matter facts outside generic runtime rules; latest verified status is the current matter authority.
