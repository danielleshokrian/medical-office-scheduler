import React, { useState, useEffect } from 'react';
import { fetchWithAuth } from '../api.js';
import { API_ENDPOINTS } from '../config';
import './TimeOffForm.css';

function TimeOffForm({ isOpen, onClose, onSubmit, staff, fixedStaffId, defaultType = 'pto' }) {
  const [requestType, setRequestType] = useState(defaultType);
  const [formData, setFormData] = useState({
    staff_id: '',
    start_date: '',
    end_date: '',
    reason: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Sync type and staffId when modal opens or defaults change
  useEffect(() => {
    setRequestType(defaultType);
    setError('');
  }, [defaultType, isOpen]);

  useEffect(() => {
    if (fixedStaffId) {
      setFormData(prev => ({ ...prev, staff_id: String(fixedStaffId) }));
    }
  }, [fixedStaffId]);

  // For day_off, end_date always mirrors start_date
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => {
      const updated = { ...prev, [name]: value };
      if (requestType === 'day_off' && name === 'start_date') {
        updated.end_date = value;
      }
      return updated;
    });
    setError('');
  };

  const handleTypeChange = (type) => {
    setRequestType(type);
    setFormData(prev => ({ ...prev, start_date: '', end_date: '', reason: '' }));
    setError('');
  };

  const validateForm = () => {
    if (!formData.staff_id) return 'Please select a staff member';
    if (!formData.start_date) return requestType === 'day_off' ? 'Please select a date' : 'Please select a start date';
    if (requestType === 'pto' && !formData.end_date) return 'Please select an end date';
    if (requestType === 'pto') {
      const start = new Date(formData.start_date);
      const end = new Date(formData.end_date);
      if (end < start) return 'End date must be after start date';
    }
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const validationError = validateForm();
    if (validationError) { setError(validationError); return; }

    setLoading(true);
    setError('');

    const payload = {
      ...formData,
      end_date: requestType === 'day_off' ? formData.start_date : formData.end_date,
      request_type: requestType
    };

    try {
      const response = await fetchWithAuth(API_ENDPOINTS.TIME_OFF, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to submit request');
      }

      onSubmit();
      onClose();
      setFormData({ staff_id: fixedStaffId ? String(fixedStaffId) : '', start_date: '', end_date: '', reason: '' });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const isDayOff = requestType === 'day_off';

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content time-off-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{isDayOff ? 'Add Scheduled Day Off' : 'Submit PTO Request'}</h2>
          <button className="close-button" onClick={onClose}>×</button>
        </div>

        {/* Request type toggle */}
        <div className="request-type-toggle">
          <button
            type="button"
            className={`type-btn ${!isDayOff ? 'type-btn--active-pto' : ''}`}
            onClick={() => handleTypeChange('pto')}
          >
            PTO / Vacation
          </button>
          <button
            type="button"
            className={`type-btn ${isDayOff ? 'type-btn--active-dayoff' : ''}`}
            onClick={() => handleTypeChange('day_off')}
          >
            Scheduled Day Off
          </button>
        </div>

        {isDayOff && (
          <p className="type-description">
            For 4-day/week staff — select which day this week you will be off. Auto-approved, not counted as PTO.
          </p>
        )}

        <form onSubmit={handleSubmit}>
          {error && <div className="error-message">{error}</div>}

          {!fixedStaffId && (
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
                      {s.name} ({s.role}{s.days_per_week === 4 ? ', 4-day' : ''})
                    </option>
                  ))}
              </select>
            </div>
          )}

          {isDayOff ? (
            <div className="form-group">
              <label htmlFor="start_date">Day Off *</label>
              <input
                type="date"
                id="start_date"
                name="start_date"
                value={formData.start_date}
                onChange={handleChange}
                required
              />
            </div>
          ) : (
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="start_date">Start Date *</label>
                <input
                  type="date"
                  id="start_date"
                  name="start_date"
                  value={formData.start_date}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="end_date">End Date *</label>
                <input
                  type="date"
                  id="end_date"
                  name="end_date"
                  value={formData.end_date}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>
          )}

          <div className="form-group">
            <label htmlFor="reason">Note {isDayOff ? '(Optional)' : '(Optional)'}</label>
            <textarea
              id="reason"
              name="reason"
              value={formData.reason}
              onChange={handleChange}
              rows="2"
              placeholder={isDayOff ? 'e.g., Regular day off, flex day...' : 'e.g., Vacation, Medical, Personal...'}
            />
          </div>

          <div className="form-actions">
            <button type="button" className="cancel-button" onClick={onClose} disabled={loading}>
              Cancel
            </button>
            <button type="submit" className={`submit-button ${isDayOff ? 'submit-dayoff' : ''}`} disabled={loading}>
              {loading ? 'Submitting...' : isDayOff ? 'Add Day Off' : 'Submit Request'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default TimeOffForm;
