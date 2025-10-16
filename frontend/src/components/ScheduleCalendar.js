import React, { useState, useEffect } from 'react';
import './ScheduleCalendar.css';

function ScheduleCalendar() {
  const [shifts, setShifts] = useState([]);
  const [areas, setAreas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentWeek, setCurrentWeek] = useState(getMonday(new Date()));

  function getMonday(date) {
    const d = new Date(date);
    const day = d.getDay();
    const diff = d.getDate() - day + (day === 0 ? -6 : 1);
    return new Date(d.setDate(diff));
  }

  function getWeekDates(monday) {
    return Array.from({ length: 5 }, (_, i) => {
      const date = new Date(monday);
      date.setDate(monday.getDate() + i);
      return date;
    });
  }

  const weekDates = getWeekDates(currentWeek);

  useEffect(() => {
    fetchScheduleData();
  }, [currentWeek]);

  const fetchScheduleData = async () => {
    try {
      setLoading(true);
      
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

  const getShiftsForAreaAndDate = (areaId, date) => {
    const dateStr = date.toISOString().split('T')[0];
    return shifts.filter(shift => 
      shift.area_id === areaId && shift.date === dateStr
    );
  };

  const goToPreviousWeek = () => {
    const newWeek = new Date(currentWeek);
    newWeek.setDate(currentWeek.getDate() - 7);
    setCurrentWeek(newWeek);
  };

  const goToNextWeek = () => {
    const newWeek = new Date(currentWeek);
    newWeek.setDate(currentWeek.getDate() + 7);
    setCurrentWeek(newWeek);
  };

  const goToCurrentWeek = () => {
    setCurrentWeek(getMonday(new Date()));
  };

  if (loading) return <div className="loading">Loading schedule...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div className="schedule-container">
      <div className="schedule-header">
        <button onClick={goToPreviousWeek}>← Previous Week</button>
        <h2>Week of {currentWeek.toLocaleDateString()}</h2>
        <button onClick={goToNextWeek}>Next Week →</button>
        <button onClick={goToCurrentWeek}>Today</button>
      </div>

      <div className="schedule-grid">
        <div className="grid-header">
          <div className="area-label">Area</div>
          {weekDates.map(date => (
            <div key={date.toISOString()} className="day-header">
              <div className="day-name">{date.toLocaleDateString('en-US', { weekday: 'short' })}</div>
              <div className="day-date">{date.toLocaleDateString('en-US', { month: 'numeric', day: 'numeric' })}</div>
            </div>
          ))}
        </div>

        {areas.map(area => (
          <div key={area.id} className="area-row">
            <div className="area-name">{area.name}</div>
            {weekDates.map(date => {
              const areaShifts = getShiftsForAreaAndDate(area.id, date);
              return (
                <div key={`${area.id}-${date.toISOString()}`} className="schedule-cell">
                  {areaShifts.length === 0 ? (
                    <div className="empty-cell">Not Staffed</div>
                  ) : (
                    areaShifts.map(shift => (
                      <div key={shift.id} className="shift-card">
                        <div className="staff-name">{shift.staff_name}</div>
                        <div className="shift-time">{shift.start_time} - {shift.end_time}</div>
                      </div>
                    ))
                  )}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}

export default ScheduleCalendar;