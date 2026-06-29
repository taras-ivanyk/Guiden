# IMPROVEMENTS.md — Fixes, Features & Refactor

> Follow conventions in `.github/copilot-instructions.md` and `SPEC.md`.
> Implement in PRIORITY ORDER. Fix CRITICAL BUGS first, then features.
> Test after each section.

---

## 🔴 CRITICAL BUG 1: Health Conditions Ignored

PROBLEM: User entered "Problems with heart" / "back pain and too big right
aorta" in injuries/contraindications, but the generated plans and analysis
do NOT account for it.

FIX:
- The user's `injuries` / `contraindications` / health notes MUST be injected
  into the context of EVERY skill (analysis, training plan, next session,
  race prep, coaching).
- Add explicit instruction in ALL prompts:
  "CRITICAL: The athlete reported these health conditions: {injuries}.
   You MUST adapt all recommendations for safety. If conditions are
   cardiovascular (e.g. heart problems), be conservative with high-intensity
   zones (Zone 4-5), recommend medical clearance, and prioritize safety over
   performance. Explicitly reference how the plan accounts for these conditions."
- If a serious condition is detected (keywords: heart, cardiac, aorta, chest
  pain), the output MUST include a prominent safety warning recommending the
  user consult a doctor/cardiologist before following the plan.
- Make this verifiable: the generated plan should visibly mention the
  adaptation (e.g. "Given your reported heart condition, intensity is capped...").

---

## 🔴 CRITICAL BUG 2: Date Filter Finds No Activities

PROBLEM: Filtering activities from 25.08.2025 to 25.09.2025 returns nothing,
even though activities exist in that period.

LIKELY CAUSES (investigate & fix all):
1. `get_recent_activities` only fetches the most recent N activities
   (TOP_K_ACTIVITIES) — older activities in the date range are never fetched.
   FIX: When a date range is given, query Strava with `before` and `after`
   epoch timestamp params:
   `GET /athlete/activities?after={start_epoch}&before={end_epoch}&per_page=200`
   Handle pagination (loop pages until empty) so ALL activities in range load.
2. Date comparison bug: Strava dates are ISO strings (e.g.
   "2025-08-25T07:30:00Z"). Ensure filtering converts both sides to
   comparable date objects, not string comparison.
3. Timezone: use `start_date_local` consistently.

ADD: a function `get_activities_in_range(start_date, end_date, sport="Ride")`
in `src/strava.py` that handles epoch conversion + pagination + sport filter.

ADD logging: log how many activities were fetched, the date range used, and
the epoch values sent to Strava (helps debug).

---

## 🟠 UI FIX 3: Top Navigation Alignment (Image 5)

PROBLEM: The "Cycling" tab and disabled "Running/Swimming — coming soon"
buttons are cut off / misaligned at the top, hidden behind Streamlit's header.

FIX:
- Use `st.set_page_config(layout="wide")` and add top padding/margin so the
  sport selector is fully visible below Streamlit's toolbar.
- Render the 3 sport options in a clean `st.columns(3)` row with proper
  spacing. "Cycling" active (highlighted), Running & Swimming visibly
  disabled with "coming soon" labels.
- Ensure nothing is clipped on standard laptop screen widths.

---

## 🟠 UI FIX 4: Race Type Options (Image 1)

CHANGE race type dropdown to ONLY these two cycling options:
- "Road race"
- "Time trial"
Remove "Long group race / gran fondo" etc. Keep it simple.

---

## 🟠 UI FIX 5: Current Fitness — Simpler Options (Image 2)

REPLACE the current fitness dropdown options with exactly these 4 plain-language choices:
- "Not training for a long time"
- "Training 3-4 times a week"
- "Training 5-6 times a week"
- "Competitive / racing regularly"
Map each to an internal experience level used by the prompts.

---

## 🟠 UI FIX 6: Analysis Output Too Verbose (Image 3)

