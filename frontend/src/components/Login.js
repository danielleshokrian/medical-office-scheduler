import React, { useState } from 'react';
import { useAuth } from '../AuthContext';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import './Login.css';

function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const successMessage = searchParams.get('registered')
    ? 'Account created! You can now sign in.'
    : searchParams.get('reset')
    ? 'Password updated! You can now sign in.'
    : null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    const result = await login(email, password);
    setLoading(false);
    if (result.success) navigate('/');
    else setError(result.error || 'Invalid email or password');
  };

  const handleDemoLogin = async (demoEmail, demoPassword) => {
    setError('');
    setLoading(true);
    const result = await login(demoEmail, demoPassword);
    setLoading(false);
    if (result.success) navigate('/');
    else setError(result.error || 'Demo login failed');
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
            <button className="demo-role-button admin-demo-button"
              onClick={() => handleDemoLogin('admin@example.com', 'admin123')}
              disabled={loading}>
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
            <button className="demo-role-button nurse-demo-button"
              onClick={() => handleDemoLogin('lori@example.com', 'nurse123')}
              disabled={loading}>
              Demo: Nurse Login
            </button>
          </div>
        </div>

        <div className="login-box">
          <h2>Sign In</h2>

          {successMessage && (
            <div className="success-message">{successMessage}</div>
          )}
          {error && <div className="error-message">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input id="email" type="email" value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="you@example.com" required autoFocus />
            </div>

            <div className="form-group">
              <label htmlFor="password">
                Password
                <Link to="/forgot-password" className="forgot-link">Forgot password?</Link>
              </label>
              <input id="password" type="password" value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="Enter your password" required />
            </div>

            <button type="submit" className="login-button" disabled={loading}>
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <p style={{ textAlign: 'center', marginTop: 16, fontSize: 13, color: 'var(--c-gray-500)' }}>
            New nurse?{' '}
            <Link to="/register" style={{ color: 'var(--c-primary)', fontWeight: 600 }}>
              Create an account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Login;
