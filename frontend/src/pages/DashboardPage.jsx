import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api';
import {
  Percent,
  Calendar,
  FileText,
  Activity,
  CheckSquare,
  Bell,
  ArrowRight,
  Clock,
  Sparkles,
  AlertTriangle,
  CheckCircle,
  HelpCircle,
  MessageSquare,
  Timer
} from 'lucide-react';

export const DashboardPage = ({ setActiveTab }) => {
  const { user, t } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboardSummary();
  }, []);

  const fetchDashboardSummary = async () => {
    try {
      setLoading(true);
      const res = await api.get('/dashboard/summary');
      if (res.success) {
        setData(res);
      }
    } catch (err) {
      setError(err.message || 'Failed to fetch dashboard data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '80px 0' }}>
        <div style={{ fontSize: '18px', fontWeight: 600, color: 'var(--primary-600)' }}>
          Loading real-time academic metrics from database...
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={{ padding: '30px', textAlign: 'center' }}>
        <p style={{ color: 'var(--danger)' }}>{error || 'Unable to connect to academic server.'}</p>
        <button onClick={fetchDashboardSummary} className="btn btn-primary" style={{ marginTop: '16px' }}>
          Retry
        </button>
      </div>
    );
  }

  const { metrics, upcoming_exams, pending_assignments, upcoming_activities, study_plan, recent_notifications } = data;
  const attPct = metrics?.attendance_percentage || 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Top Banner Greeting */}
      <div
        className="glass-card"
        style={{
          padding: '24px 30px',
          background: 'linear-gradient(135deg, rgba(30, 64, 175, 0.95), rgba(37, 99, 235, 0.95))',
          color: 'white',
          borderRadius: '20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
          boxShadow: '0 12px 30px rgba(37, 99, 235, 0.25)'
        }}
      >
        <div>
          <div style={{ fontSize: '13px', textTransform: 'uppercase', letterSpacing: '0.08em', opacity: 0.85, fontWeight: 700 }}>
            Academic Session 2026-2027 • {user?.profile?.department || 'Computer Science & Engineering'}
          </div>
          <h2 style={{ fontSize: '26px', fontWeight: 800, color: 'white', marginTop: '4px' }}>
            {t.welcome}, {user?.profile?.full_name || user?.email}! 🎓
          </h2>
          <p style={{ fontSize: '14px', opacity: 0.9, marginTop: '4px' }}>
            All statistics and exam countdowns are synchronized with Asia/Kolkata timezone.
          </p>
        </div>

        <button
          onClick={() => setActiveTab('chat')}
          style={{
            background: 'white',
            color: 'var(--primary-700)',
            border: 'none',
            padding: '12px 20px',
            borderRadius: 'var(--radius-full)',
            fontWeight: 700,
            fontSize: '14px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            cursor: 'pointer',
            boxShadow: '0 4px 14px rgba(0, 0, 0, 0.15)',
            transition: 'transform 0.18s ease'
          }}
        >
          <Sparkles size={16} color="var(--primary-600)" />
          <span>Ask Chatbot (English/தமிழ்)</span>
        </button>
      </div>

      {/* KPI Cards: Real Database Statistics */}
      <div className="grid-4">
        {/* Attendance Percentage */}
        <div className="glass-card glass-card-hover" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--slate-500)' }}>
                {t.overallAttendance}
              </div>
              <div style={{ fontSize: '32px', fontWeight: 800, color: attPct < 75 ? 'var(--danger)' : 'var(--slate-900)', marginTop: '6px' }}>
                {attPct}%
              </div>
            </div>
            <div
              style={{
                width: '44px',
                height: '44px',
                borderRadius: '12px',
                background: attPct < 75 ? 'var(--danger-bg)' : 'var(--success-bg)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: attPct < 75 ? 'var(--danger)' : 'var(--success)'
              }}
            >
              <Percent size={22} />
            </div>
          </div>
          <div style={{ marginTop: '14px' }}>
            <div className="progress-container">
              <div
                className="progress-bar"
                style={{
                  width: `${Math.min(100, attPct)}%`,
                  background: attPct < 75 ? 'var(--danger)' : 'var(--success)'
                }}
              />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--slate-500)', marginTop: '6px' }}>
              <span>{metrics.total_attended_classes} of {metrics.total_conducted_classes} classes</span>
              <span>{attPct < 75 ? '⚠️ Below 75% target' : '✓ Target met'}</span>
            </div>
          </div>
        </div>

        {/* Upcoming Examinations */}
        <div className="glass-card glass-card-hover" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--slate-500)' }}>
                {t.upcomingExams}
              </div>
              <div style={{ fontSize: '32px', fontWeight: 800, color: 'var(--slate-900)', marginTop: '6px' }}>
                {metrics.upcoming_exams_count}
              </div>
            </div>
            <div
              style={{
                width: '44px',
                height: '44px',
                borderRadius: '12px',
                background: 'var(--primary-50)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--primary-600)'
              }}
            >
              <Calendar size={22} />
            </div>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--slate-500)', marginTop: '14px' }}>
            {upcoming_exams.length > 0 ? (
              <span style={{ color: 'var(--primary-700)', fontWeight: 600 }}>
                Next: {upcoming_exams[0].countdown?.countdown_message || upcoming_exams[0].title}
              </span>
            ) : (
              'No upcoming exams scheduled'
            )}
          </div>
        </div>

        {/* Pending Assignments */}
        <div className="glass-card glass-card-hover" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--slate-500)' }}>
                {t.pendingAssignments}
              </div>
              <div style={{ fontSize: '32px', fontWeight: 800, color: 'var(--slate-900)', marginTop: '6px' }}>
                {metrics.pending_assignments_count}
              </div>
            </div>
            <div
              style={{
                width: '44px',
                height: '44px',
                borderRadius: '12px',
                background: 'var(--warning-bg)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--warning)'
              }}
            >
              <FileText size={22} />
            </div>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--slate-500)', marginTop: '14px' }}>
            {pending_assignments.some(a => a.is_overdue) ? (
              <span style={{ color: 'var(--danger)', fontWeight: 600 }}>⚠️ Overdue task requires attention</span>
            ) : (
              'All tasks within scheduled deadline'
            )}
          </div>
        </div>

        {/* Study Plan Progress */}
        <div className="glass-card glass-card-hover" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--slate-500)' }}>
                {t.studyProgress}
              </div>
              <div style={{ fontSize: '32px', fontWeight: 800, color: 'var(--slate-900)', marginTop: '6px' }}>
                {study_plan?.completion_percentage || 0}%
              </div>
            </div>
            <div
              style={{
                width: '44px',
                height: '44px',
                borderRadius: '12px',
                background: '#f3e8ff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--accent-purple)'
              }}
            >
              <CheckSquare size={22} />
            </div>
          </div>
          <div style={{ marginTop: '14px' }}>
            <div className="progress-container">
              <div
                className="progress-bar"
                style={{
                  width: `${study_plan?.completion_percentage || 0}%`,
                  background: 'var(--accent-purple)'
                }}
              />
            </div>
            <div style={{ fontSize: '11px', color: 'var(--slate-500)', marginTop: '6px' }}>
              {study_plan?.title || 'No active plan'}
            </div>
          </div>
        </div>
      </div>

      {/* Main Two-Column Section */}
      <div className="grid-2">
        {/* Left Column: Upcoming Examinations with Asia/Kolkata countdown */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '18px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Calendar size={18} color="var(--primary-600)" />
              <span>Upcoming Examinations & Smart Alerts</span>
            </h3>
            <button onClick={() => setActiveTab('exams')} className="btn btn-secondary btn-sm">
              <span>View All</span>
              <ArrowRight size={14} />
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {upcoming_exams.length === 0 ? (
              <div style={{ padding: '30px', textAlign: 'center', color: 'var(--slate-500)' }}>
                No exams scheduled in the upcoming period.
              </div>
            ) : (
              upcoming_exams.map((ex) => {
                const cd = ex.countdown;
                const isUrgent = cd.days_remaining <= 1;
                return (
                  <div
                    key={ex.id}
                    style={{
                      padding: '14px 18px',
                      background: isUrgent ? 'var(--danger-bg)' : 'var(--slate-50)',
                      border: `1px solid ${isUrgent ? '#fecaca' : 'var(--slate-200)'}`,
                      borderRadius: 'var(--radius-md)',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}
                  >
                    <div>
                      <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--slate-900)' }}>
                        {ex.subject_name} ({ex.subject_code})
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--slate-500)', marginTop: '3px' }}>
                        {ex.exam_type} • {ex.exam_date} • {ex.hall_number}
                      </div>
                    </div>
                    <div>
                      <span
                        className={`badge ${
                          cd.days_remaining === 0 ? 'badge-danger' :
                          cd.days_remaining === 1 ? 'badge-warning' :
                          cd.days_remaining <= 7 ? 'badge-primary' : 'badge-info'
                        }`}
                        style={{ fontSize: '12px', padding: '6px 12px' }}
                      >
                        {cd.countdown_message}
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right Column: Pending Assignments & Academic Tasks */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '18px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FileText size={18} color="var(--primary-600)" />
              <span>Pending Assignments</span>
            </h3>
            <button onClick={() => setActiveTab('assignments')} className="btn btn-secondary btn-sm">
              <span>View All</span>
              <ArrowRight size={14} />
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {pending_assignments.length === 0 ? (
              <div style={{ padding: '30px', textAlign: 'center', color: 'var(--slate-500)' }}>
                All assignments completed! Great job.
              </div>
            ) : (
              pending_assignments.map((a) => (
                <div
                  key={a.id}
                  style={{
                    padding: '14px 18px',
                    background: a.is_overdue ? 'var(--danger-bg)' : 'var(--slate-50)',
                    border: `1px solid ${a.is_overdue ? '#fecaca' : 'var(--slate-200)'}`,
                    borderRadius: 'var(--radius-md)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <div style={{ minWidth: 0, flex: 1, paddingRight: '12px' }}>
                    <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--slate-900)' }}>
                      {a.title}
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--slate-500)', marginTop: '2px' }}>
                      {a.subject_name} ({a.subject_code}) • Due: {a.deadline ? new Date(a.deadline).toLocaleDateString() : 'TBD'}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <span className={`badge ${a.priority === 'high' ? 'badge-danger' : a.priority === 'medium' ? 'badge-warning' : 'badge-info'}`}>
                      {a.priority}
                    </span>
                    {a.is_overdue && (
                      <span className="badge badge-danger">Overdue</span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Quick Navigation Cards */}
      <div>
        <h3 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '14px' }}>
          Quick Academic Modules
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
          {[
            { id: 'chat', title: 'Multilingual Chatbot', desc: 'RAG Q&A in English, Tamil, Tanglish', icon: MessageSquare, color: 'var(--primary-600)' },
            { id: 'attendance', title: 'Attendance Planner', desc: 'Target simulation & shortage alerts', icon: Percent, color: 'var(--success)' },
            { id: 'planner', title: 'Smart Study Planner', desc: 'Auto-balanced weekly task schedule', icon: CheckSquare, color: 'var(--accent-purple)' },
            { id: 'timer', title: 'Pomodoro Focus Timer', desc: 'Focus intervals with study history', icon: Timer, color: 'var(--warning)' },
            { id: 'notifications', title: 'Smart Alerts Center', desc: '7d, 3d, 1d & exam-day reminders', icon: Bell, color: 'var(--danger)' }
          ].map((card) => {
            const Icon = card.icon;
            return (
              <div
                key={card.id}
                onClick={() => setActiveTab(card.id)}
                className="glass-card glass-card-hover"
                style={{ padding: '18px', cursor: 'pointer' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                  <div style={{ padding: '8px', borderRadius: '10px', background: 'var(--slate-100)', color: card.color }}>
                    <Icon size={20} />
                  </div>
                  <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--slate-900)' }}>
                    {card.title}
                  </div>
                </div>
                <div style={{ fontSize: '12px', color: 'var(--slate-500)', lineHeight: '1.4' }}>
                  {card.desc}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
