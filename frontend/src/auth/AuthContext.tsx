import React, { createContext, useCallback, useContext, useMemo, useState } from 'react';
import type { AthleteInfo } from '../types/api';

interface AuthState {
  token: string | null;
  athlete: AthleteInfo | null;
  isAuthenticated: boolean;
}

interface AuthContextValue extends AuthState {
  login: (token: string, athlete: AthleteInfo) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const TOKEN_KEY = 'jwt';
const ATHLETE_KEY = 'athlete';

function loadFromStorage(): AuthState {
  try {
    const token = sessionStorage.getItem(TOKEN_KEY);
    const athleteRaw = sessionStorage.getItem(ATHLETE_KEY);
    const athlete: AthleteInfo | null = athleteRaw ? (JSON.parse(athleteRaw) as AthleteInfo) : null;
    return { token, athlete, isAuthenticated: !!token && !!athlete };
  } catch {
    return { token: null, athlete: null, isAuthenticated: false };
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>(loadFromStorage);

  const login = useCallback((token: string, athlete: AthleteInfo) => {
    sessionStorage.setItem(TOKEN_KEY, token);
    sessionStorage.setItem(ATHLETE_KEY, JSON.stringify(athlete));
    setState({ token, athlete, isAuthenticated: true });
  }, []);

  const logout = useCallback(() => {
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(ATHLETE_KEY);
    setState({ token: null, athlete: null, isAuthenticated: false });
  }, []);

  const value = useMemo(
    () => ({ ...state, login, logout }),
    [state, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
