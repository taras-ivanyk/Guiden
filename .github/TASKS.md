# Build Tasks — 4 n

## Data Foundation
- [x] Create repo, venv, install requirements.txt
- [x] Set up .env with OPENAI_API_KEY + Strava credentials
- [x] Implement src/strava.py (get_recent_activities, get_activity_detail)
- [x] Test: print my recent activities + one detailed activity with laps
- [x] Implement src/weather.py + test with real coordinates
- [x] Implement src/profile.py

## Agent Skills + Orchestration
- [x] Implement src/skills.py (analysis, weather, question, coaching skills)
- [x] Implement src/orchestrator.py (LangGraph, two-phase)
- [ ] Test orchestrator from a script with a real activity

## UI + Demo
- [x] Implement app.py (Streamlit)
- [ ] Test full flow locally
- [ ] Deploy to Streamlit Cloud → get public URL
- [ ] Record 2-min demo video (Loom) using my real workout

## Polish + Application
- [ ] Write README.md as a landing page (problem/solution/demo/vision/roadmap)
- [ ] Clean code, add docstrings, type hints
- [ ] Prepare answers for the application form
- [ ] Submit application