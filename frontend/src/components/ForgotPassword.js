import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { API_ENDPOINTS } from '../config';
import './Login.css';

function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await fetch(API_ENDPOINTS.AUTH_FORGOT_PASSWORD, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Request failed');
      setSent(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-wrapper" style={{ maxWidth: 440 }}>
        <div className="login-header">
          <div className="login-logo">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 5v14M5 12h14"/>
            </svg>
          </div>
          <h1>Medical Office Scheduler</h1>
          <p>Reset your password</p>
        </div>

        <div className="login-box">
          {sent ? (
            <div style={{ textAlign: 'center', padding: '8px 0' }}>
              <div style={{ fontSize: 40, marginBottom: 12 }}>
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--c-success)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 12 19.79 19.79 0 0 1 1.61 3.41 2 2 0 0 1 3.6 1h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L7.91 8.59a16 16 0 0 0 6 6l.96-.96a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/>
                </svg>
              </div>
              <h2 style={{ marginBottom: 8 }}>Check your email</h2>
              <p style={{ color: 'var(--c-gray-500)', fontSize: 14, marginBottom: 20 }}>
                If <strong>{email}</strong> is registered, you'll receive a reset link shortly. Check your spam folder too.
              </p>
              <Link to="/login" style={{ color: 'var(--c-primary)', fontWeight: 600, fontSize: 14 }}>
                Back to sign in
              </Link>
            </div>
          ) : (
            <>
              <h2> Forgot password?</h2>
              <p style={{ color: 'var(--c-gray-500)', fontSize: 13, marginBottom: 20, textAlign: 'center' }}>
                Enter your email and we'll send you a reset link.
              </p>

              {error && <div className="error-message">{error}</div>}

              <form onSubmit={handleSubmit}>
                <div className="form-group">
                  <label htmlFor="email">Email</label>
                  <input id="email" type="email" value={email}
                    onChange={e => setEmail(e.target.value)}
                    placeholder="you@example.com" required autoFocus />
                </div>
                <button type="submit" className="login-button" disabled={loading}>
                  {loading ? 'Sending...' : 'Send Reset Link'}
                </button>
              </form>

              <p style={{ textAlign: 'center', marginTop: 16, fontSize: 13, color: 'var(--c-gray-500)' }}>
                <Link to="/login" style={{ color: 'var(--c-primary)', fontWeight: 600 }}>Back to sign in</Link>
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default ForgotPassword;
