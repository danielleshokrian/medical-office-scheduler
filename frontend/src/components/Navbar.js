import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import './Navbar.css';

const ROLE_LABELS = {
  nurse_admin: 'Nurse Administrator',
  nurse: 'Nurse',
};

function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const isAdmin = user?.role === 'nurse_admin';

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="navbar">
      <div className="nav-left">
        <h1>Medical Office Scheduler</h1>
      </div>
      <div className="nav-links">
        <Link to="/">Schedule</Link>
        {isAdmin && <Link to="/staff">Staff</Link>}
        <Link to="/time-off">Time Off</Link>
      </div>
      <div className="nav-right">
        <span className="user-info">
          <span className={`role-badge role-badge--${user?.role}`}>
            {ROLE_LABELS[user?.role] || user?.role}
          </span>
          {user?.username}
        </span>
        <button onClick={handleLogout} className="logout-button">
          Logout
        </button>
      </div>
    </nav>
  );
}

export default Navbar;
