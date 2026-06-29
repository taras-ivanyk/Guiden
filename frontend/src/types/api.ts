// ─── Auth ────────────────────────────────────────────────────────────────────

export interface StravaUrlResponse {
  url: string;
}

export interface AuthCallbackPayload {
  code: string;
}

export interface AthleteInfo {
  id: number;
  firstname: string;
  lastname: string;
  profile: string;
}

export interface AuthCallbackResponse {
  jwt: string;
  athlete: AthleteInfo;
}

// ─── Profile ─────────────────────────────────────────────────────────────────

export interface UserProfile {
  age: number;
  ftp: number;
  goal: string;
  experience: string;
  injuries: string;
}

// ─── Activity / Strava ───────────────────────────────────────────────────────

export interface ActivitySummary {
  id: string;
  name: string;
  type: string;
  date: string;
  distance_km: number;
  moving_time_min: number;
  avg_hr?: number;
  max_hr?: number;
  avg_watts?: number;
}

export interface RecentSummary {
  days: number;
  num_rides: number;
  total_hours: number;
  total_distance_km: number;
  avg_power?: number;
  num_hard_sessions: number;
}

// ─── Analysis ────────────────────────────────────────────────────────────────

export interface AnalysisResult {
  summary: string[];
  structure: string;
  observations: string;
  deviations: string;
  raw: string;
}

export interface WeatherResult {
  conditions: string;
  likely_impact: string;
}

export interface AnalyzeStartRequest {
  activity_id: string;
  profile: UserProfile;
}

export interface AnalyzeStartResponse {
  activity_id: string;
  analysis: AnalysisResult;
  weather: WeatherResult;
  questions: string[];
}

export interface AnalyzeCoachRequest {
  activity_id: string;
  profile: UserProfile;
  analysis: AnalysisResult;
  weather: WeatherResult;
  answers: Record<string, string>;
}

export interface AnalyzeCoachResponse {
  coaching_output: string;
}

// ─── Plan ────────────────────────────────────────────────────────────────────

export interface CalendarSlot {
  day: string;
  start: string;
  end: string;
  duration_min: number;
}

export interface PlanRequest {
  profile: UserProfile;
  calendar: CalendarSlot[];
  weeks?: number;
  recent_summary?: RecentSummary | null;
}

export interface SessionResponse {
  day: string;
  type: string;
  duration_min: number;
  intensity: string;
  start_time?: string;
}

export interface WeekResponse {
  week_num: number;
  focus: string;
  total_hours: number;
  sessions: SessionResponse[];
  recovery_days: string[];
}
