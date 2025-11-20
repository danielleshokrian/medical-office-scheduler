import React, { useState, useEffect } from 'react';
import { fetchWithAuth } from '../api.js';
import './StaffFormModal.css';
import { API_ENDPOINTS } from '../config';

function StaffFormModal({ isOpen, onClose, onSubmit, staff }) {
  const [formData, setFormData] = useState({
    name: '',
    role: 'RN',
    shift_length: 10,
    days_per_week: 4,
    start_time: '',
    is_per_diem: false,
    allowed_areas: [],
    required_days_off: [],
    flexible_days_off: [],
    is_active: true
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [areas, setAreas] = useState([]);

  const handleDayToggle = (day, type) => {
  const field = type === 'required' ? 'required_days_off' : 'flexible_days_off';
  setFormData(prev => {
    const currentDays = prev[field];
    const newDays = currentDays.includes(day)
      ? currentDays.filter(d => d !== day)
      : [...currentDays, day];
    
    return {
      ...prev,
      [field]: newDays
    };
  });
};

const handleAreaToggle = (areaName) => {
  setFormData(prev => {
    const currentAreas = prev.allowed_areas;
    const newAreas = currentAreas.includes(areaName)
      ? currentAreas.filter(a => a !== areaName)
      : [...currentAreas, areaName];
    
    return {
      ...prev,
      allowed_areas: newAreas
    };
  });
};

const handleAllAreasToggle = () => {
  setFormData(prev => ({
    ...prev,
    allowed_areas: prev.allowed_areas.length === areas.length 
      ? [] 
      : areas.map(a => a.name)
  }));
};


useEffect(() => {
  if (isOpen) {
    fetchAreas();
  }
}, [isOpen]);
const fetchAreas = async () => {
  try {
    const response = await fetchWithAuth(API_ENDPOINTS.AREAS);
    if (response.ok) {
      const data = await response.json();
      setAreas(data);
    }
  } catch (err) {
    console.error('Failed to fetch areas:', err);
  }
};

useEffect(() => {
  if (staff && areas.length > 0) {
    const parseJsonField = (field) => {
      if (!field) return [];
      if (field === 'null') return [];
      
      // Convert to array
      if (field.startsWith('{') && field.endsWith('}')) {
        const content = field.slice(1, -1);
        return content ? content.split(',').map(s => s.trim()) : [];
      }
      
      // Try parsing as JSON
      try {
        const parsed = JSON.parse(field);

        if (parsed.includes("Any")) {
          return areas.map(a => a.name);  
        }
        
        return parsed;
      } catch (e) {
        console.error('Failed to parse:', field, e);
        return [];
      }
    };
    
    setFormData({
      name: staff.name,
      role: staff.role,
      shift_length: staff.shift_length,
      days_per_week: staff.days_per_week,
      start_time: staff.start_time || '',
      is_per_diem: staff.is_per_diem,
      allowed_areas: parseJsonField(staff.area_restrictions),        // CHANGED
      required_days_off: parseJsonField(staff.required_days_off),    // CHANGED
      flexible_days_off: parseJsonField(staff.flexible_days_off),    // CHANGED
      is_active: staff.is_active
    });
  } else {
    setFormData({
      name: '',
      role: 'RN',
      shift_length: 10,
      days_per_week: 4,
      start_time: '',
      is_per_diem: false,
      allowed_areas: [],
      required_days_off: [],
      flexible_days_off: [],
      is_active: true
    });
  }
}, [staff, isOpen, areas]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    setError('');
  };

  const validateForm = () => {
    if (!formData.name.trim()) return 'Name is required';
    if (!formData.role) return 'Role is required';
    if (!formData.shift_length) return 'Shift length is required';
    if (!formData.days_per_week) return 'Days per week is required';
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
         const url = staff
        ? API_ENDPOINTS.STAFF_BY_ID(staff.id)
        : API_ENDPOINTS.STAFF;
      
      const method = staff ? 'PUT' : 'POST';

      const payload = {
        name: formData.name,
        role: formData.role,
        shift_length: formData.shift_length,
        days_per_week: formData.days_per_week,
        start_time: formData.start_time || null,
        is_per_diem: formData.is_per_diem,
        area_restrictions: formData.allowed_areas.length > 0 
          ? JSON.stringify(formData.allowed_areas) 
          : JSON.stringify(["Any"]),
        required_days_off: formData.required_days_off.length > 0 ? JSON.stringify(formData.required_days_off) : null,
        flexible_days_off: formData.flexible_days_off.length > 0 ? JSON.stringify(formData.flexible_days_off) : null,
        is_active: formData.is_active
      };

      const response = await fetchWithAuth(url, {
        method: method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to save staff');
      }

      onSubmit();
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content staff-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{staff ? 'Edit Staff Member' : 'Add New Staff Member'}</h2>
          <button className="close-button" onClick={onClose}>×</button>
        </div>

        <form onSubmit={handleSubmit}>
          {error && <div className="error-message">{error}</div>}

          <div className="form-group">
            <label htmlFor="name">Name *</label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="role">Role *</label>
              <select
                id="role"
                name="role"
                value={formData.role}
                onChange={handleChange}
                required
              >
                <option value="RN">RN</option>
                <option value="GI_Tech">GI Tech</option>
                <option value="Scope_Tech">Scope Tech</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="shift_length">Shift Length (hours) *</label>
              <select
                id="shift_length"
                name="shift_length"
                value={formData.shift_length}
                onChange={handleChange}
                required
              >
                <option value={8}>8 hours</option>
                <option value={10}>10 hours</option>
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="days_per_week">Days per Week *</label>
              <select
                id="days_per_week"
                name="days_per_week"
                value={formData.days_per_week}
                onChange={handleChange}
                required
              >
                <option value={3}>3 days</option>
                <option value={4}>4 days</option>
                <option value={5}>5 days</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="start_time">Preferred Start Time</label>
              <select
                id="start_time"
                name="start_time"
                value={formData.start_time}
                onChange={handleChange}
              >
                <option value="">No preference</option>
                <option value="06:15">6:15 AM</option>
                <option value="06:30">6:30 AM</option>
                <option value="07:00">7:00 AM</option>
                <option value="07:30">7:30 AM</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label>Required Days Off (ALWAYS off these days)</label>
            <div className="days-checkbox-group">
              {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'].map(day => (
                <label key={day} className="day-checkbox">
                  <input
                    type="checkbox"
                    checked={formData.required_days_off.includes(day)}
                    onChange={() => handleDayToggle(day, 'required')}
                  />
                  {day}
                </label>
              ))}
            </div>
            <small>Staff member will NEVER work on these days</small>
          </div>

          <div className="form-group">
            <label>Flexible Days Off (must be off AT LEAST ONE)</label>
            <div className="days-checkbox-group">
              {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'].map(day => (
                <label key={day} className="day-checkbox">
                  <input
                    type="checkbox"
                    checked={formData.flexible_days_off.includes(day)}
                    onChange={() => handleDayToggle(day, 'flexible')}
                  />
                  {day}
                </label>
              ))}
            </div>
            <small>Staff member must have at least ONE of these days off each week</small>
          </div>

          <div className="form-group">
            <label>Allowed Areas</label>
            <div className="areas-checkbox-group">
              <label className="area-checkbox all-areas">
                <input
                  type="checkbox"
                  checked={formData.allowed_areas.length === areas.length}
                  onChange={handleAllAreasToggle}
                />
                <strong>All Areas (Any)</strong>
              </label>
              
              {areas.map(area => (
                <label key={area.id} className="area-checkbox">
                  <input
                    type="checkbox"
                    checked={formData.allowed_areas.includes(area.name)}
                    onChange={() => handleAreaToggle(area.name)}
                  />
                  {area.name}
                </label>
              ))}
            </div>
          </div>

          <div className="form-group checkbox-group">
            <label>
              <input
                type="checkbox"
                name="is_per_diem"
                checked={formData.is_per_diem}
                onChange={handleChange}
              />
              Per Diem Staff
            </label>
          </div>

          <div className="form-actions">
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
              {loading ? 'Saving...' : (staff ? 'Update Staff' : 'Add Staff')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default StaffFormModal;