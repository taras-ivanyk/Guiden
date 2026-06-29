# Roadmap — AI Cycling Coach

## Data Sources
- [ ] **Garmin Connect** integration (native training data, HRV, sleep, Body Battery)
- [ ] **Wahoo SYSTM / ELEMNT** integration (structured workout sync)
- [ ] **Runna** integration (run training plan import for multi-sport users)
- [ ] **Polar Flow** and **Suunto** API support
- [ ] **Apple Health / Google Fit** as lightweight fallback for non-device users

## Multi-Sport
- [ ] Running analysis (pace zones, cadence, ground contact time)
- [ ] Swimming (stroke rate, SWOLF, pool vs open water)
- [ ] Triathlon composite load model (TSS across disciplines)
- [ ] Sport-aware prompts and skill routing per activity type

## UI / Frontend
- [ ] Evaluate **Next.js + FastAPI** migration when user base warrants richer interactivity
- [ ] Mobile-optimised layout (responsive CSS breakpoints)
- [ ] Real-time agent step streaming (WebSocket / SSE) to replace `st.status` polling
- [ ] Dark mode support
- [ ] Workout heatmap / calendar history view

## Auth & Multi-User
- [ ] OAuth 2.0 user auth (Google / GitHub sign-in via Streamlit or FastAPI)
- [ ] Per-user profile persistence (PostgreSQL or Supabase)
- [ ] Session isolation and token budget per user account
- [ ] Shared-link demo mode (read-only, no auth required)

## Analytics & Intelligence
- [ ] Long-term fitness tracking: CTL / ATL / TSB (Training Stress Balance)
- [ ] Segment analysis (KOM attempts, climb performance trends over time)
- [ ] HRV-based readiness score — gate hard sessions automatically
- [ ] Injury risk model (ramp rate, monotony, strain index)
- [ ] Nutrition / fueling log integration

## Platform & DevOps
- [ ] Streamlit Cloud deployment (public demo URL)
- [ ] Docker Compose for self-hosting
- [ ] GitHub Actions CI: lint, type-check, unit tests on every push
- [ ] Rate limiting and abuse prevention for public deployment
- [ ] Structured logging to external sink (Datadog / Grafana Cloud)
