import React, { useState } from 'react';
import { fetchWithAuth } from '../api.js';
import './TimeOffForm.css';

function TimeOffForm({ isOpen, onClose, onSubmit, staff }) {
  const [formData, setFormData] = useState({
    staff_id: '',
    start_date: '',
    end_date: '',
    reason: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    setError('');
  };

  const validateForm = () => {
    if (!formData.staff_id) return 'Please select a staff member';
    if (!formData.start_date) return 'Please select a start date';
    if (!formData.end_date) return 'Please select an end date';
    
    const start = new Date(formData.start_date);
    const end = new Date(formData.end_date);
    
    if (end < start) {
      return 'End date must be after start date';
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
      const response = await fetchWithAuth('http://127.0.0.1:5001/time-off', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to submit request');
      }

      onSubmit();
      onClose();
      
      // Reset form
      setFormData({
        staff_id: '',
        start_date: '',
        end_date: '',
        reason: ''
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content time-off-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Submit Time-Off Request</h2>
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

          <div className="form-group">
            <label htmlFor="reason">Reason (Optional)</label>
            <textarea
              id="reason"
              name="reason"
              value={formData.reason}
              onChange={handleChange}
              rows="3"
              placeholder="e.g., Vacation, Personal, Medical..."
            />
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
              {loading ? 'Submitting...' : 'Submit Request'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default TimeOffForm;