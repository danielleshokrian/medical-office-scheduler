import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import ScheduleCalendar from './components/ScheduleCalendar';
import StaffList from './components/StaffList';
import TimeOffRequests from './components/TimeOffRequests';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Navbar />
        <Routes>
          <Route path="/" element={<ScheduleCalendar />} />
          <Route path="/staff" element={<StaffList />} />
          <Route path="/time-off" element={<TimeOffRequests />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
