import React, { useState } from 'react';
import { useAuth } from '../AuthContext';
import { useNavigate } from 'react-router-dom';
import './Login.css';

function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const result = await login(username, password);
    setLoading(false);

    if (result.success) {
      navigate('/');
    } else {
      setError(result.error || 'Invalid username or password');
    }
  };

  const handleDemoLogin = async (demoUsername, demoPassword) => {
    setError('');
    setLoading(true);
    const result = await login(demoUsername, demoPassword);
    setLoading(false);

    if (result.success) {
      navigate('/');
    } else {
      setError(result.error || 'Demo login failed');
    }
  };

  return (
    <div className="login-container">
      <div className="login-wrapper">
        <div className="login-header">
          <div className="login-logo">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 5v14M5 12h14"/>
          </svg>
        </div>
          <h1>Medical Office Scheduler</h1>
          <p>Staff scheduling and time-off management</p>
        </div>

        <div className="role-cards">
          <div className="role-card admin-card">
            <div className="role-card-icon">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              </svg>
            </div>
            <h3>Nurse Administrator</h3>
            <ul className="role-features">
              <li>Create &amp; edit schedules</li>
              <li>Manage staff members</li>
              <li>Approve or deny time-off requests</li>
              <li>AI-assisted schedule generation</li>
            </ul>
            <button
              className="demo-role-button admin-demo-button"
              onClick={() => handleDemoLogin('admin', 'admin123')}
              disabled={loading}
            >
              Demo: Admin Login
            </button>
          </div>

          <div className="role-card nurse-card">
            <div className="role-card-icon">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
            </div>
            <h3>Nurse</h3>
            <ul className="role-features">
              <li>View weekly schedule</li>
              <li>Submit time-off requests</li>
              <li>Track request status</li>
              <li>View your assigned shifts</li>
            </ul>
            <button
              className="demo-role-button nurse-demo-button"
              onClick={() => handleDemoLogin('lori', 'nurse123')}
              disabled={loading}
            >
              Demo: Nurse Login
            </button>
          </div>
        </div>

        <div className="login-box">
          <h2>Sign In</h2>

          {error && <div className="error-message">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="username">Username</label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
                required
                autoFocus
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                required
              />
            </div>

            <button type="submit" className="login-button" disabled={loading}>
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default Login;
