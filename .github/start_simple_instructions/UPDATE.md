# UPDATE.md — Feature Expansion & Improvements

> Implement these changes following the conventions in
> `.github/copilot-instructions.md` and the structure in `SPEC.md`.
> Build in the PHASE ORDER below. Do not skip ahead.
> Test each phase before moving to the next.

## Global Changes

### Single Sport Focus: CYCLING ONLY
- The MVP supports **cycling only**. Remove/ignore run & swim logic.
- All prompts, analysis, and plans should assume cycling context
  (power in watts, FTP, cadence, intervals, climbing, etc.).
- In the UI, show a sport selector with "Cycling" selected and
  "Running / Swimming — coming soon" shown as disabled options
  (for roadmap signaling, not functional).

### Configuration via `.env`
Create/extend `.env.example` with these tunable parameters:
Required
OPENAI_API_KEY=sk-...
STRAVA_CLIENT_ID=12345
STRAVA_CLIENT_SECRET=your_secret
STRAVA_ACCESS_TOKEN=your_token

Optional / tunable (with sensible defaults in code)
OPENAI_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.4
TOP_K_ACTIVITIES=10          # how many recent activities to fetch
DEFAULT_WEEKS_AHEAD=4        # default training plan length

- Read all of these via `python-dotenv` with `os.getenv(..., default)`.
- Never crash if optional vars are missing — always fall back to defaults.

---

## PHASE 1 — Improve Existing "Workout Analysis" Skill (BUILD FIRST)

Improve `src/skills.py` → `analysis_skill` and the related UI:

### Analysis filtering (UI side, in `app.py`)
- Add a date range picker (start date / end date) to filter activities.
- Add optional filters: min/max distance (km), min/max duration (min).
- Default: show last `TOP_K_ACTIVITIES` cycling activities, no filter.
- Filters are a "nice to have" — keep them simple, don't over-engineer.

### Light progress context (OPTIONAL — only if Phase 1+2 done early)
- When analyzing one workout, optionally pass a SHORT summary of the
  last 1-2 weeks of cycling activities (total hours, avg power, # of
  hard sessions) so the agent can comment on recent trend.
- Keep this as a simple aggregate dict — do NOT build complex analytics.
- If implementing, add a function `get_recent_summary(days=14)` in
  `src/strava.py` returning aggregate stats only.

### Keep existing behavior
- Weather grounding, clarifying questions, disclaimer — all stay.
- Coaching output must remain grounded in real data (no invented numbers).

---

## PHASE 2 — New Skill: Training Plan (THE HERO FEATURE)

Add to `src/skills.py` two related capabilities, orchestrated in
`src/orchestrator.py` as a new flow.

### 2A. Next-Session Recommendation
- Function: `next_session_skill(profile, recent_summary, plan_inputs)`
- Returns ONE concrete recommended next cycling session
  (type, duration, target power zones/intervals, rationale).
- Grounded in: recent training load + user's stated goal + available time.

### 2B. Multi-Week Training Plan
- Function: `training_plan_skill(profile, plan_inputs)`
- Generates a structured multi-week cycling plan (default
  `DEFAULT_WEEKS_AHEAD` weeks, user-configurable 1-12).
- Output structure (return as structured data, then render nicely):
  - Per week: focus/theme, total hours, key sessions, recovery days.
  - Per key session: type, duration, target intensity.
- Apply basic cycling training principles: progressive overload,
  recovery weeks (e.g. easier every 3-4th week), polarized intensity.
- MUST respect user's available training hours/days.
- MUST include disclaimer (not medical/professional coaching advice).

### Plan Inputs (collect in UI questionnaire)
Add a form in `app.py` for the training plan flow:
- Available training days/week + hours available per day
- Goal (free text, e.g. "improve FTP", "build endurance base")
- Current fitness/experience level
- Sleep hours (avg)
- Contraindications / injuries / health notes
- Plan length in weeks (default DEFAULT_WEEKS_AHEAD)

### Clarifying questions
- The plan skill should ask 1-3 clarifying questions if key info is
  missing (reuse the existing `question_skill` pattern).

---

## PHASE 3 — New Skill: Race Preparation (BUILD ONLY IF TIME REMAINS)

Add to `src/skills.py`:

