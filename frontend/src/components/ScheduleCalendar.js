import React, { useState, useEffect } from 'react';
import './ScheduleCalendar.css';
import ShiftForm from './ShiftForm';

function ScheduleCalendar() {
  const [shifts, setShifts] = useState([]);
  const [areas, setAreas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentWeek, setCurrentWeek] = useState(getMonday(new Date()));
  const [viewMode, setViewMode] = useState('week'); // 'week' or 'day'
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [showShiftForm, setShowShiftForm] = useState(false);
  const [selectedShift, setSelectedShift] = useState(null);
  const [selectedDateForForm, setSelectedDateForForm] = useState(null);
  const [staff, setStaff] = useState([]);
  const [coverage, setCoverage] = useState({});
  const [history, setHistory] = useState([]);
  const [historyIndex, setHistoryIndex] = useState(-1);

  const [previewMode, setPreviewMode] = useState(false);
  const [previewShifts, setPreviewShifts] = useState([]);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState('');



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

  useEffect(() => {
  if (areas.length > 0) {
    fetchCoverageData();
  }
}, [viewMode, selectedDate, areas]);

const fetchCoverageData = async () => {
  try {
    const coverageData = {};
    
    const datesToCheck = viewMode === 'week' ? weekDates : [selectedDate];
    
    for (const date of datesToCheck) {
      const dateStr = date.toISOString().split('T')[0];
      coverageData[dateStr] = {};
      
      for (const area of areas) {
        const response = await fetch(`http://127.0.0.1:5000/coverage/${area.id}/${dateStr}`);
        if (response.ok) {
          const data = await response.json();
          coverageData[dateStr][area.id] = data;
        }
      }
    }
    
    setCoverage(coverageData);
  } catch (err) {
    console.error('Failed to fetch coverage data:', err);
  }
};
      
const fetchScheduleData = async () => {
  try {
    setLoading(true);
    
    const [areasResponse, shiftsResponse, staffResponse] = await Promise.all([
      fetch('http://127.0.0.1:5000/areas'),
      fetch('http://127.0.0.1:5000/shifts'),
      fetch('http://127.0.0.1:5000/staff')
    ]);
    
    if (!areasResponse.ok) throw new Error('Failed to fetch areas');
    if (!shiftsResponse.ok) throw new Error('Failed to fetch shifts');
    if (!staffResponse.ok) throw new Error('Failed to fetch staff');
    
    const areasData = await areasResponse.json();
    const shiftsData = await shiftsResponse.json();
    const staffData = await staffResponse.json();
    
    setAreas(areasData);
    setShifts(shiftsData);
    setStaff(staffData);
    
    setLoading(false);

    setTimeout(() => fetchCoverageData(), 100);
  } catch (err) {
    setError(err.message);
    setLoading(false);
  }
};

const getCoverageStatus = (areaId, date) => {
  const dateStr = date.toISOString().split('T')[0];
  const coverageInfo = coverage[dateStr]?.[areaId];
  
  if (!coverageInfo) return { status: 'unknown', warnings: [] };
  
  if (coverageInfo.is_covered) {
    return { status: 'covered', warnings: [] };
  } else if (coverageInfo.warnings && coverageInfo.warnings.length > 0) {
    return { status: 'understaffed', warnings: coverageInfo.warnings };
  } else {
    return { status: 'empty', warnings: ['Not staffed'] };
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
    // Get actual shifts
    const actualShifts = shifts.filter(shift => 
      shift.area_id === areaId && 
      shift.date === dateStr
    );
    
    // Get preview shifts if in preview mode
    const previewShiftsForCell = previewMode ? previewShifts.filter(shift =>
      shift.area_id === areaId &&
      shift.date === dateStr
    ) : [];
    
    return [...actualShifts, ...previewShiftsForCell];
  };

  const getShiftsForDate = (date) => {
    const dateStr = date.toISOString().split('T')[0];
    // Get actual shifts
    const actualShifts = shifts.filter(shift => shift.date === dateStr);
    
    // Get preview shifts if in preview mode
    const previewShiftsForDate = previewMode ? previewShifts.filter(shift =>
      shift.date === dateStr
    ) : [];
    
    return [...actualShifts, ...previewShiftsForDate];
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

  const handleAddShift = (date = null) => {
  saveToHistory(shifts);
  setSelectedShift(null);
  setSelectedDateForForm(date || new Date());
  setShowShiftForm(true);
};

const handleEditShift = (shift) => {
  saveToHistory(shifts);
  setSelectedShift(shift);
  setShowShiftForm(true);
};

const handleCloseForm = () => {
  saveToHistory(shifts);
  setShowShiftForm(false);
  setSelectedShift(null);
  setSelectedDateForForm(null);
};

const handleShiftSubmit = (data) => {
  if (data.deleted) {
    setShifts(shifts.filter(s => s.id !== data.id));
  } else {
    fetchScheduleData();
  }
};

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

  const dayShifts = viewMode === 'day' ? getShiftsForDate(selectedDate) : [];

  // AI Scheduling Handlers
  const handleGenerateFullSchedule = async () => {
  if (!window.confirm('⚠️ This will replace ALL existing shifts for this week. Continue?')) {
    return;
  }
  
  setAiLoading(true);
  setAiError('');
  
  try {
    const monday = getMonday(currentWeek);
    const response = await fetch('http://127.0.0.1:5000/ai/generate-schedule', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        week_start_date: monday.toISOString().split('T')[0],
        fill_empty_only: false
      })
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to generate schedule');
    }
    
    const data = await response.json();
    
    // Convert AI shifts to preview format with staff/area info
    const shiftsWithInfo = data.shifts.map(shift => ({
      ...shift,
      id: `preview-${Math.random()}`,
      staff_name: staff.find(s => s.id === shift.staff_id)?.name || 'Unknown',
      staff_role: staff.find(s => s.id === shift.staff_id)?.role || 'Unknown',
      area_name: areas.find(a => a.id === shift.area_id)?.name || 'Unknown',
      is_preview: true
    }));
    
    setPreviewShifts(shiftsWithInfo);
    setPreviewMode(true);
    setAiLoading(false);
  } catch (err) {
    setAiError(err.message);
    setAiLoading(false);
  }
};

const handleFillEmptyShifts = async () => {
  setAiLoading(true);
  setAiError('');
  
  try {
    const monday = getMonday(currentWeek);
    const response = await fetch('http://127.0.0.1:5000/ai/generate-schedule', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        week_start_date: monday.toISOString().split('T')[0],
        fill_empty_only: true
      })
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to generate suggestions');
    }
    
    const data = await response.json();
    
    // Convert AI shifts to preview format with staff/area info
    const shiftsWithInfo = data.shifts.map(shift => ({
      ...shift,
      id: `preview-${Math.random()}`,
      staff_name: staff.find(s => s.id === shift.staff_id)?.name || 'Unknown',
      staff_role: staff.find(s => s.id === shift.staff_id)?.role || 'Unknown',
      area_name: areas.find(a => a.id === shift.area_id)?.name || 'Unknown',
      is_preview: true
    }));
    
    setPreviewShifts(shiftsWithInfo);
    setPreviewMode(true);
    setAiLoading(false);
  } catch (err) {
    setAiError(err.message);
    setAiLoading(false);
  }
};

