# Legal OS

Legal OS is an open, modular workflow framework for reliable legal work with AI agents.

It is designed around:

- task routing and minimum-context loading;
- reusable Skills, rule packs and quality gates;
- source-locked factual and legal verification;
- contract, litigation, correspondence, data, file-delivery, reporting and matter-memory workspaces;
- validation and release checks for reviewable legal work products.

## Current public scope

This pre-release repository contains generic, reusable workflow material, including:

- public Legal OS Skills and their workflow references;
- workspace and routing documentation;
- contract redline quality-gate and metrics scripts;
- synthetic-safe test guidance;
- the public/private separation policy.

The public repository does not contain client files, matter facts, private prompts, user-specific preferences, confidential templates, credentials or signed-in service details.

## Quick start

Start with [`OPEN_SOURCE_BOUNDARY.md`](OPEN_SOURCE_BOUNDARY.md), then read [`docs/architecture.md`](docs/architecture.md) and the documentation for the Skill or workspace you want to use. Each module is intended to be reviewed and adapted to its own jurisdiction, evidence sources, permissions and quality requirements.

## Legal and safety notice

This repository provides workflow structures, prompts, scripts and validation guidance. It is not legal advice, does not replace professional judgment, and does not establish that any legal proposition is current or applicable to a particular matter. Verify current law, authority, facts, permissions and output quality before relying on or releasing work produced with these materials.

## Status

Pre-release (`v0.1.0` will be the first public release). Interfaces, module boundaries and repository layout may change before the first stable release.

## License

Unless a file or subdirectory states otherwise, this repository is licensed under the Apache License, Version 2.0. See [`LICENSE`](LICENSE). Third-party materials, if added later, remain subject to their own license and attribution requirements.
