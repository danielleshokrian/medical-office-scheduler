import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './AuthContext';
import Login from './components/Login';
import Navbar from './components/Navbar';
import ScheduleCalendar from './components/ScheduleCalendar';
import StaffList from './components/StaffList';
import TimeOffRequests from './components/TimeOffRequests';
import './App.css';

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return <div>Loading...</div>;
  }
  
  return isAuthenticated ? children : <Navigate to="/login" />;
}

function AppContent() {
  const { isAuthenticated, user } = useAuth();

  return (
    <Router>
      {isAuthenticated && <Navbar user={user} />}
      
      <Routes>
        <Route path="/login" element={<Login />} />
        
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <ScheduleCalendar />
            </ProtectedRoute>
          }
        />
        
        <Route
          path="/staff"
          element={
            <ProtectedRoute>
              <StaffList />
            </ProtectedRoute>
          }
        />
        
        <Route
          path="/time-off"
          element={
            <ProtectedRoute>
              <TimeOffRequests />
            </ProtectedRoute>
          }
        />
      </Routes>
    </Router>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
