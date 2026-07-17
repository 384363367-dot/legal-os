# Architecture

```text
User request and materials
        ↓
Public Kernel manifest
        ↓
Unified Intake (`route-only` or `route-and-run`)
        ↓
One primary workspace
        ↓
Necessary rule packs, plugins and source checks
        ↓
Independent quality gates
        ↓
Requested deliverable
        ↓
Learning observation and controlled upgrade
```

## Design principles

- Load only what the current task requires.
- Keep facts, knowledge, experience, rules and quality controls separate.
- Treat user materials and verified sources as evidence; do not fill gaps silently.
- Preserve one current authority for each scope and keep version history.
- Detect issues automatically, but govern changes to authoritative rules.
- Keep the public runtime generic; place organization-specific behaviour in private configuration.
- Treat `legalos.manifest.json` as the public machine authority for version, profiles, Skills, routes, invocation policy and gates.
