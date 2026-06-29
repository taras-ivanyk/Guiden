import { useState } from 'react';
import { useAuth } from '../auth/AuthContext';
import ConnectStrava from '../components/ConnectStrava';
import LoadingSpinner from '../components/LoadingSpinner';
import { stravaApi } from '../api/strava';
import { planApi } from '../api/plan';
import type { CalendarSlot, WeekResponse, UserProfile } from '../types/api';

const DAYS = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];

function toMins(t: string) { const [h, m] = t.split(':').map(Number); return h * 60 + m; }
function fmtDur(start: string, end: string) {
  const m = Math.max(0, toMins(end) - toMins(start));
  return m >= 60 ? `${Math.floor(m/60)}h${m%60 ? `${m%60}m` : ''}` : `${m}m`;
}

function loadProfile(): UserProfile {
  try {
    const r = sessionStorage.getItem('profile');
    return r ? JSON.parse(r) : { age: 30, ftp: 250, goal: 'General fitness', experience: 'Intermediate', injuries: 'None' };
  } catch { return { age: 30, ftp: 250, goal: 'General fitness', experience: 'Intermediate', injuries: 'None' }; }
}

export default function PlanPage() {
  const { isAuthenticated } = useAuth();
  const [cal, setCal] = useState<Record<string, { start: string; end: string }>>({
    Saturday: { start: '09:00', end: '11:00' },
    Sunday:   { start: '08:00', end: '10:00' },
  });
  const [weeks, setWeeks] = useState(4);
  const [result, setResult] = useState<WeekResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function toggleDay(day: string) {
    setCal(prev => {
      const next = { ...prev };
      if (day in next) { delete next[day]; } else { next[day] = { start: '09:00', end: '11:00' }; }
      return next;
    });
  }
  function updateTime(day: string, field: 'start' | 'end', val: string) {
    setCal(prev => ({ ...prev, [day]: { ...prev[day], [field]: val } }));
  }

  async function generate() {
    const keys = Object.keys(cal);
    if (!keys.length) { setError('Select at least one training day.'); return; }
    const calendar: CalendarSlot[] = keys.map(day => ({
      day, start: cal[day].start, end: cal[day].end,
      duration_min: Math.max(0, toMins(cal[day].end) - toMins(cal[day].start)),
    }));
    setLoading(true); setError(null);
    try {
      let recent_summary = null;
      try { recent_summary = await stravaApi.getRecentSummary(); } catch { /* optional */ }
      const res = await planApi.nextSession({ profile: loadProfile(), calendar, weeks, recent_summary });
      setResult(res.next_session);
    } catch (e: unknown) { setError(e instanceof Error ? e.message : String(e)); }
    finally { setLoading(false); }
  }

  if (!isAuthenticated) {
    return (
      <div className="page page--medium">
        <div>
          <h1>Training Plan</h1>
          <p style={{ color: 'var(--text-muted)', marginTop: '0.25rem' }}>Connect Strava to generate a personalised plan.</p>
        </div>
        <ConnectStrava />
      </div>
    );
  }

  const hasResult = result !== null;

  return (
    <div className="page" style={{ maxWidth: hasResult ? '1000px' : '680px' }}>
      <h1>Training Plan</h1>

      <div className={`plan-workspace${hasResult ? ' plan-workspace--split' : ''}`}>
        {/* ── Form column ── */}
        <div className={`plan-form-col${hasResult ? '' : ' plan-form-col--solo'}`}>
          <section className="section">
            <h2>Your Availability</h2>
            <div className="calendar-grid">
              {DAYS.map(day => {
                const active = day in cal;
                return (
                  <div key={day} className={`cal-tile${active ? ' cal-tile--active' : ''}`}>
                    <label className="cal-tile-label">
                      <input type="checkbox" checked={active} onChange={() => toggleDay(day)} />
                      {day}
                    </label>
                    {active && (
                      <div className="cal-times">
                        <input type="time" value={cal[day].start}
                          onChange={e => updateTime(day, 'start', e.target.value)} />
                        <span style={{ color: 'var(--text-subtle)', fontSize: '0.75rem' }}>–</span>
                        <input type="time" value={cal[day].end}
                          onChange={e => updateTime(day, 'end', e.target.value)} />
                        <span className="duration-badge">{fmtDur(cal[day].start, cal[day].end)}</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </section>

          <div className="plan-controls">
            <label>
              Weeks:
              <input type="number" min={1} max={12} value={weeks}
                onChange={e => setWeeks(Number(e.target.value))} className="weeks-input" />
            </label>
            <button className="btn-primary" onClick={generate} disabled={loading}>
              {loading ? 'Generating…' : hasResult ? 'Regenerate →' : 'Generate Plan →'}
            </button>
          </div>

          {loading && <LoadingSpinner label="Building your plan…" />}
          {error && <div className="alert alert--error">{error}</div>}
        </div>

        {/* ── Result column ── */}
        {result && (
          <div className="plan-result-col">
            <div className="card card--accent">
              <h3>Week {result.week_num} — {result.focus}</h3>
              <p className="result-meta">
                {result.total_hours.toFixed(1)}h planned
                {result.recovery_days?.length ? ` • Rest: ${result.recovery_days.join(', ')}` : ''}
              </p>
              <div className="sessions-list">
                {result.sessions.map((s, i) => (
                  <div key={i} className="session-row">
                    <span className="session-day">{s.day}{s.start_time ? ` ${s.start_time}` : ''}</span>
                    <span className="session-info">
                      <strong>{s.type}</strong> · {s.duration_min}min · {s.intensity}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
