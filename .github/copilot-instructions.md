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

## Prompting Principles (always active)
These rules apply whenever you create or modify any LLM prompt or LLM-based feature in this project.
For deep prompt-engineering work, load `.github/prompts/prompt-engineer-agent.md` for the full process.

- **Ask first.** Before writing any prompt, ask the minimum clarifying questions needed (goal, inputs, output format, constraints, parsing requirements).
- **Restate.** Translate the task into your own words and flag contradictions before proceeding.
- **Decompose.** One prompt = one clear goal. Map each step to a skill in `src/skills/`. Show the plan before writing.
- **Structure + example.** Use XML tags for parseable output. Provide 1–2 positive examples, not more.
- **Self-evaluate.** Embed this block in every important app prompt:
  > Before returning your answer, rate it 1–10 on accuracy, clarity, and rule compliance. If below 9 and you can do better, improve it first, then return the final version with `<self_score>`.
- **Generic fixes.** When something is wrong, ask the LLM to explain its reasoning, then fix the root cause — never patch a single case.
