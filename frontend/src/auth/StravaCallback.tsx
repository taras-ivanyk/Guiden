import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi } from '../api/auth';
import { useAuth } from './AuthContext';

export default function StravaCallback() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const processed = useRef(false);

  useEffect(() => {
    if (processed.current) return;
    processed.current = true;

    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const error = params.get('error');

    if (error || !code) {
      navigate('/?strava_error=1', { replace: true });
      return;
    }

    authApi
      .exchangeCode({ code })
      .then(({ jwt, athlete }) => {
        login(jwt, athlete);
        navigate('/', { replace: true });
      })
      .catch(() => {
        navigate('/?strava_error=1', { replace: true });
      });
  }, [login, navigate]);

  return (
    <div className="callback-loading">
      <p>Connecting to Strava…</p>
    </div>
  );
}
