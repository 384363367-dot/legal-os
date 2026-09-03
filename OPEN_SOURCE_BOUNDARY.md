# Open-source boundary

## Public by default

- Generic workflows, schemas and interfaces
- Reusable skills and deterministic validation scripts
- Synthetic or fully anonymized fixtures
- General rule-pack structures and quality gates
- Public documentation and contribution tests

## Private by default

- Client, counterparty, employee or matter materials
- Real contracts, evidence, correspondence and case files
- Names, contact information, amounts, case numbers and project status
- User-specific preferences, memories and internal strategy
- Absolute local paths, credentials, tokens and signed-in service details
- Proprietary or third-party templates without redistribution permission
- Military, state-secret, commercially sensitive or privileged materials

## Publication gate

Before any commit or release intended for publication:

1. scan for personal data, secrets and absolute local paths;
2. confirm every example is synthetic or irreversibly anonymized;
3. review third-party licences and attribution requirements;
4. ensure no private or archival artifact or matter record was copied;
5. run tests and obtain a clean repository status;
6. publish only through the authorized maintainer and release workflow.

## v0.7.0 first-party research boundary

`cn-case-hub` and `cn-law-hub` are maintained inside Legal OS. They must not require another third-party Skill, MCP package, commercial database SDK, or copied crawler implementation in order to run. External official websites remain research data sources rather than bundled code dependencies. If access is blocked by login, CAPTCHA, maintenance, robots policy or another access control, record the limitation and stop; do not bypass the control.

### Change disclosure

This v0.7.0 section is an intentional expansion of the public repository boundary. It records a distribution and runtime-dependency rule; it does not claim ownership of legislation, cases, databases or official websites, and it does not authorize copying third-party crawler code or restricted content into the repository.

## v0.8.0 public current-law adaptation

The public `cn-legal-research` Skill is an independently authored, standard-library source adapter. It provides bounded runtime search, detail, article, preview and download handling for ten registered official-source families, plus deterministic authority-record validation and an optional SDK-free JSON-RPC interface. It does not bundle source data, caches, credentials, commercial database SDKs or private runtime files.

`cn-law-hub` remains a compatibility/transition Skill for public source metadata, query planning and authority-record calls from older integrations; it is not the T-05 current-law default.

The ten primary official-source entries are source metadata and research entry points, not a claim that Legal OS owns or redistributes the underlying legislation, cases, databases or government publications. The public package must open and verify an official source in the actual permitted environment before treating a proposition as `verified-source`.

The public adaptation is independent from any private runtime copy. Private names, absolute paths, internal governance records, matter materials and organization overlays remain outside the public repository. The acknowledgement in `README.md` is attribution of research experience only and does not imply code reuse, affiliation or endorsement. Official websites and their content remain subject to their own terms and access controls.
