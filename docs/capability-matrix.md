# Public capability matrix

Legal OS v0.4.0 public pre-release contains twelve installable Skills. The T-routes describe capabilities; not every route is a separate Skill directory. `legalos.manifest.json` is the machine authority for this inventory and the table below is its human-readable projection.

| Route | Capability | Public implementation | Boundary |
|---|---|---|---|
| T-01 | Contract review and redline | `legal-os-contract` | Current-law research and organization release approval remain separate. |
| T-02 / T-04 | Pleadings, litigation analysis and strategy | `legal-os-litigation` | Filing, service and signing require separate authorization. |
| T-03 | Evidence register and proof mapping | Evidence-mapping phase in `legal-os-litigation`; see `docs/evidence-workspace.md` | It does not determine authenticity, admissibility or weight. |
| T-05 | Current law, regulation and case research | `cn-case-hub` for free official-source case research; an available authoritative current-law capability for legislation | Case research does not replace current-law verification; source login and CAPTCHA controls must not be bypassed. |
| T-06 | Formal correspondence | `legal-os-correspondence` | Drafting does not authorize sending or service. |
| T-07 | Business communication | `legal-os-business-communication` | Formal notices route to T-06. |
| T-08 | Amount, payment, date and data verification | `legal-os-data-verification` | Arithmetic status is not a legal conclusion. |
| T-09 | File delivery and archive | `legal-os-file-delivery` | Substantive changes remain with the primary legal workflow. |
| T-10 | Reports and presentations | `legal-os-reporting-presentation` | Use an installed presentation tool for artifact generation. |
| T-11 | Matter memory | `legal-os-matter-memory` | Memory is a lead, not current fact or authority. |
| T-12 | Correction and learning candidate | Classify with `legal-os-unified-intake`, then record a candidate through `legal-os-matter-memory` | The public package does not auto-modify global rules. |

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
- `legal-os-template-runtime` (cross-cutting auxiliary; explicit invocation only)
- `legal-quality-gate` (cross-cutting final review and release control; explicit invocation only)
- `cn-case-hub` (official-source Chinese case research; explicit invocation or router selection)

This matrix is the authority for the public package boundary. Bundled templates and their executable resolver are documented in `docs/template-runtime.md`; unbundled connectors must not be described as locally executable. Every named Legal OS Skill dependency must appear in the installable list; external dependencies must be described generically and identified as unbundled.
