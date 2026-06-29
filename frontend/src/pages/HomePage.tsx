import { useSearchParams } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import ConnectStrava from '../components/ConnectStrava';

export default function HomePage() {
  const { isAuthenticated, athlete } = useAuth();
  const [params] = useSearchParams();
  const stravaError = params.get('strava_error');

  return (
    <div className="page page--medium">
      <div className="home-hero">
        <h1>Guiden</h1>
        <p>Your AI cycling coach — analyse rides, plan training, get smarter.</p>
      </div>

      {stravaError && (
        <div className="alert alert--error">Strava connection failed. Please try again.</div>
      )}

      {isAuthenticated && athlete ? (
        <>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            Hi <strong>{athlete.firstname}</strong> — what do you want to work on today?
          </p>
          <div className="feature-cards">
            <a className="feature-card" href="/analyze">
              <h3>Analyze Workout</h3>
              <p>Deep analysis and coaching feedback on any of your recent rides.</p>
            </a>
            <a className="feature-card" href="/plan">
              <h3>Training Plan</h3>
              <p>Generate a personalised next session based on your schedule and fitness.</p>
            </a>
            <a className="feature-card" href="/profile">
              <h3>Athlete Profile</h3>
              <p>Keep your FTP, goals and training history up to date for better coaching.</p>
            </a>
          </div>
        </>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <p style={{ color: 'var(--text-muted)' }}>Connect your Strava account to get started.</p>
          <ConnectStrava />
        </div>
      )}
    </div>
  );
}
