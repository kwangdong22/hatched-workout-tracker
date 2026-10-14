// services/api.js
// ─────────────────────────────────────────────────────────────
//  Replace BASE_URL with your local IP when testing on device.
//  e.g. 'http://192.168.1.10:8000' — localhost won't work on phone.
// ─────────────────────────────────────────────────────────────
export const BASE_URL = 'http://192.168.0.71:8000';

let authToken = null;

export function setAuthToken(token) {
  authToken = token;
}

export function getAuthToken() {
  return authToken;
}

async function request(method, path, body = null, token = null) {
  const headers = { 'Content-Type': 'application/json' };
  const effectiveToken = token || authToken;
  if (effectiveToken) headers['Authorization'] = `Bearer ${effectiveToken}`;

  const options = { method, headers };
  if (body) options.body = JSON.stringify(body);

  const res = await fetch(`${BASE_URL}${path}`, options);
  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new Error(data.detail || 'Request failed');
  }
  return data;
}

// ── Auth ─────────────────────────────────────────────────────
export const authAPI = {
  register: (email, username, password) =>
    request('POST', '/api/auth/register', { email, username, password }),

  login: async (email, password) => {
    const data = await request('POST', '/api/auth/login', { email, password });
    if (data.access_token) {
      setAuthToken(data.access_token);
    }
    return data;
  },
};

// ── Workouts ─────────────────────────────────────────────────
export const workoutAPI = {
  logWorkout: (workoutDate, token = null, exercises = []) =>
    request('POST', '/api/workouts/log', { workout_date: workoutDate, exercises }, token),

  getStreak: (token = null) =>
    request('GET', '/api/workouts/streak', null, token),

  getWeeklyCycle: (token = null) =>
    request('GET', '/api/workouts/weekly-cycle', null, token),

  logSet: (workoutExerciseId, setNumber, reps, weight, rpe = null, token = null) =>
    request('POST', '/api/workouts/sets', {
      workout_exercise_id: workoutExerciseId,
      set_number: setNumber,
      reps,
      weight,
      rpe,
    }, token),
};

// ── Goals ────────────────────────────────────────────────────
export const goalAPI = {
  setGoal: (targetHours, targetDays, token = null) =>
    request('POST', '/api/goals', {
      target_hours_per_week: targetHours,
      target_days_per_week: targetDays,
    }, token),

  getGoal: (token = null) =>
    request('GET', '/api/goals/active', null, token),
};

// ── Gamification ─────────────────────────────────────────────
export const gamificationAPI = {
  getStatus: (token = null) =>
    request('GET', '/api/gamification', null, token),
};
