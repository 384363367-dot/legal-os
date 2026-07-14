# Pleading and Evidence Document Workspace

This module provides a source-locked interface for producing blank or case-populated Chinese legal documents. It is designed to sit after litigation analysis, evidence mapping, and legal-research outputs.

## Supported document types

- Civil complaint
- Civil defence
- Arbitration application
- Arbitration defence
- Evidence catalogue

The repository may provide reusable blank templates and validation logic. It must not contain client names, case numbers, private evidence, internal legal strategy, or copied matter files.

## Required input contract

Every populated document should carry a traceable link to:

1. user-confirmed parties, dates, amounts, procedural posture, and requested relief;
2. evidence items supporting each material fact or disputed proposition; and
3. current, source-verified legal research used for legal propositions.

If a material value is missing, contradictory, or only inferred, the generator must stop or mark it for review. Templates and old memory are not substitutes for current source material.

## Quality gate

Before a document is treated as final, check:

- fact–evidence–authority–relief/defence alignment;
- party identity, jurisdiction, amount, date, case number, and procedural posture;
- headings, numbering, A4 layout, page numbers, and evidence-table headers;
- removal of internal-only strategy from any external version; and
- separate authorization for drafting, internal review, sending, filing, and signing.

The workspace supports drafting and internal review. Availability of a template does not authorize filing, service, signature, or any other external action.

## Release boundary

This public module is a generic workflow and template layer. Real-case files remain private and should be maintained in the private Legal OS workspace.
