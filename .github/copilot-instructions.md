# Copilot Instructions

## Project
AI cycling coach (currently Streamlit, migrating to React).

## Branch Strategy
- main = production, protected, no direct commits
- dev = integration branch
- Feature branches from dev:
  - feat/<short-name>
  - fix/<short-name>
  - docs/<short-name>
  - refactor/<short-name>
  - migrate/<short-name>

## Commit Convention (Conventional Commits)
- feat: ...
- fix: ...
- docs: ...
- refactor: ...
- test: ...
- chore: ...

## PR Rules
- Always target dev (not main) unless it's a release.
- Keep PRs small and focused.
- Include: summary, changes, testing notes.

## Code Rules
- Write clear, typed, documented code.
- Add tests for new logic.
- Never commit secrets, .env, venv, __pycache__, node_modules.

## When asked to act as an "agent"
Follow the matching prompt file in .github/prompts/.
