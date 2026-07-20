# Pleading and Evidence Document Workspace

This module provides a source-locked interface for producing blank or case-populated Chinese legal documents. It is designed to sit after litigation analysis, evidence mapping, and legal-research outputs.

## Supported document types

- Civil complaint
- Civil defence
- Commercial arbitration application
- Commercial arbitration defence
- Labour/personnel arbitration application
- Labour/personnel arbitration defence
- Evidence catalogue

The repository may provide reusable blank templates and validation logic. It must not contain client names, case numbers, private evidence, internal legal strategy, or copied matter files.

## Required input contract

Every populated document should carry a traceable link to:

1. user-confirmed parties, dates, amounts, procedural posture, and requested relief;
2. evidence items supporting each material fact or disputed proposition; and
3. current, source-verified legal research used for legal propositions.

If a material value is missing, contradictory, or only inferred, the generator must stop or mark it for review. Templates and old memory are not substitutes for current source material.

## Paired-output contract

Every complaint, application or answer must be generated together with an independent evidence catalogue. The pair is one T-02 drafting output even though the evidence workspace remains a reusable litigation phase.

- The pleading contains facts, requests/defences and necessary legal reasoning, but no independent “证据和证据来源” chapter.
- The evidence catalogue contains evidence number, name, page range and proof purpose; those fields must align with the pleading's factual structure.
- Incomplete evidence does not cancel the paired output. Generate a `待补证 / 内部草稿` catalogue and keep the matter in draft or blocked status.
- Labour/personnel arbitration uses dedicated variants rather than commercial-arbitration templates. It must not include a request that the opposing party bear labour-arbitration costs.

## Quality gate

Before a document is treated as final, check:

- fact–evidence–authority–relief/defence alignment;
- party identity, jurisdiction, amount, date, case number, and procedural posture;
- headings, numbering, A4 layout, page numbers, and evidence-table headers;
- exact cross-artifact alignment between the pleading and evidence catalogue;
- absence of an independent evidence-source chapter in the pleading;
- removal of internal-only strategy from any external version; and
- separate authorization for drafting, internal review, sending, filing, and signing.

The workspace supports drafting and internal review. Availability of a template does not authorize filing, service, signature, or any other external action.

## Release boundary

This public module is a generic workflow and template layer. Real-case files remain private and should be maintained in the private Legal OS workspace.
