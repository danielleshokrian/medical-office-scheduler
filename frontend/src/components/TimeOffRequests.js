import React, { useState, useEffect } from 'react';
import TimeOffForm from './TimeOffForm';
import './TimeOffRequests.css';

function TimeOffRequests() {
  const [requests, setRequests] = useState([]);
  const [staff, setStaff] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState('all');
  const [showRequestForm, setShowRequestForm] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      const [requestsResponse, staffResponse] = await Promise.all([
        fetch('http://127.0.0.1:5000/time-off'),
        fetch('http://127.0.0.1:5000/staff')
      ]);

      if (!requestsResponse.ok) throw new Error('Failed to fetch time-off requests');
      if (!staffResponse.ok) throw new Error('Failed to fetch staff');

      const requestsData = await requestsResponse.json();
      const staffData = await staffResponse.json();

      setRequests(requestsData);
      setStaff(staffData);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (requestId, newStatus) => {
    try {
      const response = await fetch(`http://127.0.0.1:5000/time-off/${requestId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
      });

      if (!response.ok) throw new Error('Failed to update request');
      
      fetchData(); // Refresh list
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };

  const handleDelete = async (requestId) => {
    if (!window.confirm('Are you sure you want to delete this time-off request?')) {
      return;
    }

    try {
      const response = await fetch(`http://127.0.0.1:5000/time-off/${requestId}`, {
        method: 'DELETE'
      });

      if (!response.ok) throw new Error('Failed to delete request');
      
      fetchData(); // Refresh list
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };

  const getStatusBadgeClass = (status) => {
    const classes = {
      'pending': 'status-pending',
      'approved': 'status-approved',
      'denied': 'status-denied'
    };
    return classes[status] || '';
  };

  const filteredRequests = requests.filter(req => {
    if (statusFilter === 'all') return true;
    return req.status === statusFilter;
  });

  if (loading) return <div className="loading">Loading time-off requests...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div className="time-off-container">
      <div className="time-off-header">
        <h1>Time-Off Requests</h1>
        <button 
          onClick={() => setShowRequestForm(true)} 
          className="add-request-button"
        >
          + Submit Time-Off Request
        </button>
      </div>

      <div className="time-off-filters">
        <div className="filter-buttons">
          <button 
            className={statusFilter === 'all' ? 'active' : ''}
            onClick={() => setStatusFilter('all')}
          >
            All ({requests.length})
          </button>
          <button 
            className={statusFilter === 'pending' ? 'active' : ''}
            onClick={() => setStatusFilter('pending')}
          >
            Pending ({requests.filter(r => r.status === 'pending').length})
          </button>
          <button 
            className={statusFilter === 'approved' ? 'active' : ''}
            onClick={() => setStatusFilter('approved')}
          >
            Approved ({requests.filter(r => r.status === 'approved').length})
          </button>
          <button 
            className={statusFilter === 'denied' ? 'active' : ''}
            onClick={() => setStatusFilter('denied')}
          >
            Denied ({requests.filter(r => r.status === 'denied').length})
          </button>
        </div>
      </div>

      <div className="requests-list">
        {filteredRequests.length === 0 ? (
          <div className="no-requests">
            No {statusFilter !== 'all' ? statusFilter : ''} time-off requests found.
          </div>
        ) : (
          <table className="requests-table">
            <thead>
              <tr>
                <th>Staff Member</th>
                <th>Start Date</th>
                <th>End Date</th>
                <th>Days</th>
                <th>Reason</th>
                <th>Status</th>
                <th>Submitted</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredRequests.map(request => {
                const startDate = new Date(request.start_date);
                const endDate = new Date(request.end_date);
                const days = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24)) + 1;
                
                return (
                  <tr key={request.id}>
                    <td className="staff-name-cell">
                      <strong>{request.staff_name}</strong>
                    </td>
                    <td>{new Date(request.start_date).toLocaleDateString()}</td>
                    <td>{new Date(request.end_date).toLocaleDateString()}</td>
                    <td>{days} day{days !== 1 ? 's' : ''}</td>
                    <td>{request.reason || '-'}</td>
                    <td>
                      <span className={`status-badge ${getStatusBadgeClass(request.status)}`}>
                        {request.status}
                      </span>
                    </td>
                    <td>{new Date(request.created_at).toLocaleDateString()}</td>
                    <td className="actions-cell">
                      {request.status === 'pending' && (
                        <>
                          <button
                            className="approve-button"
                            onClick={() => handleStatusUpdate(request.id, 'approved')}
                          >
                            ✓ Approve
                          </button>
                          <button
                            className="deny-button"
                            onClick={() => handleStatusUpdate(request.id, 'denied')}
                          >
                            ✗ Deny
                          </button>
                        </>
                      )}
                      <button
                        className="delete-button"
                        onClick={() => handleDelete(request.id)}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      <TimeOffForm
        isOpen={showRequestForm}
        onClose={() => setShowRequestForm(false)}
        onSubmit={fetchData}
        staff={staff}
      />
    </div>
  );
}

export default TimeOffRequests;