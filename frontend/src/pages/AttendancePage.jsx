import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api';
import {
  Percent,
  AlertTriangle,
  CheckCircle,
  HelpCircle,
  TrendingUp,
  Sliders,
  Calculator,
  PlusCircle,
  Save
} from 'lucide-react';

export const AttendancePage = () => {
  const { user, isAdmin } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editingTargetId, setEditingTargetId] = useState(null);
  const [targetInput, setTargetInput] = useState('75');

  // Simulator State
  const [showSimulator, setShowSimulator] = useState(false);
  const [simSubject, setSimSubject] = useState(null);
  const [futureAttend, setFutureAttend] = useState(5);
  const [futureMiss, setFutureMiss] = useState(0);
  const [simResult, setSimResult] = useState(null);

  // Admin edit attendance state
  const [adminRecordSubj, setAdminRecordSubj] = useState(null);
  const [adminConducted, setAdminConducted] = useState(0);
  const [adminAttended, setAdminAttended] = useState(0);

  useEffect(() => {
    fetchAttendance();
  }, []);

  const fetchAttendance = async () => {
    try {
      setLoading(true);
      const res = await api.get('/attendance');
      if (res.success) {
        setData(res);
      }
    } catch (err) {
      console.error('Failed to fetch attendance:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateTarget = async (subjectId) => {
    try {
      const targetVal = parseFloat(targetInput);
      if (isNaN(targetVal) || targetVal <= 0 || targetVal > 100) {
        alert('Please enter a valid target between 1 and 100.');
        return;
      }
      await api.put('/attendance/target', {
        subject_id: subjectId,
        target_percentage: targetVal
      });
      setEditingTargetId(null);
      fetchAttendance();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleSimulate = async () => {
    if (!simSubject) return;
    try {
      const res = await api.post('/attendance/simulate', {
        conducted: simSubject.conducted_classes,
        attended: simSubject.attended_classes,
        target: simSubject.target_percentage,
        future_classes_attend: Number(futureAttend),
        future_classes_miss: Number(futureMiss)
      });
      if (res.success) {
        setSimResult(res);
      }
    } catch (err) {
      alert(err.message);
    }
  };

  const handleSaveAdminRecord = async (e) => {
    e.preventDefault();
    if (!adminRecordSubj) return;
    try {
      await api.post('/attendance/record', {
        subject_id: adminRecordSubj.subject_id,
        conducted_classes: Number(adminConducted),
        attended_classes: Number(adminAttended)
      });
      setAdminRecordSubj(null);
      fetchAttendance();
    } catch (err) {
      alert(err.message);
    }
  };

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '60px' }}>Loading subject attendance data...</div>;
  }

  const { overall, records } = data || { overall: {}, records: [] };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Overall Attendance Summary Banner */}
      <div
        className="glass-card"
        style={{
          padding: '24px 30px',
          background: 'linear-gradient(135deg, #1e3a8a, #2563eb)',
          color: 'white',
          borderRadius: '20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '20px'
        }}
      >
        <div>
          <div style={{ fontSize: '13px', fontWeight: 600, opacity: 0.85, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            Semester Attendance Summary
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px', marginTop: '6px' }}>
            <span style={{ fontSize: '36px', fontWeight: 800 }}>{overall.percentage}%</span>
            <span style={{ fontSize: '15px', opacity: 0.9 }}>
              ({overall.attended} attended / {overall.conducted} conducted)
            </span>
          </div>
          <div style={{ fontSize: '13px', opacity: 0.9, marginTop: '4px' }}>
            {overall.warning_message}
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <div style={{ background: 'rgba(255, 255, 255, 0.15)', backdropFilter: 'blur(10px)', padding: '12px 18px', borderRadius: '12px', textAlign: 'center' }}>
            <div style={{ fontSize: '12px', opacity: 0.8 }}>Required Target</div>
            <div style={{ fontSize: '18px', fontWeight: 700 }}>{overall.target_percentage}%</div>
          </div>
          {overall.classes_needed > 0 && (
            <div style={{ background: 'rgba(239, 68, 68, 0.25)', border: '1px solid rgba(254, 202, 202, 0.4)', padding: '12px 18px', borderRadius: '12px', textAlign: 'center' }}>
              <div style={{ fontSize: '12px', color: '#fee2e2' }}>Need to Attend</div>
              <div style={{ fontSize: '18px', fontWeight: 800, color: 'white' }}>
                +{overall.classes_needed} consecutive
              </div>
            </div>
          )}
          {overall.target_met && overall.classes_can_miss > 0 && (
            <div style={{ background: 'rgba(16, 185, 129, 0.25)', border: '1px solid rgba(167, 243, 208, 0.4)', padding: '12px 18px', borderRadius: '12px', textAlign: 'center' }}>
              <div style={{ fontSize: '12px', color: '#d1fae5' }}>Safety Margin</div>
              <div style={{ fontSize: '18px', fontWeight: 800, color: 'white' }}>
                Can miss {overall.classes_can_miss} classes
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Subject-Wise Cards Grid */}
      <div>
        <h3 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '16px' }}>
          Enrolled Course Attendance & Shortage Forecast
        </h3>

        <div className="grid-2">
          {records.map((rec) => {
            const m = rec.metrics;
            const isEditing = editingTargetId === rec.subject_id;
            const isDanger = m.status_level === 'danger';
            const isWarning = m.status_level === 'warning';

            return (
              <div
                key={rec.id}
                className="glass-card glass-card-hover"
                style={{
                  padding: '22px',
                  borderLeft: `5px solid ${isDanger ? 'var(--danger)' : isWarning ? 'var(--warning)' : 'var(--success)'}`
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--primary-600)', textTransform: 'uppercase' }}>
                      {rec.subject_code}
                    </div>
                    <h4 style={{ fontSize: '17px', fontWeight: 700, color: 'var(--slate-900)', marginTop: '2px' }}>
                      {rec.subject_name}
                    </h4>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '24px', fontWeight: 800, color: isDanger ? 'var(--danger)' : 'var(--slate-900)' }}>
                      {m.percentage}%
                    </div>
                    <span className={`badge ${isDanger ? 'badge-danger' : isWarning ? 'badge-warning' : 'badge-success'}`}>
                      {m.status}
                    </span>
                  </div>
                </div>

                {/* Progress bar */}
                <div style={{ marginTop: '16px' }}>
                  <div className="progress-container" style={{ height: '10px' }}>
                    <div
                      className="progress-bar"
                      style={{
                        width: `${Math.min(100, m.percentage)}%`,
                        background: isDanger ? 'var(--danger)' : isWarning ? 'var(--warning)' : 'var(--success)'
                      }}
                    />
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--slate-500)', marginTop: '6px' }}>
                    <span>{m.attended} attended / {m.conducted} conducted</span>
                    <span>Target: {m.target_percentage}%</span>
                  </div>
                </div>

                {/* Warning / Advice message */}
                <div
                  style={{
                    marginTop: '14px',
                    padding: '10px 14px',
                    background: isDanger ? 'var(--danger-bg)' : isWarning ? 'var(--warning-bg)' : 'var(--slate-50)',
                    borderRadius: 'var(--radius-md)',
                    fontSize: '12px',
                    color: isDanger ? '#991b1b' : isWarning ? '#92400e' : 'var(--slate-700)',
                    lineHeight: '1.4'
                  }}
                >
                  {m.warning_message}
                </div>

                {/* Bottom Actions: Target Setter & Simulator */}
                <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                  {isEditing ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <input
                        type="number"
                        min="1"
                        max="100"
                        className="form-input"
                        style={{ width: '70px', padding: '4px 8px', fontSize: '12px' }}
                        value={targetInput}
                        onChange={(e) => setTargetInput(e.target.value)}
                      />
                      <button
                        onClick={() => handleUpdateTarget(rec.subject_id)}
                        className="btn btn-primary btn-sm"
                        style={{ padding: '4px 10px', fontSize: '12px' }}
                      >
                        <Save size={12} />
                        <span>Save</span>
                      </button>
                      <button
                        onClick={() => setEditingTargetId(null)}
                        className="btn btn-secondary btn-sm"
                        style={{ padding: '4px 8px', fontSize: '12px' }}
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => {
                        setEditingTargetId(rec.subject_id);
                        setTargetInput(rec.target_percentage.toString());
                      }}
                      className="btn btn-secondary btn-sm"
                      style={{ fontSize: '12px', padding: '6px 10px' }}
                    >
                      <Sliders size={13} />
                      <span>Set Target ({rec.target_percentage}%)</span>
                    </button>
                  )}

                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      onClick={() => {
                        setSimSubject(rec);
                        setSimResult(null);
                        setShowSimulator(true);
                      }}
                      className="btn btn-secondary btn-sm"
                      style={{ fontSize: '12px', padding: '6px 12px' }}
                    >
                      <Calculator size={13} color="var(--primary-600)" />
                      <span>What-If Simulator</span>
                    </button>

                    {isAdmin && (
                      <button
                        onClick={() => {
                          setAdminRecordSubj(rec);
                          setAdminConducted(rec.conducted_classes);
                          setAdminAttended(rec.attended_classes);
                        }}
                        className="btn btn-secondary btn-sm"
                        style={{ fontSize: '12px', padding: '6px 10px' }}
                      >
                        Edit Count
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* What-If Attendance Simulator Modal */}
      {showSimulator && simSubject && (
        <div className="modal-overlay" onClick={() => setShowSimulator(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '560px' }}>
            <div style={{ padding: '18px 24px', borderBottom: '1px solid var(--slate-100)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Calculator size={20} color="var(--primary-600)" />
                <h3 style={{ fontSize: '18px', fontWeight: 700 }}>
                  Attendance Forecast Simulator
                </h3>
              </div>
              <button onClick={() => setShowSimulator(false)} className="btn btn-secondary btn-sm">✕</button>
            </div>

            <div style={{ padding: '24px' }}>
              <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--slate-900)' }}>
                {simSubject.subject_name} ({simSubject.subject_code})
              </div>
              <div style={{ fontSize: '12px', color: 'var(--slate-500)', marginTop: '2px' }}>
                Current: {simSubject.attended_classes} of {simSubject.conducted_classes} classes ({simSubject.metrics.percentage}%)
              </div>

              <div style={{ marginTop: '20px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div className="form-group">
                  <label className="form-label">Future Classes to ATTEND</label>
                  <input
                    type="number"
                    min="0"
                    className="form-input"
                    value={futureAttend}
                    onChange={(e) => setFutureAttend(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Future Classes to MISS</label>
                  <input
                    type="number"
                    min="0"
                    className="form-input"
                    value={futureMiss}
                    onChange={(e) => setFutureMiss(e.target.value)}
                  />
                </div>
              </div>

              <button onClick={handleSimulate} className="btn btn-primary" style={{ width: '100%', marginTop: '6px' }}>
                Calculate Projected Attendance
              </button>

              {simResult && (
                <div
                  style={{
                    marginTop: '20px',
                    padding: '16px',
                    borderRadius: 'var(--radius-md)',
                    background: simResult.simulated.percentage >= simSubject.target_percentage ? 'var(--success-bg)' : 'var(--danger-bg)',
                    border: `1px solid ${simResult.simulated.percentage >= simSubject.target_percentage ? '#a7f3d0' : '#fecaca'}`
                  }}
                >
                  <div style={{ fontSize: '15px', fontWeight: 800, color: 'var(--slate-900)' }}>
                    Projected Attendance: {simResult.simulated.percentage}%
                  </div>
                  <div style={{ fontSize: '13px', marginTop: '6px', lineHeight: '1.5', color: 'var(--slate-700)' }}>
                    {simResult.summary}
                  </div>
                  <div style={{ fontSize: '12px', marginTop: '8px', color: 'var(--slate-600)' }}>
                    Status: <strong>{simResult.simulated.status}</strong> ({simResult.simulated.warning_message})
                  </div>
                </div>
              )}
            </div>

            <div style={{ padding: '14px 24px', background: 'var(--slate-50)', borderTop: '1px solid var(--slate-100)', display: 'flex', justifyContent: 'flex-end' }}>
              <button onClick={() => setShowSimulator(false)} className="btn btn-secondary btn-sm">
                Close Simulator
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Admin Quick Record Editor Modal */}
      {adminRecordSubj && (
        <div className="modal-overlay" onClick={() => setAdminRecordSubj(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <form onSubmit={handleSaveAdminRecord}>
              <div style={{ padding: '18px 24px', borderBottom: '1px solid var(--slate-100)' }}>
                <h3 style={{ fontSize: '18px', fontWeight: 700 }}>
                  Update Attendance Count (Admin)
                </h3>
                <p style={{ fontSize: '12px', color: 'var(--slate-500)' }}>
                  {adminRecordSubj.subject_name} ({adminRecordSubj.subject_code})
                </p>
              </div>

              <div style={{ padding: '24px' }}>
                <div className="form-group">
                  <label className="form-label">Total Conducted Classes</label>
                  <input
                    type="number"
                    min="0"
                    required
                    className="form-input"
                    value={adminConducted}
                    onChange={(e) => setAdminConducted(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Total Attended Classes</label>
                  <input
                    type="number"
                    min="0"
                    required
                    className="form-input"
                    value={adminAttended}
                    onChange={(e) => setAdminAttended(e.target.value)}
                  />
                </div>
              </div>

              <div style={{ padding: '14px 24px', background: 'var(--slate-50)', borderTop: '1px solid var(--slate-100)', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button type="button" onClick={() => setAdminRecordSubj(null)} className="btn btn-secondary btn-sm">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary btn-sm">
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AttendancePage;
