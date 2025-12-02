import React, { useState } from 'react';
import { useAuth } from '../AuthContext';
import { useNavigate } from 'react-router-dom';
import './Login.css';

function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const result = await login(username, password);
    
    if (result.success) {
      navigate('/');
    } else {
      setError(result.error);
    }
  };

  const handleDemoLogin = async () => {
    setError('');
    const result = await login('admin', 'admin123');
    
    if (result.success) {
      navigate('/');
    } else {
      setError(result.error);
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <h2>Medical Office Scheduler</h2>
        <h3>Login</h3>
        
        {error && <div className="error-message">{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          
          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          
          <button type="submit" className="login-button">
            Login
          </button>
          
          <button 
            type="button" 
            onClick={handleDemoLogin}
            className="demo-button"
            style={{
              marginTop: '15px',
              background: 'linear-gradient(135deg, #42a5f5 0%, #1e88e5 100%)',
              color: 'white',
              border: 'none',
              padding: '14px 24px',
              borderRadius: '8px',
              cursor: 'pointer',
              width: '100%',
              fontSize: '16px',
              fontWeight: '600',
              transition: 'all 0.3s ease',
              boxShadow: '0 4px 12px rgba(66, 165, 245, 0.3)'
            }}
            onMouseOver={(e) => {
              e.target.style.background = 'linear-gradient(135deg, #1e88e5 0%, #1565c0 100%)';
              e.target.style.boxShadow = '0 6px 16px rgba(66, 165, 245, 0.4)';
              e.target.style.transform = 'translateY(-2px)';
            }}
            onMouseOut={(e) => {
              e.target.style.background = 'linear-gradient(135deg, #42a5f5 0%, #1e88e5 100%)';
              e.target.style.boxShadow = '0 4px 12px rgba(66, 165, 245, 0.3)';
              e.target.style.transform = 'translateY(0)';
            }}
          >
            Try Demo Account
          </button>
        </form>
        
        <p style={{ 
          marginTop: '20px', 
          fontSize: '14px', 
          color: '#666',
          textAlign: 'center' 
        }}>
          Demo account has pre-loaded staff and schedules
        </p>
      </div>
    </div>
  );
}

export default Login;