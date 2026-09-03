# Official source registry

The registry identifies public official entry points and supported authority categories. It is metadata for routing and validation, not a mirror of external content.

| ID | Official entry point | Main scope | Access note |
|---|---|---|---|
| `npc-law` | <https://flk.npc.gov.cn/> | Laws, administrative regulations, local regulations and related normative texts | The adapter validates the official host and uses the site's public search/detail/download interfaces when available. |
| `gov-rules` | <https://www.gov.cn/zhengce/xxgk/gjgzk/> | State and department rule information | Search/detail pages may change; preserve the returned official URL and access date. |
| `mfa-treaty` | <https://treaty.mfa.gov.cn/> | Treaty identity, parties, entry into force and public text links | Treaty status requires separate signature, approval/accession and effective-date review. |
| `state-council-policy` | <https://sousuo.www.gov.cn/> | State Council and department policy documents | A policy document is not automatically a law, regulation or rule. |
| `moj-regulations` | <https://xzfg.moj.gov.cn/> | Administrative-regulation public information | The official page must identify status and dates before a deterministic conclusion. |
| `party-rules` | <https://www.12371.cn/special/dnfg/> | Publicly available Party rules | Keep this category distinct from laws, regulations and judicial interpretations. |
| `mod-regulations` | <https://www.mod.gov.cn/gfbw/fgwx/> | Public national-defence regulations and documents | Only the public official pages are accessed; no restricted material is collected. |
| `tax-rules` | <https://fgk.chinatax.gov.cn/> | Tax laws, regulations, rules and fiscal/tax documents | The source may expose category-specific search parameters. |
| `mee-regulations` | <https://www.mee.gov.cn/ywgz/fgbz/> | Ecological-environment regulations, rules and enforcement interpretations | The source may use category indexes rather than a stable search API. |
| `spc-publications` | <https://www.court.gov.cn/fabu/> | Supreme People's Court interpretations, documents and public releases | This is a publication source, not a complete case database. |

## Source validation

All registered URLs use HTTPS. `scripts/source_registry.py` rejects an unregistered host, an insecure scheme, and an authority type not listed for the selected source. A URL that redirects outside the registered host set is rejected by the client.

The source registry does not establish that the underlying official content is freely redistributable. Do not put downloaded responses, official documents, or source caches into this repository.
