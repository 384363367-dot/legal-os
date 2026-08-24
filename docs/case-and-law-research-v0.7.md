# v0.7.0 Case and Current-Law Research Architecture

## Why the change

The prior public repository had a first-party case Skill but treated current-law retrieval as an external capability. A later local runtime contained a third-party law-research Skill/crawler package. v0.7.0 resolves both issues without creating a duplicate all-in-one research Skill.

## First-party split

- `cn-case-hub`: cases, program chains, dual-axis relevance/direction, decision-fork variables.
- `cn-law-hub`: authority identity, effect, version history, article/pinpoint and temporal application.
- `legal-os-litigation`: consumes verified outputs and converts them into matter evidence/argument/procedural actions.

## New and existing matters

New matters start with confirmed vs unverified facts and the legal question. Existing matters additionally lock the latest procedural status, judgments, evidence and opponent position. Latest verified status is current authority; earlier statuses remain history.

## Case matrix

Relevance `A/B/C/D` is independent from direction `+/±/0/-`. `A-` means highly relevant and adverse and is therefore especially important. The older v0.6 `similarity` and `direction` fields remain readable for compatibility.

## Decision-fork variables

A useful research result identifies why outcomes diverge: authorization, party qualification, contract wording, performance facts, burden of proof, evidence strength, timing, procedure or legal version. Those variables are mapped against the current matter and become evidence or argument actions.

## Statistical discipline

Search results are not a random population. Any count is labelled `检索样本支持比例`; it is not a success probability and not a `胜诉率`.

## Dependency boundary

Neither research Skill requires a third-party Skill, MCP, commercial database SDK or bundled copied crawler. Official/professional databases may be used as actual data sources when available, but access controls may not be bypassed and the final record must remain traceable to verified authority.
