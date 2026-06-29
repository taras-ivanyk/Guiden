import { NavLink } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';

export default function Sidebar() {
  const { athlete, isAuthenticated, logout } = useAuth();

  return (
    <nav className="sidebar">
      <div className="sidebar-logo">Guiden</div>

      {isAuthenticated && athlete && (
        <div className="sidebar-athlete">
          <img
            src={athlete.profile}
            alt={`${athlete.firstname} ${athlete.lastname}`}
            className="sidebar-avatar"
          />
          <span className="sidebar-name">
            {athlete.firstname} {athlete.lastname}
          </span>
        </div>
      )}

      <ul className="sidebar-nav">
        <li>
          <NavLink to="/" end className={({ isActive }) => isActive ? 'active' : ''}>
            Home
          </NavLink>
        </li>
        <li>
          <NavLink to="/analyze" className={({ isActive }) => isActive ? 'active' : ''}>
            Analyze
          </NavLink>
        </li>
        <li>
          <NavLink to="/plan" className={({ isActive }) => isActive ? 'active' : ''}>
            Plan
          </NavLink>
        </li>
        <li>
          <NavLink to="/profile" className={({ isActive }) => isActive ? 'active' : ''}>
            Profile
          </NavLink>
        </li>
      </ul>

      {isAuthenticated && (
        <button className="btn-logout" onClick={logout}>
          Disconnect Strava
        </button>
      )}
    </nav>
  );
}
