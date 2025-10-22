import React, { useState, useEffect } from 'react';
import StaffFormModal from './StaffFormModal.js';
import './StaffList.css';

function StaffList() {
  const [staff, setStaff] = useState([]);
  const [filteredStaff, setFilteredStaff] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [showStaffForm, setShowStaffForm] = useState(false);
  const [selectedStaff, setSelectedStaff] = useState(null);

  useEffect(() => {
    fetchStaff();
  }, []);

  useEffect(() => {
    filterStaff();
  }, [staff, searchTerm, roleFilter]);

  const fetchStaff = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://127.0.0.1:5000/staff?active=false'); // Get all staff including inactive
      if (!response.ok) throw new Error('Failed to fetch staff');
      const data = await response.json();
      setStaff(data);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const filterStaff = () => {
    let filtered = staff;

    if (searchTerm) {
      filtered = filtered.filter(s => 
        s.name.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (roleFilter !== 'all') {
      filtered = filtered.filter(s => s.role === roleFilter);
    }

    setFilteredStaff(filtered);
  };

  const handleAddStaff = () => {
    setSelectedStaff(null);
    setShowStaffForm(true);
  };

  const handleEditStaff = (staffMember) => {
    setSelectedStaff(staffMember);
    setShowStaffForm(true);
  };

  const handleCloseForm = () => {
    setShowStaffForm(false);
    setSelectedStaff(null);
  };

  const handleStaffSubmit = () => {
    fetchStaff(); 
  };

  const handleToggleActive = async (staffMember) => {
    try {
      const response = await fetch(`http://127.0.0.1:5000/staff/${staffMember.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: !staffMember.is_active })
      });

      if (!response.ok) throw new Error('Failed to update staff');
      fetchStaff();
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };

  const getRoleBadgeColor = (role) => {
    const colors = {
      'RN': '#3498db',
      'GI_Tech': '#2ecc71',
      'Scope_Tech': '#e74c3c'
    };
    return colors[role] || '#95a5a6';
  };

  if (loading) return <div className="loading">Loading staff...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div className="staff-list-container">
      <div className="staff-header">
        <h1>Staff Management</h1>
        <button onClick={handleAddStaff} className="add-staff-button">
          + Add Staff Member
        </button>
      </div>

      <div className="staff-filters">
        <input
          type="text"
          placeholder="Search by name..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="search-input"
        />

        <select 
          value={roleFilter} 
          onChange={(e) => setRoleFilter(e.target.value)}
          className="role-filter"
        >
          <option value="all">All Roles</option>
          <option value="RN">RN</option>
          <option value="GI_Tech">GI Tech</option>
          <option value="Scope_Tech">Scope Tech</option>
        </select>

        <div className="staff-count">
          Showing {filteredStaff.length} of {staff.length} staff members
        </div>
      </div>

      <div className="staff-grid">
        {filteredStaff.map(staffMember => (
          <div 
            key={staffMember.id} 
            className={`staff-card ${!staffMember.is_active ? 'inactive' : ''}`}
          >
            <div className="staff-card-header">
              <h3>{staffMember.name}</h3>
              <span 
                className="role-badge"
                style={{ background: getRoleBadgeColor(staffMember.role) }}
              >
                {staffMember.role}
              </span>
            </div>

            <div className="staff-details">
              <div className="detail-row">
                <span className="detail-label">Shift Length:</span>
                <span className="detail-value">{staffMember.shift_length} hours</span>
              </div>

              <div className="detail-row">
                <span className="detail-label">Days/Week:</span>
                <span className="detail-value">{staffMember.days_per_week} days</span>
              </div>

              {staffMember.start_time && (
                <div className="detail-row">
                  <span className="detail-label">Start Time:</span>
                  <span className="detail-value">{staffMember.start_time}</span>
                </div>
              )}

              {staffMember.required_day_off && (
                <div className="detail-row">
                  <span className="detail-label">Required Day Off:</span>
                  <span className="detail-value">{staffMember.required_day_off}</span>
                </div>
              )}

              {staffMember.is_per_diem && (
                <div className="per-diem-badge">Per Diem</div>
              )}

              {staffMember.area_restrictions && staffMember.area_restrictions !== '["Any"]' && (
                <div className="detail-row">
                  <span className="detail-label">Restrictions:</span>
                  <span className="detail-value">{staffMember.area_restrictions}</span>
                </div>
              )}
            </div>

            <div className="staff-actions">
              <button 
                onClick={() => handleEditStaff(staffMember)}
                className="edit-button"
              >
                Edit
              </button>
              <button 
                onClick={() => handleToggleActive(staffMember)}
                className={staffMember.is_active ? 'deactivate-button' : 'activate-button'}
              >
                {staffMember.is_active ? 'Deactivate' : 'Activate'}
              </button>
            </div>

            {!staffMember.is_active && (
              <div className="inactive-overlay">INACTIVE</div>
            )}
          </div>
        ))}
      </div>

      {filteredStaff.length === 0 && (
        <div className="no-results">
          No staff members found matching your filters.
        </div>
      )}

      <StaffFormModal
        isOpen={showStaffForm}
        onClose={handleCloseForm}
        onSubmit={handleStaffSubmit}
        staff={selectedStaff}
      />
    </div>
  );
}

export default StaffList;