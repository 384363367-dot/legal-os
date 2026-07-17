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
Approved template resolution (when the artifact is templated)
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
- For templated artifacts, bind the approved template before drafting. Keep the shell fixed and the substantive body expandable to the matter.
- Treat `legalos.manifest.json` as the public machine authority for version, profiles, Skills, routes, invocation policy and gates.
