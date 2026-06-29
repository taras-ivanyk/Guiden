# Development Process

## Workflow
1. Pick a task.
2. Create branch from `dev`: `git checkout dev && git checkout -b feat/<name>`
3. Use the relevant agent prompt from `.github/prompts/`.
4. Commit using Conventional Commits.
5. Open PR into `dev`.
6. CI runs (lint + tests).
7. Merge to dev. Periodically merge dev -> main for releases.

## Agents (manual prompt personas)
- planner-agent → breaks big task into steps
- decision-agent → evaluates options, recommends one
- migration-agent → executes migrations step by step
- testing-agent → writes/fixes tests
- refactor-agent → restructures code safely
- docs-agent → writes documentation
