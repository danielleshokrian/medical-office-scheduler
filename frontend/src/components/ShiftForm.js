import React, { useState, useEffect } from 'react';
import './ShiftForm.css';

function ShiftForm({ isOpen, onClose, onSubmit, shift, areas, staff, selectedDate }) {
  const [formData, setFormData] = useState({
    staff_id: '',
    area_id: '',
    date: '',
    start_time: '',
    end_time: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [overrideValidation, setOverrideValidation] = useState(false);

  useEffect(() => {
    if (shift) {
      setFormData({
        staff_id: shift.staff_id,
        area_id: shift.area_id,
        date: shift.date,
        start_time: shift.start_time,
        end_time: shift.end_time
      });
    } else if (selectedDate) {
      setFormData({
        staff_id: '',
        area_id: '',
        date: selectedDate.toISOString().split('T')[0],
        start_time: '',
        end_time: ''
      });
    }
  }, [shift, selectedDate]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  
  // Auto-calculate end time based on staff and start time
  if (name === 'staff_id' || name === 'start_time') {
    const staffId = name === 'staff_id' ? value : formData.staff_id;
    const startTime = name === 'start_time' ? value : formData.start_time;
    
    if (staffId && startTime) {
      const selectedStaff = staff.find(s => s.id === parseInt(staffId));
      if (selectedStaff && selectedStaff.shift_length) {
        const calculatedEndTime = calculateEndTime(startTime, selectedStaff.shift_length);
        setFormData(prev => ({
          ...prev,
          [name]: value,
          end_time: calculatedEndTime
        }));
      }
    }
  }
  
  setError('');
};

const calculateEndTime = (startTime, shiftLength) => {
  if (!startTime) return '';
  
  const [hours, minutes] = startTime.split(':').map(Number);
  const startDate = new Date();
  startDate.setHours(hours, minutes, 0, 0);
  
  startDate.setHours(startDate.getHours() + shiftLength);
  
  const endHours = startDate.getHours().toString().padStart(2, '0');
  const endMinutes = startDate.getMinutes().toString().padStart(2, '0');
  
  return `${endHours}:${endMinutes}`;
};

  const validateForm = () => {
    if (!formData.staff_id) return 'Please select a staff member';
    if (!formData.area_id) return 'Please select an area';
    if (!formData.date) return 'Please select a date';
    if (!formData.start_time) return 'Please select a start time';
    if (!formData.end_time) return 'Please select an end time';
    
    if (formData.start_time >= formData.end_time) {
      return 'End time must be after start time';
    }
    
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    setError('');

    try {
      const url = shift 
        ? `http://127.0.0.1:5000/shifts/${shift.id}`
        : 'http://127.0.0.1:5000/shifts';
      
      const method = shift ? 'PUT' : 'POST';

      const payload = {
      ...formData,
      override_validation: overrideValidation
    };
      
      const response = await fetch(url, {
        method: method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        const errorData = await response.json();

      // If validation error, show option to override for exceptions
      if (response.status === 400 && !overrideValidation) {
        const shouldOverride = window.confirm(
          `Validation Error: ${errorData.error}\n\nDo you want to override validation and save anyway? This will bypass all scheduling rules.`
        );
        
        if (shouldOverride) {
          setOverrideValidation(true);
          // Resubmit immediately with override flag
          const retryResponse = await fetch(url, {
            method: method,
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              ...formData,
              override_validation: true
            })
          });
          
          if (retryResponse.ok) {
            const data = await retryResponse.json();
            onSubmit(data);
            onClose();
            return;
          }
        }
        
        setLoading(false);
        return;
      }
      
      throw new Error(errorData.error || 'Failed to save shift');
    }

      const data = await response.json();
      onSubmit(data);
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!shift) return;
    
    if (!window.confirm('Are you sure you want to delete this shift?')) {
      return;
    }

    setLoading(true);
    
    try {
      const response = await fetch(`http://127.0.0.1:5000/shifts/${shift.id}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error('Failed to delete shift');
      }

      onSubmit({ deleted: true, id: shift.id });
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const startTimes = ['06:15', '06:30', '07:00', '07:30'];
  
  const generateEndTimes = () => {
    const times = [];
    for (let hour = 6; hour <= 18; hour++) {
      for (let minute of ['00', '15', '30', '45']) {
        const time = `${hour.toString().padStart(2, '0')}:${minute}`;
        times.push(time);
      }
    }
    return times;
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{shift ? 'Edit Shift' : 'Add New Shift'}</h2>
          <button className="close-button" onClick={onClose}>×</button>
        </div>

        <form onSubmit={handleSubmit}>
          {error && <div className="error-message">{error}</div>}

          <div className="form-group">
            <label htmlFor="staff_id">Staff Member *</label>
            <select
              id="staff_id"
              name="staff_id"
              value={formData.staff_id}
              onChange={handleChange}
              required
            >
              <option value="">Select Staff Member</option>
              {staff
                .filter(s => s.is_active)
                .sort((a, b) => a.name.localeCompare(b.name))
                .map(s => (
                  <option key={s.id} value={s.id}>
                    {s.name} - {s.role}
                  </option>
                ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="area_id">Area *</label>
            <select
              id="area_id"
              name="area_id"
              value={formData.area_id}
              onChange={handleChange}
              required
            >
              <option value="">Select Area</option>
              {areas.map(area => (
                <option key={area.id} value={area.id}>
                  {area.name}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="date">Date *</label>
            <input
              type="date"
              id="date"
              name="date"
              value={formData.date}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="start_time">Start Time *</label>
              <select
                id="start_time"
                name="start_time"
                value={formData.start_time}
                onChange={handleChange}
                required
              >
                <option value="">Select Start Time</option>
                {startTimes.map(time => (
                  <option key={time} value={time}>{time}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="end_time">End Time *</label>
              <select
                id="end_time"
                name="end_time"
                value={formData.end_time}
                onChange={handleChange}
                required
              >
                <option value="">Select End Time</option>
                {generateEndTimes().map(time => (
                  <option key={time} value={time}>{time}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-actions">
            {shift && (
              <button 
                type="button" 
                className="delete-button"
                onClick={handleDelete}
                disabled={loading}
              >
                Delete Shift
              </button>
            )}
            <div className="right-buttons">
              <button 
                type="button" 
                className="cancel-button"
                onClick={onClose}
                disabled={loading}
              >
                Cancel
              </button>
              <button 
                type="submit" 
                className="submit-button"
                disabled={loading}
              >
                {loading ? 'Saving...' : (shift ? 'Update Shift' : 'Add Shift')}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}

export default ShiftForm;