### Race Prep Skill (intentionally LESS detailed than training plan)
- Function: `race_prep_skill(profile, race_inputs)`
- For a target cycling event, produce a HIGH-LEVEL day-by-day-ish plan
  toward race day. Less granular than the multi-week training plan —
  focus on phases (base → build → peak → taper) rather than every session.
- Supported cycling race types (user selects):
  - Long group race (e.g. 200km mountainous / flat)
  - Time trial (e.g. 10km road TT)
  - (Keep cycling-only; do not add run/swim races now.)

### Interactive deepening (key behavior)
- The plan starts high-level.
- The user can ask follow-up questions about any part
  (e.g. "expand week 3", "what should taper look like?").
- When the user asks, the agent EXPANDS that specific section with
  more detail — but keeps the rest high-level.
- Implement this as a chat-style follow-up: store the plan in session
  state, and on a follow-up question, re-prompt the LLM with the plan +
  question to produce an expanded section.

### Race Inputs (UI)
- Race type, race date, expected distance/elevation, current fitness,
  available weekly training time, goal (finish / compete / specific time).

---

## FRONTEND IMPROVEMENTS (Copilot has freedom here)

Significantly improve `app.py` (Streamlit) — make it functional AND clean/beautiful:

### Structure
- Use a clear navigation with 3 modes (e.g. `st.sidebar.radio` or tabs):
  1. **Analyze Workout** (Phase 1)
  2. **Training Plan** (Phase 2)
  3. **Race Prep** (Phase 3, show "beta" tag)
- Sidebar: persistent user profile (loaded once, reused across modes).

### Visual polish
- Use `st.set_page_config` with a title, icon (🚴), wide layout.
- Use `st.metric` for key numbers (avg power, distance, time, etc.).
- Use `st.columns` for clean layouts.
- Use `st.expander` for clarifying questions and detailed plan sections.
- Use `st.chat_message` / `st.chat_input` for the coaching conversation
  and race-prep follow-up questions.
- Show the DISCLAIMER clearly but unobtrusively (e.g. in a caption/info box).
- Add light custom CSS via `st.markdown(..., unsafe_allow_html=True)` for
  a polished look (clean cards, spacing) — keep it tasteful, not heavy.
- Show loading spinners (`st.spinner`) during LLM/API calls.

### State management
- Use `st.session_state` to persist: profile, selected activity,
  intermediate analysis, generated plans, and chat history.

---

## ORCHESTRATOR UPDATES (`src/orchestrator.py`)

- Keep the existing two-phase analysis flow.
- Add separate entry functions for each mode:
  - `run_workout_analysis(...)` (existing, phase 1)
  - `run_training_plan(...)` (phase 2)
  - `run_race_prep(...)` and `expand_race_section(...)` (phase 3)
- Each can use LangGraph or simple sequential skill calls — prioritize
  clarity and working code over architectural complexity.

---

## PROMPTS (add as module-level constants in skills.py)
- NEXT_SESSION_PROMPT
- TRAINING_PLAN_PROMPT (emphasize progressive overload, recovery weeks,
  respecting available time, cycling-specific zones)
- RACE_PREP_PROMPT (high-level phases: base/build/peak/taper)
- RACE_EXPAND_PROMPT (expand one section in detail on user request)
All prompts must: stay cycling-specific, stay grounded, include safety
disclaimer, and avoid inventing data the user didn't provide.

---

## ACCEPTANCE CRITERIA (updated)
- [ ] App is cycling-only, clean and visually polished
- [ ] Workout analysis works with date/distance/time filters
- [ ] Training Plan: generates valid multi-week cycling plan respecting user time
- [ ] Next-session recommendation works
- [ ] (If time) Race Prep generates high-level plan + supports follow-up expansion
- [ ] (Optional) Light recent-weeks progress context in analysis
- [ ] All tunable params read from .env with safe defaults
- [ ] Disclaimer always shown
- [ ] No invented/hallucinated numbers — everything grounded in real data
- [ ] Runs end-to-end locally and deploys to Streamlit Cloud

## BUILD ORDER REMINDER
1. Phase 1 (improve analysis + filters + UI shell) → test
2. Phase 2 (training plan — THE HERO) → test
3. Frontend polish pass
4. Phase 3 (race prep) ONLY if time remains
5. Optional progress context LAST