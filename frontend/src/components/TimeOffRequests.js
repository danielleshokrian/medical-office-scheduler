import React, { useState, useEffect, useCallback } from 'react';
import TimeOffForm from './TimeOffForm';
import { fetchWithAuth } from '../api.js';
import { API_ENDPOINTS } from '../config';
import './TimeOffRequests.css';
import { useAuth } from '../AuthContext';

function getMonday(date) {
  const d = new Date(date);
  const day = d.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  d.setDate(d.getDate() + diff);
  d.setHours(0, 0, 0, 0);
  return d;
}

function addWeeks(date, n) {
  const d = new Date(date);
  d.setDate(d.getDate() + n * 7);
  return d;
}

function formatWeekLabel(mondayDate) {
  const friday = new Date(mondayDate);
  friday.setDate(friday.getDate() + 4);
  const opts = { month: 'short', day: 'numeric' };
  return `${mondayDate.toLocaleDateString('en-US', opts)} – ${friday.toLocaleDateString('en-US', opts)}`;
}

function isSameWeek(date, monday) {
  const d = getMonday(new Date(date + 'T12:00:00'));
  return d.toISOString().slice(0, 10) === monday.toISOString().slice(0, 10);
}

function TimeOffRequests() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'nurse_admin';

  const [ptoRequests, setPtoRequests] = useState([]);
  const [dayOffRequests, setDayOffRequests] = useState([]);
  const [staff, setStaff] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // PTO filters
  const [ptoFilter, setPtoFilter] = useState('all');

  // Day-off week navigation
  const [viewedWeek, setViewedWeek] = useState(() => getMonday(new Date()));
  const [showPast, setShowPast] = useState(false);
  const [staffFilter, setStaffFilter] = useState('all');

  // Form
  const [showForm, setShowForm] = useState(false);
  const [defaultFormType, setDefaultFormType] = useState('pto');

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [requestsRes, staffRes] = await Promise.all([
        fetchWithAuth(API_ENDPOINTS.TIME_OFF),
        isAdmin
          ? fetchWithAuth(API_ENDPOINTS.STAFF)
          : Promise.resolve({ ok: true, json: async () => [] })
      ]);
      if (!requestsRes.ok) throw new Error('Failed to fetch time-off requests');
      if (!staffRes.ok) throw new Error('Failed to fetch staff');

      const all = await requestsRes.json();
      const staffData = await staffRes.json();

      setPtoRequests(all.filter(r => r.request_type !== 'day_off'));
      setDayOffRequests(all.filter(r => r.request_type === 'day_off'));
      setStaff(staffData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [isAdmin]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleStatusUpdate = async (requestId, newStatus) => {
    try {
      const response = await fetchWithAuth(API_ENDPOINTS.TIME_OFF_BY_ID(requestId), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
      });
      if (!response.ok) throw new Error('Failed to update request');
      fetchData();
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };

  const handleDelete = async (requestId) => {
    if (!window.confirm('Delete this request?')) return;
    try {
      const response = await fetchWithAuth(API_ENDPOINTS.TIME_OFF_BY_ID(requestId), { method: 'DELETE' });
      if (!response.ok) throw new Error('Failed to delete request');
      fetchData();
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };

  const openForm = (type) => { setDefaultFormType(type); setShowForm(true); };

  const statusBadgeClass = (status) =>
    ({ pending: 'status-pending', approved: 'status-approved', denied: 'status-denied' }[status] || '');

  // ── Day-off derived state ──────────────────────────────
  const currentWeekMonday = getMonday(new Date());
  const isPastWeek = viewedWeek < currentWeekMonday;

  // All day-off requests filtered by staff
  const filteredDayOffs = dayOffRequests.filter(r =>
    staffFilter === 'all' || String(r.staff_id) === staffFilter
  );

  // Requests visible in the currently viewed week
  const weekRequests = filteredDayOffs.filter(r => isSameWeek(r.start_date, viewedWeek));

  // Can we navigate backward?
  const canGoPrev = showPast || viewedWeek > currentWeekMonday;

  // ── PTO derived state ─────────────────────────────────
  const filteredPto = ptoRequests.filter(r => ptoFilter === 'all' || r.status === ptoFilter);

  if (loading) return <div className="loading">Loading...</div>;
  if (error) return <div className="error">Error: {error}</div>;
  if (!isAdmin && !user?.staff_id) return (
    <div className="error" style={{ margin: '2rem auto', maxWidth: 480, textAlign: 'center' }}>
      Your account is not linked to a staff record yet.<br />
      Please contact your nurse administrator to get set up.
    </div>
  );

  return (
    <div className="time-off-container">

      {/* ── SECTION 1: Scheduled Days Off ── */}
      <div className="tor-section">
        <div className="tor-section-header">
          <div>
            <h2>Scheduled Days Off</h2>
            <p className="tor-section-subtitle">
              Regular weekly days off for 4-day/week staff — requires admin approval, not counted as PTO.
            </p>
          </div>
          <button className="add-request-button day-off-button" onClick={() => openForm('day_off')}>
            + Add Scheduled Day Off
          </button>
        </div>

        {/* Controls row */}
        <div className="dayoff-controls">
          {/* Staff filter (admin only) */}
          {isAdmin && (
            <select
              className="dayoff-staff-filter"
              value={staffFilter}
              onChange={e => setStaffFilter(e.target.value)}
            >
              <option value="all">All staff</option>
              {staff
                .filter(s => s.is_active)
                .sort((a, b) => a.name.localeCompare(b.name))
                .map(s => (
                  <option key={s.id} value={String(s.id)}>{s.name}</option>
                ))}
            </select>
          )}

          {/* Week navigator */}
          <div className="week-nav">
            <button
              className="week-nav-btn"
              onClick={() => setViewedWeek(w => addWeeks(w, -1))}
              disabled={!canGoPrev}
              title="Previous week"
            >
              &#8249;
            </button>

            <span className="week-nav-label">
              {isPastWeek && <span className="past-tag">Past</span>}
              {formatWeekLabel(viewedWeek)}
              <span className="week-count">
                {weekRequests.length} request{weekRequests.length !== 1 ? 's' : ''}
              </span>
            </span>

            <button
              className="week-nav-btn"
              onClick={() => setViewedWeek(w => addWeeks(w, 1))}
              title="Next week"
            >
              &#8250;
            </button>

            {viewedWeek.toISOString().slice(0,10) !== currentWeekMonday.toISOString().slice(0,10) && (
              <button
                className="week-today-btn"
                onClick={() => setViewedWeek(currentWeekMonday)}
              >
                Today
              </button>
            )}
          </div>

          {/* Past toggle */}
          <label className="past-toggle">
            <input
              type="checkbox"
              checked={showPast}
              onChange={e => {
                setShowPast(e.target.checked);
                if (!e.target.checked && viewedWeek < currentWeekMonday) {
                  setViewedWeek(currentWeekMonday);
                }
              }}
            />
            Show past weeks
          </label>
        </div>

        {/* Week requests */}
        {weekRequests.length === 0 ? (
          <div className="no-requests">No scheduled days off for this week.</div>
        ) : (
          <div className="week-block">
            {weekRequests
              .sort((a, b) => new Date(a.start_date) - new Date(b.start_date))
              .map(req => (
                <div key={req.id} className="dayoff-row">
                  <div className="dayoff-info">
                    {isAdmin && <span className="dayoff-staff">{req.staff_name}</span>}
                    <span className="dayoff-date">
                      {new Date(req.start_date + 'T12:00:00').toLocaleDateString('en-US', {
                        weekday: 'long', month: 'short', day: 'numeric'
                      })}
                    </span>
                    {req.reason && <span className="dayoff-reason">{req.reason}</span>}
                  </div>
                  <div className="dayoff-actions">
                    <span className={`status-badge ${statusBadgeClass(req.status)}`}>
                      {req.status}
                    </span>
                    {isAdmin && req.status === 'pending' && (
                      <>
                        <button className="approve-button" onClick={() => handleStatusUpdate(req.id, 'approved')}>
                          Approve
                        </button>
                        <button className="deny-button" onClick={() => handleStatusUpdate(req.id, 'denied')}>
                          Deny
                        </button>
                      </>
                    )}
                    <button
                      className="delete-button"
                      onClick={() => handleDelete(req.id)}
                      disabled={!isAdmin && req.status !== 'pending'}
                    >
                      Remove
                    </button>
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>

      {/* ── SECTION 2: PTO / Vacation Requests ── */}
      <div className="tor-section">
        <div className="tor-section-header">
          <div>
            <h2>PTO / Vacation Requests</h2>
            <p className="tor-section-subtitle">
              Vacation, sick days, and other time off that requires{isAdmin ? ' your ' : ' admin '}approval.
            </p>
          </div>
          <button className="add-request-button" onClick={() => openForm('pto')}>
            + Submit PTO Request
          </button>
        </div>

        <div className="time-off-filters">
          <div className="filter-buttons">
            {['all', 'pending', 'approved', 'denied'].map(f => (
              <button
                key={f}
                className={ptoFilter === f ? 'active' : ''}
                onClick={() => setPtoFilter(f)}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
                {' '}({f === 'all' ? ptoRequests.length : ptoRequests.filter(r => r.status === f).length})
              </button>
            ))}
          </div>
        </div>

        {filteredPto.length === 0 ? (
          <div className="no-requests">
            No {ptoFilter !== 'all' ? ptoFilter + ' ' : ''}PTO requests found.
          </div>
        ) : (
          <table className="requests-table">
            <thead>
              <tr>
                {isAdmin && <th>Staff Member</th>}
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
              {filteredPto.map(request => {
                const start = new Date(request.start_date + 'T12:00:00');
                const end   = new Date(request.end_date   + 'T12:00:00');
                const days  = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1;
                return (
                  <tr key={request.id}>
                    {isAdmin && <td><strong>{request.staff_name}</strong></td>}
                    <td>{start.toLocaleDateString()}</td>
                    <td>{end.toLocaleDateString()}</td>
                    <td>{days} day{days !== 1 ? 's' : ''}</td>
                    <td>{request.reason || '-'}</td>
                    <td>
                      <span className={`status-badge ${statusBadgeClass(request.status)}`}>
                        {request.status}
                      </span>
                    </td>
                    <td>{new Date(request.created_at).toLocaleDateString()}</td>
                    <td className="actions-cell">
                      {isAdmin && request.status === 'pending' && (
                        <>
                          <button className="approve-button" onClick={() => handleStatusUpdate(request.id, 'approved')}>
                            Approve
                          </button>
                          <button className="deny-button" onClick={() => handleStatusUpdate(request.id, 'denied')}>
                            Deny
                          </button>
                        </>
                      )}
                      <button
                        className="delete-button"
                        onClick={() => handleDelete(request.id)}
                        disabled={!isAdmin && request.status !== 'pending'}
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
        isOpen={showForm}
        onClose={() => setShowForm(false)}
        onSubmit={fetchData}
        staff={staff}
        fixedStaffId={!isAdmin ? user?.staff_id : null}
        defaultType={defaultFormType}
      />
    </div>
  );
}

export default TimeOffRequests;
