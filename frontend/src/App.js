import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './AuthContext';
import Login from './components/Login';
import Navbar from './components/Navbar';
import ScheduleCalendar from './components/ScheduleCalendar';
import StaffList from './components/StaffList';
import TimeOffRequests from './components/TimeOffRequests';
import './App.css';

function ProtectedRoute({ children, allowedRoles }) {
  const { isAuthenticated, loading, user } = useAuth();
  
  if (loading) {
    return <div>Loading...</div>;
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  if (allowedRoles && !allowedRoles.includes(user?.role)) {
    return <Navigate to="/" />;
  }

  return children;
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
            <ProtectedRoute allowedRoles={['nurse_admin', 'nurse']}>
              <ScheduleCalendar />
            </ProtectedRoute>
          }
        />
        
        <Route
          path="/staff"
          element={
            <ProtectedRoute allowedRoles={['nurse_admin']}>
              <StaffList />
            </ProtectedRoute>
          }
        />
        
        <Route
          path="/time-off"
          element={
            <ProtectedRoute allowedRoles={['nurse_admin', 'nurse']}>
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
