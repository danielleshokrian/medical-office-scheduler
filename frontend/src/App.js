import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import ScheduleCalendar from './components/ScheduleCalendar';
import StaffList from './components/StaffList';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Navbar />
        <Routes>
          <Route path="/" element={<ScheduleCalendar />} />
          <Route path="/staff" element={<StaffList />} />
          <Route path="/shifts" element={<div style={{padding: '20px'}}><h2>Shifts Page - Coming Soon</h2></div>} />
          <Route path="/time-off" element={<div style={{padding: '20px'}}><h2>Time Off Page - Coming Soon</h2></div>} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
