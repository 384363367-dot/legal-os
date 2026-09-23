# Public capability matrix

Legal OS v0.8.1 public prerelease contains fifteen installable Skills. T-routes describe capabilities; not every route is a separate Skill directory. `legalos.manifest.json` is the machine authority for this inventory.

| Route | Capability | Public implementation | Boundary |
|---|---|---|---|
| T-01 | Contract review and redline | `legal-os-contract` | Current-law questions may call T-05; external release requires separate authorization. |
| T-02 / T-04 | Pleadings, litigation analysis and strategy | `legal-os-litigation` | Filing, service and signing require separate authorization. v0.7.0 converts verified case-law forks into evidence and strategy actions. |
| T-03 | Evidence register and proof mapping | phase in `legal-os-litigation` | Does not determine authenticity, admissibility or weight. |
| T-05 | Current law and case research | `cn-legal-research` is the default current-law executor; `cn-case-hub` handles cases; `cn-law-hub` remains compatibility-only | Official/authoritative source verification required; access controls may not be bypassed; public package does not bundle downloaded data, credentials or third-party SDKs. |
| T-06 | Formal correspondence | `legal-os-correspondence` | Drafting does not authorize sending/service. |
| T-07 | Business communication | `legal-os-business-communication` | Formal notices route to T-06. |
| T-08 | Amount, payment, date and data verification | `legal-os-data-verification` | Arithmetic status is not a legal conclusion. |
| T-09 | File delivery and archive | `legal-os-file-delivery` | Substantive changes stay with primary legal workflow. |
| T-10 | Reports and presentations | `legal-os-reporting-presentation` | Artifact generation depends on available presentation tooling. |
| T-11 | Matter memory | `legal-os-matter-memory` | Memory is a lead, not current fact or authority. |
| T-12 | Correction and learning maintenance | `legal-os-learning-maintenance` | Net-new-only governance; no automatic global rule mutation. |

## Installable Skills

- `legal-os-unified-intake`
- `legal-os-contract`
- `legal-os-litigation`
- `legal-os-correspondence`
- `legal-os-business-communication`
- `legal-os-data-verification`
- `legal-os-file-delivery`
- `legal-os-reporting-presentation`
- `legal-os-matter-memory`
- `legal-os-template-runtime`
- `legal-quality-gate`
- `cn-case-hub`
- `cn-legal-research`
- `cn-law-hub`
- `legal-os-learning-maintenance`

## v0.8.0 compatibility note

T-01 through T-12 remain stable. `cn-case-hub` retains the v0.6 case-record fields while adding a dual-axis case matrix and decision-fork variables. T-05 current-law questions dispatch to bundled `cn-legal-research`, whose public adapter provides bounded search, detail, preview, article, download, cross-law search and source-specific official adapters. `cn-law-hub` remains available only for compatibility with public metadata, query plans and authority-record validation; it is not a second default. The public package still requires human legal judgment and separate authorization for external actions.
