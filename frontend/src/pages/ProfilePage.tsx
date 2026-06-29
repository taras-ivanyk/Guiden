import { useState, useEffect } from 'react';
import type { UserProfile } from '../types/api';

const STORAGE_KEY = 'profile';

const DEFAULTS: UserProfile = {
  age: 30,
  ftp: 250,
  goal: 'General fitness',
  experience: 'Intermediate',
  injuries: 'None',
};

function loadProfile(): UserProfile {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as UserProfile) : { ...DEFAULTS };
  } catch {
    return { ...DEFAULTS };
  }
}

export default function ProfilePage() {
  const [profile, setProfile] = useState<UserProfile>(loadProfile);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setProfile(loadProfile());
  }, []);

  function handleChange(field: keyof UserProfile, value: string | number) {
    setProfile(prev => ({ ...prev, [field]: value }));
    setSaved(false);
  }

  function handleSave(e: React.FormEvent) {
    e.preventDefault();
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(profile));
    setSaved(true);
  }

  return (
    <div className="page profile-page">
      <h2>Athlete Profile</h2>
      <form onSubmit={handleSave} className="profile-form">
        <label>
          Age
          <input
            type="number"
            min={10}
            max={100}
            value={profile.age}
            onChange={e => handleChange('age', Number(e.target.value))}
          />
        </label>

        <label>
          FTP (W)
          <input
            type="number"
            min={50}
            max={600}
            value={profile.ftp}
            onChange={e => handleChange('ftp', Number(e.target.value))}
          />
        </label>

        <label>
          Goal
          <select value={profile.goal} onChange={e => handleChange('goal', e.target.value)}>
            <option>General fitness</option>
            <option>Lose weight</option>
            <option>Build endurance</option>
            <option>Race preparation</option>
            <option>Improve power</option>
          </select>
        </label>

        <label>
          Experience
          <select value={profile.experience} onChange={e => handleChange('experience', e.target.value)}>
            <option>Beginner</option>
            <option>Intermediate</option>
            <option>Advanced</option>
            <option>Elite</option>
          </select>
        </label>

        <label>
          Injuries / Limitations
          <textarea
            value={profile.injuries}
            onChange={e => handleChange('injuries', e.target.value)}
            rows={3}
          />
        </label>

        <button type="submit" className="btn-primary">
          Save Profile
        </button>
        {saved && <p className="save-success">Profile saved!</p>}
      </form>
    </div>
  );
}
