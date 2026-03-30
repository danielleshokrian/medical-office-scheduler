import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { API_ENDPOINTS } from '../config';
import './Login.css';

function Register() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({ name: '', email: '', password: '', confirm: '', invite_code: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (formData.password !== formData.confirm) {
      setError('Passwords do not match');
      return;
    }
    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(API_ENDPOINTS.AUTH_REGISTER, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: formData.name,
          email: formData.email,
          password: formData.password,
          invite_code: formData.invite_code
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Registration failed');
      navigate('/login?registered=1');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-wrapper" style={{ maxWidth: 480 }}>
        <div className="login-header">
          <div className="login-logo">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 5v14M5 12h14"/>
            </svg>
          </div>
          <h1>Medical Office Scheduler</h1>
          <p>Create your nurse account</p>
        </div>

        <div className="login-box">
          <h2>Create Account</h2>
          {error && <div className="error-message">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="name">Full Name</label>
              <input id="name" name="name" type="text" value={formData.name}
                onChange={handleChange} placeholder="Jane Smith" required />
            </div>
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input id="email" name="email" type="email" value={formData.email}
                onChange={handleChange} placeholder="you@example.com" required />
            </div>
            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input id="password" name="password" type="password" value={formData.password}
                onChange={handleChange} placeholder="At least 8 characters" required />
            </div>
            <div className="form-group">
              <label htmlFor="confirm">Confirm Password</label>
              <input id="confirm" name="confirm" type="password" value={formData.confirm}
                onChange={handleChange} placeholder="Repeat your password" required />
            </div>
            <div className="form-group">
              <label htmlFor="invite_code">Clinic Invite Code</label>
              <input id="invite_code" name="invite_code" type="text" value={formData.invite_code}
                onChange={handleChange} placeholder="Provided by your administrator" required />
            </div>

            <button type="submit" className="login-button" disabled={loading}>
              {loading ? 'Creating account...' : 'Create Account'}
            </button>
          </form>

          <p style={{ textAlign: 'center', marginTop: 16, fontSize: 13, color: 'var(--c-gray-500)' }}>
            Already have an account? <Link to="/login" style={{ color: 'var(--c-primary)', fontWeight: 600 }}>Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Register;
