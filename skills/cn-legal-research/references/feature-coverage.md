# Public adaptation feature coverage

This matrix records the public reimplementation boundary. It is intentionally explicit about live-source assumptions because this repository's tests are offline.

| Feature | Public implementation | Offline evidence | Known limitation |
|---|---|---|---|
| Registered official-source routing | `source_registry.py` | Registry count, HTTPS and host/type tests | The official site can change its public paths. |
| National law database search | `download.py` + `research_runtime.py` | Payload construction and response normalization tests | Live API availability and fields must be checked in the permitted environment. |
| Detail/metadata lookup | `download.py`, `site_adapters.py` | JSON/HTML fixture parsing tests | Unstable official page fields are preserved as raw/unknown rather than inferred. |
| Preview and article lookup | `document_parser.py` + `download.py` | Synthetic DOCX/XML and article-number tests | A source may publish a non-DOCX or scanned file; OCR is not bundled. |
| Cross-law keyword search | `article_search.py` | Pagination, filtering and article matching tests | It depends on the selected source returning candidate laws and accessible official text. |
| Government-rule/policy/department sources | Source-specific thin adapters over the common client | URL construction and HTML parser tests | Some sources expose category pages instead of documented APIs; source-specific layout changes require maintenance. |
| Treaty collection/detail/preview links | `treaty_crawler.py` | Label/link extraction tests | Treaty legal status still needs human review of official fields. |
| Regional classification | `region_classifier.py` | Province/city/national synthetic cases | Classifier is a routing aid, not a legal classification authority. |
| Cache | `research_runtime.CacheStore` | Explicit temporary-directory cache test | No default cache directory; caller must explicitly opt in. |
| Rate limiting | `research_runtime.RateLimiter` | Deterministic configuration tests | The caller remains responsible for the source's current limits and access rules. |
| File download | `research_runtime.OfficialClient.download` | Destination-boundary and content-disposition tests | No data is bundled; caller must choose an output directory and review terms. |
| DOCX/XML parsing | `document_parser.py` | Standard-library XML fixture tests | No OCR, PDF conversion or third-party document parser. |
| CLI | Public NPC, article, region, authority-record, MCP and source-specific adapter entrypoints | `--help`, offline parser and mock-client tests | Live requests are not run in CI/local candidate validation. |
| Optional MCP-style interface | `mcp_server.py` JSON-RPC stdio server | Protocol/tool-list and no-network tests | It is intentionally SDK-free; integrations must validate their own host protocol expectations. |

## Rights and boundary result

The implementation is newly authored with Python standard-library primitives and does not copy source-specific crawler code. `NOTICE` records the external-source boundary. Official source content, downloaded documents and cache entries remain runtime outputs and are never part of the public candidate.
