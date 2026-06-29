import { useState } from 'react';
import { useAuth } from '../auth/AuthContext';
import ConnectStrava from '../components/ConnectStrava';
import LoadingSpinner from '../components/LoadingSpinner';
import AgentPipeline from '../components/AgentPipeline';
import DateRangePicker from '../components/DateRangePicker';
import QuestionsModal from '../components/QuestionsModal';
import { stravaApi } from '../api/strava';
import { analyzeApi } from '../api/analyze';
import type { ActivitySummary, AnalyzeStartResponse, UserProfile } from '../types/api';

type SS = 'pending' | 'running' | 'done' | 'error';
const STEPS0 = [
  { label: 'Analysis + Weather', status: 'pending' as SS },
  { label: 'Clarifying Questions', status: 'pending' as SS },
  { label: 'Coaching Feedback',   status: 'pending' as SS },
];

function loadProfile(): UserProfile {
  try {
    const r = sessionStorage.getItem('profile');
    return r ? JSON.parse(r) : { age: 30, ftp: 250, goal: 'General fitness', experience: 'Intermediate', injuries: 'None' };
  } catch { return { age: 30, ftp: 250, goal: 'General fitness', experience: 'Intermediate', injuries: 'None' }; }
}

function fmt(n?: number, unit = '') { return n != null ? `${Math.round(n)}${unit}` : null; }

