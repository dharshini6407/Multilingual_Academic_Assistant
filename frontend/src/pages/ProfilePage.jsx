import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api';
import { User, Bell, Globe, Save, CheckCircle, Shield } from 'lucide-react';

export const ProfilePage = () => {
  const { user, language, setLanguage } = useAuth();
  const [fullName, setFullName] = useState('');
  const [department, setDepartment] = useState('');
  const [yearOfStudy, setYearOfStudy] = useState(3);
  const [semester, setSemester] = useState(5);
  const [prefLang, setPrefLang] = useState('en');

  // Preferences
  const [examAlerts, setExamAlerts] = useState(true);
  const [assignmentAlerts, setAssignmentAlerts] = useState(true);
  const [activityAlerts, setActivityAlerts] = useState(true);
  const [attendanceAlerts, setAttendanceAlerts] = useState(true);
  const [plannerAlerts, setPlannerAlerts] = useState(true);

  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (user?.profile) {
      setFullName(user.profile.full_name || '');
      setDepartment(user.profile.department || 'Computer Science and Engineering');
      setYearOfStudy(user.profile.year_of_study || 3);
      setSemester(user.profile.semester || 5);
      setPrefLang(user.profile.preferred_language || 'en');
    }
    fetchPreferences();
  }, [user]);

  const fetchPreferences = async () => {
    try {
      const res = await api.get('/auth/me');
      if (res.success && res.preferences) {
        const p = res.preferences;
        setExamAlerts(p.exam_alerts ?? true);
        setAssignmentAlerts(p.assignment_alerts ?? true);
        setActivityAlerts(p.activity_alerts ?? true);
        setAttendanceAlerts(p.low_attendance_warning ?? true);
        setPlannerAlerts(p.study_plan_reminders ?? true);
      }
    } catch (err) {
      console.error('Failed to fetch preferences:', err);
    }
  };

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    setSaving(true);
    setMessage('');
    try {
      await api.put('/auth/profile', {
        full_name: fullName,
        department,
        year_of_study: Number(yearOfStudy),
        semester: Number(semester),
        preferred_language: prefLang
      });

      await api.put('/auth/preferences', {
        exam_alerts: examAlerts,
        assignment_alerts: assignmentAlerts,
        activity_alerts: activityAlerts,
        low_attendance_warning: attendanceAlerts,
        study_plan_reminders: plannerAlerts
      });

      setLanguage(prefLang);
      setMessage('Profile and notification preferences updated successfully!');
      setTimeout(() => setMessage(''), 4000);
    } catch (err) {
      alert(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <h2 style={{ fontSize: '22px', fontWeight: 800, color: 'var(--slate-900)' }}>
          Student Profile & Notification Preferences
        </h2>
        <p style={{ fontSize: '13px', color: 'var(--slate-500)', marginTop: '2px' }}>
          Configure personal details, language preferences, and smart academic alert delivery channels.
        </p>
      </div>

      {message && (
        <div style={{ background: 'var(--success-bg)', border: '1px solid #a7f3d0', color: '#065f46', padding: '12px 18px', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle size={18} />
          <span>{message}</span>
        </div>
      )}

      <form onSubmit={handleSaveProfile} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {/* Profile Card */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '17px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <User size={18} color="var(--primary-600)" />
            <span>Academic Profile Details</span>
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
              <div className="form-group" style={{ margin: 0 }}>
                <label className="form-label">Full Name</label>
                <input
                  type="text"
                  required
                  className="form-input"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                />
              </div>
              <div className="form-group" style={{ margin: 0 }}>
                <label className="form-label">Email (Account ID)</label>
                <input
                  type="email"
                  disabled
                  className="form-input"
                  value={user?.email || ''}
                  style={{ background: 'var(--slate-100)', color: 'var(--slate-500)' }}
                />
              </div>
            </div>

            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">Department</label>
              <input
                type="text"
                className="form-input"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '14px' }}>
              <div className="form-group" style={{ margin: 0 }}>
                <label className="form-label">Year of Study</label>
                <select
                  className="form-select"
                  value={yearOfStudy}
                  onChange={(e) => setYearOfStudy(e.target.value)}
                >
                  <option value={1}>1st Year</option>
                  <option value={2}>2nd Year</option>
                  <option value={3}>3rd Year</option>
                  <option value={4}>4th Year</option>
                </select>
              </div>

              <div className="form-group" style={{ margin: 0 }}>
                <label className="form-label">Semester</label>
                <select
                  className="form-select"
                  value={semester}
                  onChange={(e) => setSemester(e.target.value)}
                >
                  {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                    <option key={s} value={s}>Semester {s}</option>
                  ))}
                </select>
              </div>

              <div className="form-group" style={{ margin: 0 }}>
                <label className="form-label">Preferred Language</label>
                <select
                  className="form-select"
                  value={prefLang}
                  onChange={(e) => setPrefLang(e.target.value)}
                >
                  <option value="en">English</option>
                  <option value="ta">Tamil (தமிழ்)</option>
                  <option value="tanglish">Tanglish</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Notifications Preference Card */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '17px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Bell size={18} color="var(--primary-600)" />
            <span>Smart Academic Alerts Delivery Preferences</span>
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {[
              { label: 'Examination Alerts', desc: 'Receive reminders 7 days, 3 days, 1 day, and on exam morning', checked: examAlerts, setChecked: setExamAlerts },
              { label: 'Assignment Deadline Alerts', desc: 'Alerts 1 day before due date and on submission day', checked: assignmentAlerts, setChecked: setAssignmentAlerts },
              { label: 'Academic Activities & Workshops', desc: 'Notifications about departmental symposiums, workshops, and hackathons', checked: activityAlerts, setChecked: setActivityAlerts },
              { label: 'Low Attendance Warnings', desc: 'Immediate notification when attendance falls below minimum 75% target', checked: attendanceAlerts, setChecked: setAttendanceAlerts },
              { label: 'Study Planner Reminders', desc: 'Daily evening prompts to complete scheduled study blocks', checked: plannerAlerts, setChecked: setPlannerAlerts }
            ].map((pref, idx) => (
              <label
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '12px 16px',
                  background: 'var(--slate-50)',
                  borderRadius: 'var(--radius-md)',
                  cursor: 'pointer'
                }}
              >
                <div>
                  <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--slate-900)' }}>{pref.label}</div>
                  <div style={{ fontSize: '12px', color: 'var(--slate-500)', marginTop: '2px' }}>{pref.desc}</div>
                </div>
                <input
                  type="checkbox"
                  style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                  checked={pref.checked}
                  onChange={(e) => pref.setChecked(e.target.checked)}
                />
              </label>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button type="submit" disabled={saving} className="btn btn-primary" style={{ padding: '12px 28px' }}>
            <Save size={16} />
            <span>{saving ? 'Saving Preferences...' : 'Save All Preferences'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};

export default ProfilePage;