const handleApplySchedule = async () => {
  setAiLoading(true);
  
  try {
    saveToHistory(shifts);
    const monday = getMonday(currentWeek);
    
    // Determine if we're replacing (full schedule) or adding (fill empty)
    const clearExisting = window.confirm(
      'Do you want to REPLACE all existing shifts?\n\n' +
      'Click OK to replace everything\n' +
      'Click Cancel to keep existing shifts and add new ones'
    );
    
    const response = await fetch('http://127.0.0.1:5000/ai/apply-schedule', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        shifts: previewShifts.map(({ id, is_preview, staff_name, staff_role, area_name, ...shift }) => shift),
        clear_existing: clearExisting,
        week_start_date: monday.toISOString().split('T')[0]
      })
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to apply schedule');
    }
    
    // Clear preview mode and refresh data
    setPreviewMode(false);
    setPreviewShifts([]);
    fetchScheduleData();
    setAiLoading(false);
  } catch (err) {
    setAiError(err.message);
    setAiLoading(false);
  }
};

const handleCancelPreview = () => {
  setPreviewMode(false);
  setPreviewShifts([]);
  setAiError('');
};

const saveToHistory = (shifts) => {
  const newHistory = history.slice(0, historyIndex + 1);
  newHistory.push(JSON.parse(JSON.stringify(shifts))); 
  
  if (newHistory.length > 20) {
    newHistory.shift();
  } else {
    setHistoryIndex(historyIndex + 1);
  }
  
  setHistory(newHistory);
};