export default function AnalyzePage() {
  const { isAuthenticated } = useAuth();
  const [dateRange, setDateRange] = useState<{ start: string; end: string } | null>(null);
  const [activities, setActivities] = useState<ActivitySummary[]>([]);
  const [selectedId, setSelectedId] = useState('');
  const [loadingActs, setLoadingActs] = useState(false);
  const [steps, setSteps] = useState(STEPS0);
  const [phase1, setPhase1] = useState<AnalyzeStartResponse | null>(null);
  const [coaching, setCoaching] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [refineLoading, setRefineLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function setStep(i: number, s: SS) {
    setSteps(prev => prev.map((x, j) => j === i ? { ...x, status: s } : x));
  }

  async function findRides() {
    if (!dateRange) return;
    setLoadingActs(true); setError(null); setActivities([]); setSelectedId('');
    setPhase1(null); setCoaching(null);
    try {
      const data = await stravaApi.getActivitiesRange(dateRange.start, dateRange.end);
      setActivities(data);
      if (!data.length) setError('No rides found in this date range.');
    } catch (e: unknown) { setError(e instanceof Error ? e.message : String(e)); }
    finally { setLoadingActs(false); }
  }

  async function runAnalysis() {
    if (!selectedId) return;
    const profile = loadProfile();
    setSteps(STEPS0); setPhase1(null); setCoaching(null);
    setAnalyzing(true); setError(null);
    try {
      setStep(0, 'running');
      const p1 = await analyzeApi.start({ activity_id: selectedId, profile });
      setPhase1(p1); setStep(0, 'done'); setStep(1, 'done');
      setStep(2, 'running');
      const p2 = await analyzeApi.coach({ activity_id: selectedId, profile, analysis: p1.analysis, weather: p1.weather, answers: {} });
      setCoaching(p2.coaching_output); setStep(2, 'done');
    } catch (e: unknown) {
      const ri = steps.findIndex(s => s.status === 'running');
      if (ri >= 0) setStep(ri, 'error');
      setError(e instanceof Error ? e.message : String(e));
    } finally { setAnalyzing(false); }
  }

  async function handleRefine(answers: Record<string, string>) {
    if (!phase1) return;
    setRefineLoading(true);
    try {
      const p2 = await analyzeApi.coach({
        activity_id: phase1.activity_id,
        profile: loadProfile(),
        analysis: phase1.analysis,
        weather: phase1.weather,
        answers,
      });
      setCoaching(p2.coaching_output);
      setModalOpen(false);
    } catch (e: unknown) { setError(e instanceof Error ? e.message : String(e)); }
    finally { setRefineLoading(false); }
  }

  if (!isAuthenticated) {
    return (
      <div className="page page--medium">
        <div>
          <h1>Analyze Workout</h1>
          <p style={{ color: 'var(--text-muted)', marginTop: '0.25rem' }}>Connect Strava to analyze your rides.</p>
        </div>
        <ConnectStrava />
      </div>
    );
  }

  return (
    <div className="page page--wide">
      <h1>Analyze Workout</h1>

      {/* ── Date Range ── */}
      <section className="section">
        <h2>Select Date Range</h2>
        <DateRangePicker onRangeChange={(s, e) => { setDateRange({ start: s, end: e }); setActivities([]); setPhase1(null); setCoaching(null); }} />
        {dateRange?.start && dateRange.end && (
          <button className="btn-primary" onClick={findRides} disabled={loadingActs} style={{ marginTop: '0.25rem' }}>
            {loadingActs ? 'Finding rides…' : `Find Rides →`}
          </button>
        )}
        {loadingActs && <LoadingSpinner label="Loading activities…" />}
      </section>

      {/* ── Activity list ── */}
      {activities.length > 0 && (
        <section className="section">
          <h2>{activities.length} ride{activities.length !== 1 ? 's' : ''} found</h2>
          <div className="activity-list">
            {activities.map(a => {
              const chips = [
                fmt(a.distance_km, ' km'),
                fmt(a.moving_time_min, ' min'),
                a.avg_watts ? fmt(a.avg_watts, 'W') : null,
                a.avg_hr ? fmt(a.avg_hr, ' bpm') : null,
              ].filter(Boolean);
              return (
                <button key={a.id}
                  className={`activity-card${selectedId === a.id ? ' activity-card--selected' : ''}`}
                  onClick={() => setSelectedId(a.id)}>
                  <span className="activity-card-date">{a.date}</span>
                  <span className="activity-card-name">{a.name}</span>
                  <span className="activity-card-meta">
                    {chips.map((c, i) => <span key={i} className="activity-meta-chip">{c}</span>)}
                  </span>
                </button>
              );
            })}
          </div>
          {selectedId && (
            <button className="btn-primary" onClick={runAnalysis} disabled={analyzing}>
              {analyzing ? 'Analyzing…' : 'Analyze Selected Ride →'}
            </button>
          )}
        </section>
      )}

      {error && <div className="alert alert--error">{error}</div>}
      {analyzing && <AgentPipeline steps={steps} />}

      {/* ── Results ── */}
      {phase1 && (
        <section className="section">
          <div className="results-grid">
            <div className="card">
              <h3>Analysis</h3>
              <pre className="result-text">{phase1.analysis.raw || phase1.analysis.observations}</pre>
            </div>
            <div className="card">
              <h3>Weather Context</h3>
              <pre className="result-text">{phase1.weather.conditions}{phase1.weather.likely_impact ? `\n\n${phase1.weather.likely_impact}` : ''}</pre>
            </div>
          </div>

          {phase1.questions.length > 0 && (
            <div className="questions-bar">
              <span className="questions-bar-text">
                Your coach has {phase1.questions.length} question{phase1.questions.length !== 1 ? 's' : ''} — answer them to get deeper feedback.
              </span>
              <button className="btn-ghost" onClick={() => setModalOpen(true)}>Answer Questions →</button>
            </div>
          )}

          {coaching && (
            <div className="card card--accent">
              <h3>Coaching Feedback</h3>
              <pre className="result-text">{coaching}</pre>
            </div>
          )}
        </section>
      )}

      {modalOpen && phase1 && (
        <QuestionsModal
          questions={phase1.questions}
          open={modalOpen}
          onClose={() => setModalOpen(false)}
          onSubmit={handleRefine}
          loading={refineLoading}
        />
      )}
    </div>
  );
}