PROBLEM: Workout analysis shows a huge wall of text (STRUCTURE / OBSERVATIONS
/ DEVIATIONS). Too much to read.

FIX:
- Show a SHORT summary by default: 3-5 concise bullet points (key takeaways).
- Add a "🔍 More details" button/expander that reveals the full detailed
  analysis (structure, all observations, deviations).
- Implement this by having `analysis_skill` return BOTH:
  - `summary`: list of 3-5 short bullets
  - `details`: the full text
- Render summary always, details inside `st.expander("More details")`.

---

## 🟠 UI FEATURE 7: Clickable Plan Days (Image 4)

PROBLEM: Training plan shows weeks but you can't drill into a single day.

FIX:
- Make each day in the plan clickable/expandable.
- On click (use `st.expander` per day, or a button per day), show MUCH more
  detail for that session: full warm-up, main set, intervals breakdown,
  cooldown, target power/HR zones, RPE, fueling note, and how it accounts for
  health conditions.
- Implement via a new skill `expand_session_skill(week, day, session, profile)`
  that takes the brief session and generates detailed instructions ON DEMAND
  (lazy — only when user clicks, to save tokens).
- Cache expanded sessions in `st.session_state` so re-clicking doesn't re-call
  the LLM.

---

## 🟢 NEW FEATURE 8: Training Calendar

ADD a calendar interface so the user can select WHICH dates and WHAT HOURS
they are available to train.

REQUIREMENTS:
- A simple weekly availability grid OR a date picker where user marks
  available days + preferred time slots (e.g. morning/afternoon/evening or
  specific hours).
- Feed this availability into the training plan / next session skills so the
  plan is scheduled on real available days/times.
- Store availability in `st.session_state`.
- Keep it functional and clean; a full drag-drop calendar is NOT required —
  a structured weekly availability form is enough for MVP.
- ROADMAP NOTE (put in README/UI tooltip, do NOT build): future versions
  will send notifications/reminders based on this calendar.

---

## 🟢 NEW FEATURE 9: Main / Landing Page

ADD a main page (home view) shown before the user picks a mode.

CONTENT:
- App title + tagline ("AI Cycling Coach — your data-driven personal coach").
- Short explanation of the 3 modes (Analyze Workout, Training Plan, Race Prep).
- A "Get started" flow that guides user to fill profile first.
- Clean, visually appealing (cards for each feature, icons).
- Prominent but tasteful disclaimer.

---

## ⚙️ ENGINEERING 10: Logging Everywhere

ADD comprehensive logging using Python's `logging` module (configurable level
via env `LOG_LEVEL=INFO`). Create `src/logging_config.py` with a setup function.

LOG (at minimum):
- Which skill/service was triggered and when.
- Which model was used for each LLM call.
- Token usage per LLM call: prompt_tokens, completion_tokens, total_tokens
  (read from the OpenAI response `.usage`).
- Estimated cost per call (tokens × per-token price; make prices configurable).
- Cumulative tokens + cost for the session.
- External API calls (Strava, Open-Meteo): endpoint, status, # results.
- Errors with clear messages (especially Strava 401 = expired token).

CREATE a small `src/llm.py` wrapper around OpenAI calls that:
- Centralizes all LLM calls (every skill uses it).
- Automatically logs model, tokens, cost.
- Reads model + temperature from env.
- Optionally displays a small token/cost counter in the Streamlit sidebar.

---

## ⚙️ ENGINEERING 11: Token Optimization & Limits

OPTIMIZE token usage:
- Trim/condense data sent to the LLM (don't dump full raw Strava JSON — send
  only the fields each skill needs).
- For analysis, summarize laps before sending if there are many.
- Add a configurable MAX_TOKENS per response (env `MAX_OUTPUT_TOKENS`).
- Add a configurable per-session token budget (env `SESSION_TOKEN_BUDGET`);
  if exceeded, warn the user and stop further LLM calls gracefully.
- Lazy-load expensive operations (e.g. detailed session expansion only on click).
- Log token savings / usage so impact is visible.

