import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api';
import {
  FileText,
  Activity,
  Plus,
  Clock,
  Calendar,
  CheckCircle,
  AlertCircle,
  MapPin,
  Tag,
  Edit2,
  Trash2,
  UserCheck
} from 'lucide-react';

export const AssignmentsPage = () => {
  const { isAdmin } = useAuth();
  const [activeSubTab, setActiveSubTab] = useState('assignments'); // 'assignments' or 'activities'
  const [assignments, setAssignments] = useState([]);
  const [activities, setActivities] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);

  // Modals
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [showActModal, setShowActModal] = useState(false);

  // Assignment Form State
  const [assignSubjectId, setAssignSubjectId] = useState('');
  const [assignTitle, setAssignTitle] = useState('');
  const [assignDesc, setAssignDesc] = useState('');
  const [assignDeadline, setAssignDeadline] = useState('');
  const [assignPriority, setAssignPriority] = useState('medium');
  const [assignMaxScore, setAssignMaxScore] = useState(20);

  // Activity Form State
  const [actTitle, setActTitle] = useState('');
  const [actType, setActType] = useState('workshop');
  const [actDesc, setActDesc] = useState('');
  const [actDate, setActDate] = useState('');
  const [actVenue, setActVenue] = useState('Auditorium / Online');
  const [actOrganizer, setActOrganizer] = useState('Department of CSE');
  const [actPriority, setActPriority] = useState('medium');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [assignRes, actRes, subRes] = await Promise.all([
        api.get('/assignments'),
        api.get('/activities'),
        api.get('/admin/subjects').catch(() => ({ subjects: [] }))
      ]);

      if (assignRes.success) setAssignments(assignRes.assignments || []);
      if (actRes.success) setActivities(actRes.activities || []);
      if (subRes.success && subRes.subjects) {
        setSubjects(subRes.subjects);
        if (subRes.subjects.length > 0 && !assignSubjectId) {
          setAssignSubjectId(subRes.subjects[0].id);
        }
      }
    } catch (err) {
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStatus = async (assignId, currentStatus) => {
    const cycle = {
      pending: 'in_progress',
      in_progress: 'submitted',
      submitted: 'completed',
      completed: 'pending'
    };
    const nextStatus = cycle[currentStatus] || 'in_progress';

    try {
      await api.post(`/assignments/${assignId}/status`, { status: nextStatus });
      fetchData();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleCreateAssignment = async (e) => {
    e.preventDefault();
    try {
      await api.post('/assignments', {
        subject_id: Number(assignSubjectId),
        title: assignTitle,
        description: assignDesc,
        deadline: assignDeadline,
        priority: assignPriority,
        max_score: Number(assignMaxScore)
      });
      setShowAssignModal(false);
      setAssignTitle('');
      setAssignDesc('');
      setAssignDeadline('');
      fetchData();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleCreateActivity = async (e) => {
    e.preventDefault();
    try {
      await api.post('/activities', {
        title: actTitle,
        activity_type: actType,
        description: actDesc,
        activity_date: actDate,
        venue: actVenue,
        organizer: actOrganizer,
        priority: actPriority
      });
      setShowActModal(false);
      setActTitle('');
      setActDesc('');
      setActDate('');
      fetchData();
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
        <div>
          <h2 style={{ fontSize: '22px', fontWeight: 800, color: 'var(--slate-900)' }}>
            Course Assignments & Academic Activities
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--slate-500)', marginTop: '2px' }}>
            Track submissions, manage priorities, and explore campus symposiums and workshops.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          {isAdmin && (
            <>
              <button onClick={() => setShowAssignModal(true)} className="btn btn-primary btn-sm">
                <Plus size={16} />
                <span>Create Assignment</span>
              </button>
              <button onClick={() => setShowActModal(true)} className="btn btn-secondary btn-sm">
                <Plus size={16} />
                <span>Add Activity</span>
              </button>
            </>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '10px', borderBottom: '1px solid var(--slate-200)', paddingBottom: '12px' }}>
        <button
          onClick={() => setActiveSubTab('assignments')}
          className="btn btn-sm"
          style={{
            background: activeSubTab === 'assignments' ? 'var(--primary-700)' : 'var(--white)',
            color: activeSubTab === 'assignments' ? 'white' : 'var(--slate-700)',
            border: '1px solid var(--slate-200)'
          }}
        >
          <FileText size={16} />
          <span>Course Assignments ({assignments.length})</span>
        </button>
        <button
          onClick={() => setActiveSubTab('activities')}
          className="btn btn-sm"
          style={{
            background: activeSubTab === 'activities' ? 'var(--primary-700)' : 'var(--white)',
            color: activeSubTab === 'activities' ? 'white' : 'var(--slate-700)',
            border: '1px solid var(--slate-200)'
          }}
        >
          <Activity size={16} />
          <span>Workshops & Activities ({activities.length})</span>
        </button>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px' }}>Loading records...</div>
      ) : activeSubTab === 'assignments' ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {assignments.length === 0 ? (
            <div className="glass-card" style={{ padding: '40px', textAlign: 'center', color: 'var(--slate-500)' }}>
              No active assignments on record.
            </div>
          ) : (
            assignments.map((a) => {
              const status = a.student_status || 'pending';
              const isOverdue = a.is_overdue;

              return (
                <div
                  key={a.id}
                  className="glass-card glass-card-hover"
                  style={{
                    padding: '20px 24px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    flexWrap: 'wrap',
                    gap: '16px',
                    borderLeft: `5px solid ${isOverdue ? 'var(--danger)' : a.priority === 'high' ? 'var(--warning)' : 'var(--primary-500)'}`
                  }}
                >
                  <div style={{ minWidth: '300px', flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                      <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--primary-700)', background: 'var(--primary-50)', padding: '2px 8px', borderRadius: '4px' }}>
                        {a.subject_code}
                      </span>
                      <span className={`badge ${a.priority === 'high' ? 'badge-danger' : a.priority === 'medium' ? 'badge-warning' : 'badge-info'}`}>
                        {a.priority} Priority
                      </span>
                      {isOverdue && <span className="badge badge-danger">Overdue</span>}
                    </div>

                    <h3 style={{ fontSize: '17px', fontWeight: 800, color: 'var(--slate-900)' }}>
                      {a.title}
                    </h3>
                    <p style={{ fontSize: '13px', color: 'var(--slate-600)', marginTop: '4px', lineHeight: '1.4' }}>
                      {a.description}
                    </p>

                    <div style={{ display: 'flex', gap: '16px', fontSize: '12px', color: 'var(--slate-500)', marginTop: '8px' }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Clock size={14} />
                        Deadline: {a.deadline ? new Date(a.deadline).toLocaleString() : 'N/A'}
                      </span>
                      <span>Max Score: {a.max_score} marks</span>
                    </div>
                  </div>

                  {/* Student Status Toggle Button */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <button
                      onClick={() => handleUpdateStatus(a.id, status)}
                      className={`btn btn-sm ${
                        status === 'completed' || status === 'submitted' ? 'btn-secondary' : 'btn-primary'
                      }`}
                      style={{
                        padding: '8px 14px',
                        textTransform: 'capitalize',
                        background:
                          status === 'completed' ? 'var(--success-bg)' :
                          status === 'submitted' ? 'var(--info-bg)' :
                          status === 'in_progress' ? 'var(--warning-bg)' : undefined,
                        color:
                          status === 'completed' ? '#065f46' :
                          status === 'submitted' ? '#075985' :
                          status === 'in_progress' ? '#92400e' : undefined,
                        border:
                          status === 'completed' ? '1px solid #a7f3d0' :
                          status === 'submitted' ? '1px solid #bae6fd' :
                          status === 'in_progress' ? '1px solid #fde68a' : undefined
                      }}
                      title="Click to advance status: Pending -> In Progress -> Submitted -> Completed"
                    >
                      <UserCheck size={14} />
                      <span>Status: {status.replace('_', ' ')}</span>
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      ) : (
        /* Academic Activities Grid */
        <div className="grid-2">
          {activities.length === 0 ? (
            <div className="glass-card" style={{ padding: '40px', textAlign: 'center', color: 'var(--slate-500)', gridColumn: 'span 2' }}>
              No academic activities currently scheduled.
            </div>
          ) : (
            activities.map((act) => (
              <div key={act.id} className="glass-card glass-card-hover" style={{ padding: '22px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <span className="badge badge-primary" style={{ textTransform: 'uppercase' }}>
                    {act.activity_type.replace('_', ' ')}
                  </span>
                  <span className={`badge ${act.priority === 'high' ? 'badge-danger' : 'badge-info'}`}>
                    {act.priority}
                  </span>
                </div>

                <h3 style={{ fontSize: '18px', fontWeight: 800, color: 'var(--slate-900)', marginTop: '10px' }}>
                  {act.title}
                </h3>
                <p style={{ fontSize: '13px', color: 'var(--slate-600)', marginTop: '6px', lineHeight: '1.4' }}>
                  {act.description}
                </p>

                <div style={{ marginTop: '14px', display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '12px', color: 'var(--slate-600)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Calendar size={14} color="var(--primary-600)" />
                    <span>{act.activity_date ? new Date(act.activity_date).toLocaleString() : 'TBD'}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <MapPin size={14} color="var(--primary-600)" />
                    <span>{act.venue}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Tag size={14} color="var(--primary-600)" />
                    <span>Organizer: {act.organizer}</span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Admin Add Assignment Modal */}
      {showAssignModal && (
        <div className="modal-overlay" onClick={() => setShowAssignModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '560px' }}>
            <form onSubmit={handleCreateAssignment}>
              <div style={{ padding: '18px 24px', borderBottom: '1px solid var(--slate-100)' }}>
                <h3 style={{ fontSize: '18px', fontWeight: 700 }}>Publish Course Assignment</h3>
              </div>

              <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div className="form-group" style={{ margin: 0 }}>
                  <label className="form-label">Subject</label>
                  <select
                    className="form-select"
                    required
                    value={assignSubjectId}
                    onChange={(e) => setAssignSubjectId(e.target.value)}
                  >
                    {subjects.map((s) => (
                      <option key={s.id} value={s.id}>{s.code} - {s.name}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group" style={{ margin: 0 }}>
                  <label className="form-label">Assignment Title</label>
                  <input
                    type="text"
                    required
                    className="form-input"
                    value={assignTitle}
                    onChange={(e) => setAssignTitle(e.target.value)}
                  />
                </div>

                <div className="form-group" style={{ margin: 0 }}>
                  <label className="form-label">Description & Deliverables</label>
                  <textarea
                    rows="3"
                    className="form-textarea"
                    value={assignDesc}
                    onChange={(e) => setAssignDesc(e.target.value)}
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label">Submission Deadline</label>
                    <input
                      type="datetime-local"
                      required
                      className="form-input"
                      value={assignDeadline}
                      onChange={(e) => setAssignDeadline(e.target.value)}
                    />
                  </div>
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label">Priority</label>
                    <select
                      className="form-select"
                      value={assignPriority}
                      onChange={(e) => setAssignPriority(e.target.value)}
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                    </select>
                  </div>
                </div>
              </div>

              <div style={{ padding: '16px 24px', background: 'var(--slate-50)', borderTop: '1px solid var(--slate-100)', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button type="button" onClick={() => setShowAssignModal(false)} className="btn btn-secondary btn-sm">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary btn-sm">
                  Publish Assignment
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Admin Add Activity Modal */}
      {showActModal && (
        <div className="modal-overlay" onClick={() => setShowActModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '560px' }}>
            <form onSubmit={handleCreateActivity}>
              <div style={{ padding: '18px 24px', borderBottom: '1px solid var(--slate-100)' }}>
                <h3 style={{ fontSize: '18px', fontWeight: 700 }}>Schedule Academic Activity</h3>
              </div>

              <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div className="form-group" style={{ margin: 0 }}>
                  <label className="form-label">Activity Title</label>
                  <input
                    type="text"
                    required
                    className="form-input"
                    value={actTitle}
                    onChange={(e) => setActTitle(e.target.value)}
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label">Activity Type</label>
                    <select className="form-select" value={actType} onChange={(e) => setActType(e.target.value)}>
                      <option value="workshop">Workshop</option>
                      <option value="seminar">Seminar</option>
                      <option value="guest_lecture">Guest Lecture</option>
                      <option value="hackathon">Hackathon</option>
                      <option value="project_review">Project Review</option>
                      <option value="symposium">Symposium</option>
                    </select>
                  </div>
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label">Date & Time</label>
                    <input
                      type="datetime-local"
                      required
                      className="form-input"
                      value={actDate}
                      onChange={(e) => setActDate(e.target.value)}
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label">Venue</label>
                    <input
                      type="text"
                      className="form-input"
                      value={actVenue}
                      onChange={(e) => setActVenue(e.target.value)}
                    />
                  </div>
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label">Organizer</label>
                    <input
                      type="text"
                      className="form-input"
                      value={actOrganizer}
                      onChange={(e) => setActOrganizer(e.target.value)}
                    />
                  </div>
                </div>

                <div className="form-group" style={{ margin: 0 }}>
                  <label className="form-label">Description</label>
                  <textarea
                    rows="3"
                    className="form-textarea"
                    value={actDesc}
                    onChange={(e) => setActDesc(e.target.value)}
                  />
                </div>
              </div>

              <div style={{ padding: '16px 24px', background: 'var(--slate-50)', borderTop: '1px solid var(--slate-100)', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button type="button" onClick={() => setShowActModal(false)} className="btn btn-secondary btn-sm">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary btn-sm">
                  Schedule Activity
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AssignmentsPage;