const handleUndo = () => {
  if (historyIndex > 0) {
    const previousState = history[historyIndex - 1];
    setHistoryIndex(historyIndex - 1);
    restoreShiftsFromHistory(previousState);
  }
};

const handleRedo = () => {
  if (historyIndex < history.length - 1) {
    const nextState = history[historyIndex + 1];
    setHistoryIndex(historyIndex + 1);
    restoreShiftsFromHistory(nextState);
  }
};

const restoreShiftsFromHistory = async (historicalShifts) => {
  try {
    const monday = getMonday(currentWeek);
    const weekEnd = new Date(monday);
    weekEnd.setDate(weekEnd.getDate() + 4);
    
    const currentWeekShifts = shifts.filter(shift => {
      const shiftDate = new Date(shift.date);
      return shiftDate >= monday && shiftDate <= weekEnd;
    });
    
    for (const shift of currentWeekShifts) {
      await fetch(`http://127.0.0.1:5000/shifts/${shift.id}`, {
        method: 'DELETE'
      });
    }
    
    // Recreate shifts from history
    for (const shift of historicalShifts) {
      const shiftDate = new Date(shift.date);
      if (shiftDate >= monday && shiftDate <= weekEnd) {
        await fetch('http://127.0.0.1:5000/shifts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            staff_id: shift.staff_id,
            area_id: shift.area_id,
            date: shift.date,
            start_time: shift.start_time,
            end_time: shift.end_time
          })
        });
      }
    }
    
    fetchScheduleData();
  } catch (err) {
    alert(`Error restoring: ${err.message}`);
  }
};

