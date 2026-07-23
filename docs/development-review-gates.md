# Development and review gates

Legal OS uses explicit review gates so that routine engineering changes remain efficient while high-impact changes receive appropriate scrutiny.

## Changes requiring maintainer review

- material changes to architecture, scope, permissions, migration strategy or the public/private boundary;
- workflow behavior that could admit, waive, settle, release, terminate or otherwise affect legal rights;
- filing, signing, sending, publication, destructive overwrite or another external side effect;
- a major version, new Workspace family or release reaching its go/no-go decision;
- changes whose required evidence, current law, authority or licence cannot be verified;
- a failed mandatory quality gate or an unresolved Critical defect.

## Merge requirements

Each proposed release should identify its scope, verification results, unresolved limitations and rollback path. A release is eligible to merge only after required reviews and automated checks pass and no blocking defect remains open.
