import { useState } from 'react';
import { authApi } from '../api/auth';

export default function ConnectStrava() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleConnect() {
    setLoading(true);
    setError(null);
    try {
      const { url } = await authApi.getStravaUrl();
      window.location.href = url;
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(`Connection failed: ${msg}`);
      setLoading(false);
    }
  }

  return (
    <div className="connect-strava">
      {error && <p className="connect-err">{error}</p>}
      <button className="btn-strava" onClick={handleConnect} disabled={loading}>
        {loading ? 'Redirecting…' : 'Connect with Strava'}
      </button>
    </div>
  );
}