const handleClearSchedule = async () => {
  if (!window.confirm('⚠️ This will DELETE ALL shifts for this week. This cannot be undone. Continue?')) {
    return;
  }
  
  try {
    saveToHistory(shifts);
    
    const monday = getMonday(currentWeek);
    const mondayStr = monday.toISOString().split('T')[0];
    const fridayStr = new Date(monday.getFullYear(), monday.getMonth(), monday.getDate() + 4).toISOString().split('T')[0];
    
    const weekShifts = shifts.filter(shift => {
      return shift.date >= mondayStr && shift.date <= fridayStr;
    });
    
    for (const shift of weekShifts) {
      await fetch(`http://127.0.0.1:5000/shifts/${shift.id}`, {
        method: 'DELETE'
      });
    }
    
    fetchScheduleData();
  } catch (err) {
    alert(`Error clearing schedule: ${err.message}`);
  }
};

  return (
    <>
      {viewMode === 'week' ? (
        // WEEKLY VIEW
        <div className="schedule-container">
          <div className="schedule-header">
            <button onClick={goToPreviousWeek}>← Previous Week</button>
            <h2>Week of {currentWeek.toLocaleDateString()}</h2>
            <button onClick={goToNextWeek}>Next Week →</button>
            <button onClick={goToCurrentWeek}>Today</button>
        </div>

        <div className="schedule-actions">
          {/* History buttons */}
          <button 
            onClick={handleUndo}
            className="history-button"
            disabled={historyIndex <= 0}
            title="Undo last change"
          >
            ↶ Undo
          </button>
          <button 
            onClick={handleRedo}
            className="history-button"
            disabled={historyIndex >= history.length - 1}
            title="Redo last undone change"
          >
            ↷ Redo
          </button>
          
          <button onClick={() => handleAddShift()} className="add-shift-button">
            + Add Shift
          </button>
                  
            {/* AI Buttons */}
            <div className="ai-buttons">
              <button 
                onClick={handleFillEmptyShifts} 
                className="ai-fill-button"
                disabled={aiLoading || previewMode}
              >
                Fill Empty Shifts
              </button>
              <button 
                onClick={handleGenerateFullSchedule} 
                className="ai-generate-button"
                disabled={aiLoading || previewMode}
              >
                🔄 Generate Full Schedule
              </button>

              {/* Clear button */}
              <button 
                onClick={handleClearSchedule}
                className="clear-schedule-button"
                disabled={aiLoading || previewMode}
              >
                Clear Schedule
              </button>
            </div>
          </div>
                {previewMode && (
        <div className="preview-banner">
          <div className="preview-info">
            <strong>Preview Mode:</strong> {previewShifts.length} shifts suggested
            {aiError && <span className="preview-error">Error: {aiError}</span>}
          </div>
          <div className="preview-actions">
            <button 
              onClick={handleApplySchedule} 
              className="apply-button"
              disabled={aiLoading}
            >
              {aiLoading ? 'Applying...' : '✓ Apply Schedule'}
            </button>
            <button 
              onClick={handleCancelPreview} 
              className="cancel-preview-button"
              disabled={aiLoading}
            >
              ✗ Cancel
            </button>
          </div>
        </div>
      )}

      {aiLoading && (
        <div className="ai-loading">
          <div className="spinner"></div>
          <p>AI is generating schedule... This may take 10-20 seconds</p>
        </div>
      )}
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
                const coverageStatus = getCoverageStatus(area.id, date);
                return (
                  <div 
                    key={`${area.id}-${date.toISOString()}`} 
                    className={`schedule-cell ${coverageStatus.status}`}
                    onClick={() => switchToDayView(date)}
                    title={coverageStatus.warnings.join(', ')}
                  >
                    {areaShifts.length === 0 ? (
                      <div className="empty-cell">Not Staffed</div>
                    ) : (
                      <>
                      {areaShifts.map(shift => (
                        <div 
                          key={shift.id} 
                          className={`shift-card clickable-shift ${shift.is_preview ? 'preview-shift' : ''}`}
                          style={{ background: getStaffColor(shift.staff_id, shift.staff_role) }}
                          onClick={(e) => {
                            e.stopPropagation();
                            if (!shift.is_preview) {
                              handleEditShift(shift);
                            }
                          }}
                        >
                          {shift.is_preview && <span className="preview-badge">Preview</span>}
                          <div className="staff-name">{shift.staff_name}</div>
                          <div className="shift-time">{shift.start_time} - {shift.end_time}</div>
                        </div>
                      ))}
                      {coverageStatus.status === 'understaffed' && (
                        <div className="coverage-warning">
                          ⚠️ {coverageStatus.warnings[0]}
                          </div>
                      )}
                    </>
                  )}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  ) : (
    // DAILY VIEW
    <div className="schedule-container">
      <div className="schedule-header">
        <button onClick={switchToWeekView}>← Back to Week View</button>
        <h2>{selectedDate.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}</h2>
        <button onClick={() => handleAddShift(selectedDate)} className="add-shift-button">+ Add Shift</button>
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
                        className="timeline-shift-box clickable-shift"
                        style={{
                          top: `${top}px`,
                          height: `${height}px`,
                          background: getStaffColor(shift.staff_id, shift.staff_role)
                        }}
                        onClick={() => handleEditShift(shift)}
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
  )}
  

      <ShiftForm
        isOpen={showShiftForm}
        onClose={handleCloseForm}
        onSubmit={handleShiftSubmit}
        shift={selectedShift}
        areas={areas}
        staff={staff}
        selectedDate={selectedDateForForm}
      />
    </>
  );
}

export default ScheduleCalendar;