import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api';
import ConfirmationModal from '../components/ConfirmationModal';
import {
  Calendar,
  Clock,
  MapPin,
  Award,
  AlertCircle,
  Plus,
  Edit2,
  XCircle,
  CheckCircle,
  Filter,
  Sparkles
} from 'lucide-react';

export const ExamsPage = () => {
  const { isAdmin } = useAuth();
  const [exams, setExams] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('all');

  // Admin Modal States
  const [showModal, setShowModal] = useState(false);
  const [editingExam, setEditingExam] = useState(null);
  const [cancelTargetExam, setCancelTargetExam] = useState(null);

  // Form fields
  const [formSubjectId, setFormSubjectId] = useState('');
  const [formTitle, setFormTitle] = useState('');
  const [formExamType, setFormExamType] = useState('Semester End Exam');
  const [formExamDate, setFormExamDate] = useState('');
  const [formStartTime, setFormStartTime] = useState('10:00:00');
  const [formEndTime, setFormEndTime] = useState('13:00:00');
  const [formHall, setFormHall] = useState('Main Block Hall 302');
  const [formMaxMarks, setFormMaxMarks] = useState(100);
  const [formRemarks, setFormRemarks] = useState('');

  useEffect(() => {
    fetchExams();
    fetchSubjects();
  }, []);

  const fetchExams = async () => {
    try {
      setLoading(true);
      const res = await api.get('/exams');
      if (res.success) {
        setExams(res.examinations || []);
      }
    } catch (err) {
      console.error('Error fetching exams:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchSubjects = async () => {
    try {
      const res = await api.get('/admin/subjects');
      if (res.success) {
        setSubjects(res.subjects || []);
        if (res.subjects.length > 0 && !formSubjectId) {
          setFormSubjectId(res.subjects[0].id);
        }
      }
    } catch {
      // Non-admins can also fetch subjects
    }
  };

  const openCreateModal = () => {
    setEditingExam(null);
    setFormTitle('');
    setFormExamType('Semester End Exam');
    setFormExamDate('');
    setFormStartTime('10:00:00');
    setFormEndTime('13:00:00');
    setFormHall('Main Block Hall 302');
    setFormMaxMarks(100);
    setFormRemarks('');
    setShowModal(true);
  };

  const openEditModal = (exam) => {
    setEditingExam(exam);
    setFormSubjectId(exam.subject_id);
    setFormTitle(exam.title);
    setFormExamType(exam.exam_type);
    setFormExamDate(exam.exam_date);
    setFormStartTime(exam.start_time);
    setFormEndTime(exam.end_time);
    setFormHall(exam.hall_number);
    setFormMaxMarks(exam.max_marks);
    setFormRemarks(exam.remarks || '');
    setShowModal(true);
  };

  const handleSaveExam = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        subject_id: Number(formSubjectId),
        title: formTitle,
        exam_type: formExamType,
        exam_date: formExamDate,
        start_time: formStartTime,
        end_time: formEndTime,
        hall_number: formHall,
        max_marks: Number(formMaxMarks),
        remarks: formRemarks
      };

      if (editingExam) {
        await api.put(`/exams/${editingExam.id}`, payload);
      } else {
        await api.post('/exams', payload);
      }

      setShowModal(false);
      fetchExams();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleCancelExam = async () => {
    if (!cancelTargetExam) return;
    try {
      await api.post(`/exams/${cancelTargetExam.id}/cancel`);
      setCancelTargetExam(null);
      fetchExams();
    } catch (err) {
      alert(err.message);
    }
  };

  const filteredExams = exams.filter((e) => {
    if (filterStatus === 'all') return true;
    if (filterStatus === 'cancelled') return e.status === 'cancelled';
    if (filterStatus === 'rescheduled') return e.status === 'rescheduled';
    if (filterStatus === 'today') return e.countdown?.days_remaining === 0;
    if (filterStatus === 'tomorrow') return e.countdown?.days_remaining === 1;
    if (filterStatus === 'upcoming') return (e.countdown?.days_remaining || 0) > 1 && e.status !== 'cancelled';
    if (filterStatus === 'completed') return (e.countdown?.days_remaining || 0) < 0;
    return true;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
        <div>
          <h2 style={{ fontSize: '22px', fontWeight: 800, color: 'var(--slate-900)' }}>
            Examination Schedule & Smart Academic Alerts
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--slate-500)', marginTop: '2px' }}>
            Countdowns calculated in calendar days (Asia/Kolkata timezone). Automated alerts dispatched at 7d, 3d, 1d & exam day.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          {isAdmin && (
            <button onClick={openCreateModal} className="btn btn-primary btn-sm">
              <Plus size={16} />
              <span>Schedule Examination</span>
            </button>
          )}
        </div>
      </div>

      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '4px' }}>
        {[
          { id: 'all', label: 'All Exams' },
          { id: 'today', label: '🎯 Today (Exam Day!)' },
          { id: 'tomorrow', label: '⚡ Tomorrow' },
          { id: 'upcoming', label: 'Upcoming' },
          { id: 'rescheduled', label: 'Rescheduled' },
          { id: 'cancelled', label: 'Cancelled' },
          { id: 'completed', label: 'Completed' }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setFilterStatus(tab.id)}
            className="btn btn-sm"
            style={{
              background: filterStatus === tab.id ? 'var(--primary-700)' : 'var(--white)',
              color: filterStatus === tab.id ? 'white' : 'var(--slate-700)',
              border: `1px solid ${filterStatus === tab.id ? 'var(--primary-700)' : 'var(--slate-200)'}`,
              borderRadius: 'var(--radius-full)'
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Examinations Cards List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px' }}>Loading examination schedule...</div>
        ) : filteredExams.length === 0 ? (
          <div className="glass-card" style={{ padding: '40px', textAlign: 'center', color: 'var(--slate-500)' }}>
            No examinations matching this filter.
          </div>
        ) : (
          filteredExams.map((exam) => {
            const cd = exam.countdown;
            const isToday = cd?.days_remaining === 0;
            const isTomorrow = cd?.days_remaining === 1;
            const isCancelled = exam.status === 'cancelled';
            const isRescheduled = exam.status === 'rescheduled';

            return (
              <div
                key={exam.id}
                className="glass-card glass-card-hover"
                style={{
                  padding: '20px 24px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '16px',
                  borderLeft: `6px solid ${
                    isCancelled ? 'var(--slate-400)' :
                    isToday ? 'var(--danger)' :
                    isTomorrow ? 'var(--warning)' :
                    isRescheduled ? 'var(--accent-purple)' : 'var(--primary-600)'
                  }`
                }}
              >
                <div style={{ minWidth: '280px', flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
                    <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--primary-600)', background: 'var(--primary-50)', padding: '2px 8px', borderRadius: '4px' }}>
                      {exam.subject_code}
                    </span>
                    <span style={{ fontSize: '13px', color: 'var(--slate-500)', fontWeight: 600 }}>
                      {exam.exam_type}
                    </span>
                    {isRescheduled && (
                      <span className="badge badge-warning">Rescheduled</span>
                    )}
                    {isCancelled && (
                      <span className="badge badge-danger">Cancelled</span>
                    )}
                  </div>

                  <h3 style={{ fontSize: '18px', fontWeight: 800, color: 'var(--slate-900)' }}>
                    {exam.title}
                  </h3>

                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', fontSize: '13px', color: 'var(--slate-600)', marginTop: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                      <Calendar size={14} color="var(--primary-600)" />
                      <span>{exam.exam_date}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                      <Clock size={14} color="var(--primary-600)" />
                      <span>{exam.start_time} - {exam.end_time}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                      <MapPin size={14} color="var(--primary-600)" />
                      <span>{exam.hall_number}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                      <Award size={14} color="var(--primary-600)" />
                      <span>Max Marks: {exam.max_marks}</span>
                    </div>
                  </div>

                  {exam.remarks && (
                    <div style={{ fontSize: '12px', color: 'var(--slate-500)', fontStyle: 'italic', marginTop: '6px' }}>
                      Note: {exam.remarks}
                    </div>
                  )}
                </div>

                {/* Right Side: Countdown Pill & Admin Controls */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{ textAlign: 'right' }}>
                    <span
                      className={`badge ${
                        isCancelled ? 'badge-secondary' :
                        isToday ? 'badge-danger' :
                        isTomorrow ? 'badge-warning' :
                        cd?.days_remaining <= 7 ? 'badge-primary' : 'badge-info'
                      }`}
                      style={{ fontSize: '13px', padding: '8px 14px', fontWeight: 800 }}
                    >
                      {isCancelled ? 'Exam Cancelled' : cd?.countdown_message}
                    </span>
                  </div>

                  {isAdmin && (
                    <div style={{ display: 'flex', gap: '6px' }}>
                      <button
                        onClick={() => openEditModal(exam)}
                        className="btn btn-secondary btn-sm"
                        title="Reschedule / Edit Examination"
                      >
                        <Edit2 size={14} />
                      </button>
                      {!isCancelled && (
                        <button
                          onClick={() => setCancelTargetExam(exam)}
                          className="btn btn-secondary btn-sm"
                          style={{ color: 'var(--danger)' }}
                          title="Cancel Examination"
                        >
                          <XCircle size={14} />
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Admin Create / Reschedule Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '600px' }}>
            <form onSubmit={handleSaveExam}>
              <div style={{ padding: '18px 24px', borderBottom: '1px solid var(--slate-100)' }}>
                <h3 style={{ fontSize: '18px', fontWeight: 700 }}>
                  {editingExam ? 'Reschedule / Update Examination' : 'Schedule New Examination'}
                </h3>
              </div>

              <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label">Subject</label>
                    <select
                      className="form-select"
                      required
                      value={formSubjectId}
                      onChange={(e) => setFormSubjectId(e.target.value)}
                    >
                      {subjects.map((s) => (
                        <option key={s.id} value={s.id}>
                          {s.code} - {s.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label">Exam Type</label>
                    <select
                      className="form-select"
                      value={formExamType}
                      onChange={(e) => setFormExamType(e.target.value)}
                    >
                      <option value="Semester End Exam">Semester End Exam</option>
                      <option value="Internal Assessment 1">Internal Assessment 1</option>
                      <option value="Internal Assessment 2">Internal Assessment 2</option>
                      <option value="Model Exam">Model Exam</option>
                      <option value="Lab Exam">Lab Exam</option>
                    </select>
                  </div>
                </div>

                <div className="form-group" style={{ margin: 0 }}>
                  <label className="form-label">Exam Title (Optional override)</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Leave blank to use Subject Name + Exam Type"
                    value={formTitle}
                    onChange={(e) => setFormTitle(e.target.value)}
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '14px' }}>
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label">Date (YYYY-MM-DD)</label>
                    <input
                      type="date"
                      required
                      className="form-input"
                      value={formExamDate}
                      onChange={(e) => setFormExamDate(e.target.value)}
                    />
                  </div>
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label">Start Time</label>
                    <input
                      type="time"
                      required
                      className="form-input"
                      value={formStartTime}
                      onChange={(e) => setFormStartTime(e.target.value)}
                    />
                  </div>
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label">End Time</label>
                    <input
                      type="time"
                      required
                      className="form-input"
                      value={formEndTime}
                      onChange={(e) => setFormEndTime(e.target.value)}
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '14px' }}>
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label">Hall / Venue</label>
                    <input
                      type="text"
                      className="form-input"
                      value={formHall}
                      onChange={(e) => setFormHall(e.target.value)}
                    />
                  </div>
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label">Max Marks</label>
                    <input
                      type="number"
                      className="form-input"
                      value={formMaxMarks}
                      onChange={(e) => setFormMaxMarks(e.target.value)}
                    />
                  </div>
                </div>

                <div className="form-group" style={{ margin: 0 }}>
                  <label className="form-label">Instructions / Remarks</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. Non-programmable calculators allowed"
                    value={formRemarks}
                    onChange={(e) => setFormRemarks(e.target.value)}
                  />
                </div>
              </div>

              <div style={{ padding: '16px 24px', background: 'var(--slate-50)', borderTop: '1px solid var(--slate-100)', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button type="button" onClick={() => setShowModal(false)} className="btn btn-secondary btn-sm">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary btn-sm">
                  {editingExam ? 'Save & Broadcast Reschedule' : 'Confirm Examination'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Confirmation Modal for Exam Cancellation */}
      <ConfirmationModal
        isOpen={!!cancelTargetExam}
        title="Cancel Examination"
        message={`Are you sure you want to cancel the examination "${cancelTargetExam?.title}" on ${cancelTargetExam?.exam_date}? All enrolled students will be immediately sent an urgent in-app cancellation alert.`}
        confirmText="Confirm Cancellation"
        onConfirm={handleCancelExam}
        onClose={() => setCancelTargetExam(null)}
      />
    </div>
  );
};

export default ExamsPage;
