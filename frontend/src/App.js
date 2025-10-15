import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [staff, setStaff] = useState([]);
  const [areas, setAreas] = useState([]);
  const [shifts, setShifts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        const staffResponse = await fetch('http://127.0.0.1:5000/staff');
        if (!staffResponse.ok) throw new Error('Failed to fetch staff');
        const staffData = await staffResponse.json();
        setStaff(staffData);

        const areasResponse = await fetch('http://127.0.0.1:5000/areas');
        if (!areasResponse.ok) throw new Error('Failed to fetch areas');
        const areasData = await areasResponse.json();
        setAreas(areasData);

        const shiftsResponse = await fetch('http://127.0.0.1:5000/shifts');
        if (!shiftsResponse.ok) throw new Error('Failed to fetch shifts');
        const shiftsData = await shiftsResponse.json();
        setShifts(shiftsData);
        
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) return <div className="App"><h2>Loading...</h2></div>;
  if (error) return <div className="App"><h2>Error: {error}</h2></div>;

  return (
    <div className="App">
      <h1>Medical Office Scheduler</h1>
      
      <div className="test-data">
        <h2>Staff Members: {staff.length}</h2>
        <ul>
          {staff.slice(0, 5).map(s => (
            <li key={s.id}>{s.name} - {s.role}</li>
          ))}
        </ul>
        
        <h2>Areas: {areas.length}</h2>
        <ul>
          {areas.map(a => (
            <li key={a.id}>{a.name}</li>
          ))}
        </ul>
        
        <h2>Shifts: {shifts.length}</h2>
        <ul>
          {shifts.map(s => (
            <li key={s.id}>{s.staff_name} in {s.area_name} on {s.date}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default App;
