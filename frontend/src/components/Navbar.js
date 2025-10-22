import React from 'react';
import { Link } from 'react-router-dom';
import './Navbar.css';

function Navbar() {
  return (
    <nav className="navbar">
      <h1>Medical Office Scheduler</h1>
      <ul>
        <li><Link to="/">Schedule</Link></li>
        <li><Link to="/staff">Staff</Link></li>
        <li><Link to="/time-off">Time Off</Link></li>
      </ul>
    </nav>
  );
}

export default Navbar;