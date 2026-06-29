# Roadmap — Guiden

## Recently Shipped ✓
- React + Vite + TypeScript frontend (replaced Streamlit)
- FastAPI backend with stateless JWT auth
- Strava OAuth 2.0 flow
- Earthy green design system (system-adaptive light/dark)
- Date range calendar for activity selection
- Two-phase analyze pipeline with answers modal
- Training plan split-screen layout
- One-command dev start (`./scripts/dev.sh`)

---

## Up Next

### UI & Experience
- [ ] Real-time skill streaming (Server-Sent Events) — show analysis tokens as they arrive
- [ ] Mobile layout (responsive breakpoints for phone use mid-ride)
- [ ] Workout calendar view — heatmap of rides over time
- [ ] Shareable read-only analysis links

### Training Intelligence
- [ ] CTL / ATL / TSB (Training Stress Balance) tracking over time
- [ ] HRV-based readiness score — gate hard sessions automatically
- [ ] Injury risk model (ramp rate, monotony, strain index)
- [ ] Segment analysis — KOM attempts, climb trends

### Data Sources
- [ ] Garmin Connect (HRV, sleep, Body Battery)
- [ ] Wahoo SYSTM / ELEMNT
- [ ] Apple Health / Google Fit (lightweight fallback)

### Multi-Sport
- [ ] Running (pace zones, cadence, ground contact)
- [ ] Triathlon composite load model
- [ ] Sport-aware prompt routing

### Auth & Multi-User
- [ ] Per-user profile persistence (PostgreSQL / Supabase)
- [ ] Session isolation and token budget per user
- [ ] Shared-link demo mode (read-only, no auth)

### Platform & DevOps
- [ ] Docker Compose for self-hosting
- [ ] Production deployment (Railway / Fly.io)
- [ ] Rate limiting for public deployment
- [ ] Structured logging to external sink
