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
4. ensure no private Frozen artifact or matter record was copied;
5. run tests and obtain a clean repository status;
6. publish only through an explicit user-authorized action.
