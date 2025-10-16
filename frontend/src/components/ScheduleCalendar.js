import React, { useState, useEffect } from 'react';
import './ScheduleCalendar.css';

function ScheduleCalendar() {
  const [shifts, setShifts] = useState([]);
  const [areas, setAreas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentWeek, setCurrentWeek] = useState(getMonday(new Date()));
  const [viewMode, setViewMode] = useState('week'); // 'week' or 'day'
  const [selectedDate, setSelectedDate] = useState(new Date());


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

  const getStaffColor = (staffId, role) => {
    const colorPalettes = {
    'RN': [
      '#3498db', '#5dade2', '#2874a6', '#1f618d', '#21618c',
      '#2e86c1', '#3498db', '#5dade2', '#85c1e9', '#aed6f1'
    ],
    'GI_Tech': [
      '#2ecc71', '#58d68d', '#27ae60', '#229954', '#1e8449',
      '#28b463', '#52be80', '#7dcea0', '#a9dfbf', '#d4efdf'
    ],
    'Scope_Tech': [
      '#e74c3c', '#ec7063', '#cb4335', '#c0392b', '#a93226',
      '#e67e22', '#f39c12', '#f8b739', '#fad7a0', '#fdebd0'
    ]
  };

  const palette = colorPalettes[role] || ['#95a5a6', '#7f8c8d', '#bdc3c7'];
  const colorIndex = staffId % palette.length;
  return palette[colorIndex];
};

  const getShiftsForAreaAndDate = (areaId, date) => {
    const dateStr = date.toISOString().split('T')[0];
    return shifts.filter(shift => 
      shift.area_id === areaId && shift.date === dateStr
    );
  };

  const getShiftsForDate = (date) => {
    const dateStr = date.toISOString().split('T')[0];
    return shifts.filter(shift => shift.date === dateStr);
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

  const switchToDayView = (date) => {
    setSelectedDate(date);
    setViewMode('day');
  };

  const switchToWeekView = () => {
    setViewMode('week');
  };

  const generateTimeSlots = () => {
    const slots = [];
    for (let hour = 6; hour <= 18; hour++) {
      for (let minute = 0; minute < 60; minute += 15) {
        const time = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
        slots.push(time);
      }
    }
    return slots;
  };

  const timeSlots = generateTimeSlots();

  // Position and height for shift box in calendar
  const calculateShiftPosition = (startTime, endTime) => {
    const parseTime = (time) => {
      const [hours, minutes] = time.split(':').map(Number);
      return hours * 60 + minutes;
    };

    const startMinutes = parseTime(startTime);
    const endMinutes = parseTime(endTime);
    const baseMinutes = 6 * 60; 

    const top = ((startMinutes - baseMinutes) / 15) * 30; 
    const height = ((endMinutes - startMinutes) / 15) * 30;

    return { top, height };
  };

  if (loading) return <div className="loading">Loading schedule...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  if (viewMode === 'week') {
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
              <div 
                key={date.toISOString()} 
                className="day-header clickable"
                onClick={() => switchToDayView(date)}
              >
                <div className="day-name">{date.toLocaleDateString('en-US', { weekday: 'short' })}</div>
                <div className="day-date">{date.toLocaleDateString('en-US', { month: 'numeric', day: 'numeric' })}</div>
                <div className="view-detail">View Details →</div>
              </div>
            ))}
          </div>

          {areas.map(area => (
            <div key={area.id} className="area-row">
              <div className="area-name">{area.name}</div>
              {weekDates.map(date => {
                const areaShifts = getShiftsForAreaAndDate(area.id, date);
                return (
                  <div 
                    key={`${area.id}-${date.toISOString()}`} 
                    className="schedule-cell"
                    onClick={() => switchToDayView(date)}
                  >
                    {areaShifts.length === 0 ? (
                      <div className="empty-cell">Not Staffed</div>
                    ) : (
                      areaShifts.map(shift => (
                        <div 
                          key={shift.id} 
                          className="shift-card"
                          style={{ background: getStaffColor(shift.staff_id, shift.staff_role) }}
                        >
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

  const dayShifts = getShiftsForDate(selectedDate);
  
  return (
    <div className="schedule-container">
      <div className="schedule-header">
        <button onClick={switchToWeekView}>← Back to Week View</button>
        <h2>{selectedDate.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}</h2>
      </div>

      <div className="timeline-view">
        <div className="timeline-header">
          <div className="time-column-header">Time</div>
          {areas.map(area => (
            <div key={area.id} className="area-column-header">
              {area.name}
            </div>
          ))}
        </div>

        <div className="timeline-body">
          <div className="time-column">
            {timeSlots.map(time => (
              <div key={time} className="time-slot">{time}</div>
            ))}
          </div>

          {areas.map(area => {
            const areaShifts = getShiftsForAreaAndDate(area.id, selectedDate);
            return (
              <div key={area.id} className="area-column">
                <div className="shifts-container">
                  {areaShifts.map(shift => {
                    const { top, height } = calculateShiftPosition(shift.start_time, shift.end_time);
                    return (
                      <div
                        key={shift.id}
                        className="timeline-shift-box"
                        style={{
                          top: `${top}px`,
                          height: `${height}px`,
                          background: getStaffColor(shift.staff_id, shift.staff_role)
                        }}
                      >
                        <div className="timeline-staff-name">{shift.staff_name}</div>
                        <div className="timeline-staff-role">{shift.staff_role}</div>
                        <div className="timeline-shift-time">
                          {shift.start_time} - {shift.end_time}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="legend">
        <h3>Legend:</h3>
        <div className="legend-items">
          {Array.from(new Set(
            (viewMode === 'week' ? shifts : dayShifts).map(s => s.staff_id)
          )).map(staffId => {
            const shift = (viewMode === 'week' ? shifts : dayShifts).find(s => s.staff_id === staffId);
            return (
              <div key={staffId} className="legend-item">
                <div 
                  className="legend-color" 
                  style={{ background: getStaffColor(staffId, shift.staff_role) }}
                ></div>
                <span>{shift.staff_name} ({shift.staff_role})</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default ScheduleCalendar;