---

## ⚙️ ENGINEERING 12: Refactor Folder & File Structure

SPLIT large files. Target structure:

ai-cycling-coach/
├── app.py                       # thin entry: routing between pages
├── .env.example
├── README.md
├── requirements.txt
├── src/
│   ├── config.py                # loads all env vars + defaults
│   ├── logging_config.py        # logging setup
│   ├── llm.py                   # central OpenAI wrapper (logs tokens/cost)
│   ├── strava.py                # Strava API (incl. get_activities_in_range)
│   ├── weather.py               # Open-Meteo
│   ├── profile.py               # UserProfile model + disclaimer
│   ├── orchestrator.py          # routes to skill flows
│   └── skills/
│       ├── init.py
│       ├── base.py              # shared skill helpers / base prompt parts
│       ├── analysis.py          # workout analysis (summary + details)
│       ├── weather_skill.py
│       ├── questions.py         # clarifying questions
│       ├── coaching.py
│       ├── next_session.py
│       ├── training_plan.py
│       ├── expand_session.py    # on-demand day detail
│       └── race_prep.py
├── ui/
│   ├── home.py                  # main/landing page
│   ├── analyze.py               # analyze-workout page
│   ├── plan.py                  # training-plan page
│   ├── race.py                  # race-prep page
│   ├── calendar.py              # availability calendar component
│   └── components.py            # shared UI helpers (token counter, headers)
└── prompts/
└── prompts.py               # all *_PROMPT constants in one place

REFACTOR RULES:
- Each skill = its own small, single-purpose file.
- Each skill exposes a clear function with typed inputs/outputs.
- Make skills easy to configure (temperature, max_tokens, model) per-skill
  via config, falling back to global defaults.
- All prompts centralized in `prompts/prompts.py` for easy editing.
- `app.py` becomes thin: just page routing + session state init.

---

## 📄 ENGINEERING 13: README

ADD a README.md with these sections:
- Project title + one-line description + 🚴 (landing-page tone).
- The Problem / The Solution.
- Features (Analyze Workout, Training Plan, Race Prep, Calendar).
- Live Demo link (placeholder for Streamlit Cloud URL).
- Tech Stack.
- Setup & Run:
  - Prerequisites (Python 3.11+, OpenAI key, Strava API app).
  - How to get Strava credentials (client id/secret/token, note 6h expiry).
  - `python -m venv venv && source venv/bin/activate`
  - `pip install -r requirements.txt`
  - Copy `.env.example` to `.env` and fill values.
  - `streamlit run app.py`
- Configuration table (all .env params explained).
- Architecture diagram (the orchestrator → skills flow).
- Roadmap (multi-sport, notifications, mobile, integrations).
- Disclaimer.

---

## ✅ ACCEPTANCE CRITERIA
- [ ] Health conditions clearly influence ALL outputs + safety warning for heart issues
- [ ] Date-range activity filtering works (fetches ALL activities in range, paginated)
- [ ] Top sport navigation fully visible & aligned
- [ ] Race type = Road race / Time trial only
- [ ] Current fitness = 4 simple options
- [ ] Analysis shows short summary + "More details" expander
- [ ] Training plan days are clickable → detailed session view (lazy-loaded)
- [ ] Calendar availability captured & used in planning
- [ ] Main/landing page exists and looks clean
- [ ] Logging: skill triggered, model, tokens, cost, API calls, errors
- [ ] Token limits + session budget enforced & logged
- [ ] Codebase refactored into the new modular structure
- [ ] README with full setup instructions
- [ ] No hallucinated numbers; everything grounded

## BUILD ORDER
1. CRITICAL BUG 1 (health) + BUG 2 (date filter) — fix first
2. Engineering 10 (logging) + 11 (token limits) + central llm.py — foundation
3. Refactor structure (12) — do early so rest is clean
4. UI fixes 3-6
5. Features 7 (clickable days), 8 (calendar), 9 (main page)
6. README (13)