import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api';
import {
  Timer,
  Play,
  Pause,
  RotateCcw,
  CheckCircle,
  Coffee,
  Clock,
  BookOpen,
  Award,
  Sliders
} from 'lucide-react';

export const FocusTimerPage = () => {
  const { user } = useAuth();
  const [subjects, setSubjects] = useState([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState('');
  const [sessionNotes, setSessionNotes] = useState('');

  // Durations in minutes
  const [focusDuration, setFocusDuration] = useState(25);
  const [breakDuration, setBreakDuration] = useState(5);
  const [isBreakMode, setIsBreakMode] = useState(false);

  // Timer run state
  const [timeLeft, setTimeLeft] = useState(25 * 60);
  const [isRunning, setIsRunning] = useState(false);
  const [actualFocusedSeconds, setActualFocusedSeconds] = useState(0);

  // History & stats
  const [historyData, setHistoryData] = useState(null);
  const [loading, setLoading] = useState(true);

  const timerRef = useRef(null);

  useEffect(() => {
    fetchHistory();
    fetchSubjects();
  }, []);

  useEffect(() => {
    if (!isRunning && !isBreakMode) {
      setTimeLeft(focusDuration * 60);
    } else if (!isRunning && isBreakMode) {
      setTimeLeft(breakDuration * 60);
    }
  }, [focusDuration, breakDuration, isBreakMode]);

  useEffect(() => {
    if (isRunning) {
      timerRef.current = setInterval(() => {
        setTimeLeft((prev) => {
          if (prev <= 1) {
            clearInterval(timerRef.current);
            setIsRunning(false);
            handleSessionCompleted();
            return 0;
          }
          return prev - 1;
        });

        if (!isBreakMode) {
          setActualFocusedSeconds((sec) => sec + 1);
        }
      }, 1000);
    } else {
      clearInterval(timerRef.current);
    }

    return () => clearInterval(timerRef.current);
  }, [isRunning, isBreakMode]);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const res = await api.get('/timer/history');
      if (res.success) {
        setHistoryData(res);
      }
    } catch (err) {
      console.error('Failed to fetch timer history:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchSubjects = async () => {
    try {
      const res = await api.get('/admin/subjects');
      if (res.success && res.subjects) {
        setSubjects(res.subjects);
        if (res.subjects.length > 0 && !selectedSubjectId) {
          setSelectedSubjectId(res.subjects[0].id);
        }
      }
    } catch {
      // Ignored
    }
  };

  const handleStart = () => {
    setIsRunning(true);
  };

  const handlePause = () => {
    setIsRunning(false);
  };

  const handleResume = () => {
    setIsRunning(true);
  };

  const handleReset = () => {
    setIsRunning(false);
    setActualFocusedSeconds(0);
    setTimeLeft(isBreakMode ? breakDuration * 60 : focusDuration * 60);
  };

  const handleSessionCompleted = async () => {
    if (!isBreakMode) {
      // Save completed focus session in database
      try {
        await api.post('/timer/sessions', {
          subject_id: selectedSubjectId ? Number(selectedSubjectId) : null,
          duration_minutes: focusDuration,
          break_minutes: breakDuration,
          actual_focused_seconds: actualFocusedSeconds > 0 ? actualFocusedSeconds : (focusDuration * 60),
          session_status: 'completed',
          notes: sessionNotes || 'Focused Pomodoro Study Block'
        });
        setActualFocusedSeconds(0);
        setSessionNotes('');
        fetchHistory();
        alert('🎉 Focus session completed and logged to your academic history! Take a 5-minute break.');
        setIsBreakMode(true);
        setTimeLeft(breakDuration * 60);
      } catch (err) {
        console.error('Failed to log focus session:', err);
      }
    } else {
      alert('☕ Break is over! Ready for another focused study block?');
      setIsBreakMode(false);
      setTimeLeft(focusDuration * 60);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const totalDuration = isBreakMode ? breakDuration * 60 : focusDuration * 60;
  const progressPercent = ((totalDuration - timeLeft) / totalDuration) * 100;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Banner */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
        <div>
          <h2 style={{ fontSize: '22px', fontWeight: 800, color: 'var(--slate-900)' }}>
            Pomodoro Focus Study Timer
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--slate-500)', marginTop: '2px' }}>
            Accurate study sessions tracking. Paused time is strictly excluded from focused statistics.
          </p>
        </div>

        {/* Mode Switcher */}
        <div style={{ display: 'flex', background: 'var(--slate-100)', padding: '4px', borderRadius: 'var(--radius-full)' }}>
          <button
            onClick={() => {
              if (isRunning && !confirm('Switching modes will reset current timer. Proceed?')) return;
              setIsRunning(false);
              setIsBreakMode(false);
              setTimeLeft(focusDuration * 60);
            }}
            className="btn btn-sm"
            style={{
              background: !isBreakMode ? 'var(--primary-700)' : 'transparent',
              color: !isBreakMode ? 'white' : 'var(--slate-700)',
              borderRadius: 'var(--radius-full)',
              border: 'none',
              padding: '6px 16px'
            }}
          >
            <Timer size={14} />
            <span>Focus Mode ({focusDuration}m)</span>
          </button>
          <button
            onClick={() => {
              if (isRunning && !confirm('Switching modes will reset current timer. Proceed?')) return;
              setIsRunning(false);
              setIsBreakMode(true);
              setTimeLeft(breakDuration * 60);
            }}
            className="btn btn-sm"
            style={{
              background: isBreakMode ? 'var(--success)' : 'transparent',
              color: isBreakMode ? 'white' : 'var(--slate-700)',
              borderRadius: 'var(--radius-full)',
              border: 'none',
              padding: '6px 16px'
            }}
          >
            <Coffee size={14} />
            <span>Break ({breakDuration}m)</span>
          </button>
        </div>
      </div>

      {/* Main Timer Display Card */}
      <div className="grid-2">
        <div
          className="glass-card"
          style={{
            padding: '36px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            textAlign: 'center',
            background: isBreakMode
              ? 'linear-gradient(135deg, rgba(236, 253, 245, 0.95), rgba(255, 255, 255, 0.9))'
              : 'linear-gradient(135deg, rgba(239, 246, 255, 0.95), rgba(255, 255, 255, 0.9))'
          }}
        >
          {/* Circular Countdown Progress UI */}
          <div
            style={{
              width: '240px',
              height: '240px',
              borderRadius: '50%',
              background: `conic-gradient(${isBreakMode ? '#10b981' : '#2563eb'} ${progressPercent}%, var(--slate-200) 0%)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 10px 30px rgba(37, 99, 235, 0.15)',
              position: 'relative'
            }}
          >
            <div
              style={{
                width: '210px',
                height: '210px',
                borderRadius: '50%',
                background: 'var(--white)',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <div style={{ fontSize: '13px', fontWeight: 700, color: isBreakMode ? 'var(--success)' : 'var(--primary-600)', textTransform: 'uppercase' }}>
                {isBreakMode ? '☕ Rest Period' : '🎯 Deep Study'}
              </div>
              <div style={{ fontSize: '48px', fontWeight: 800, color: 'var(--slate-900)', fontFamily: 'Outfit' }}>
                {formatTime(timeLeft)}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--slate-400)' }}>
                {isRunning ? 'Active Focus' : timeLeft === 0 ? 'Completed' : 'Paused / Ready'}
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div style={{ display: 'flex', gap: '14px', marginTop: '28px' }}>
            {!isRunning ? (
              <button
                onClick={handleStart}
                className="btn btn-primary"
                style={{ padding: '12px 28px', fontSize: '15px' }}
              >
                <Play size={18} />
                <span>{timeLeft === totalDuration ? 'Start Session' : 'Resume'}</span>
              </button>
            ) : (
              <button
                onClick={handlePause}
                className="btn btn-secondary"
                style={{ padding: '12px 28px', fontSize: '15px', color: 'var(--warning)', borderColor: 'var(--warning)' }}
              >
                <Pause size={18} />
                <span>Pause</span>
              </button>
            )}

            <button
              onClick={handleReset}
              className="btn btn-secondary"
              style={{ padding: '12px 20px' }}
              title="Reset Timer"
            >
              <RotateCcw size={18} />
              <span>Reset</span>
            </button>
          </div>

          <div style={{ marginTop: '16px', fontSize: '12px', color: 'var(--slate-500)' }}>
            Active Focus Accumulated: {Math.floor(actualFocusedSeconds / 60)}m {actualFocusedSeconds % 60}s
          </div>
        </div>

        {/* Configuration & Subject Session Tagging */}
        <div className="glass-card" style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sliders size={18} color="var(--primary-600)" />
            <span>Session Configuration</span>
          </h3>

          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">Subject Tagging</label>
            <select
              className="form-select"
              value={selectedSubjectId}
              onChange={(e) => setSelectedSubjectId(e.target.value)}
            >
              <option value="">General Study</option>
              {subjects.map((s) => (
                <option key={s.id} value={s.id}>{s.code} - {s.name}</option>
              ))}
            </select>
          </div>

          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">Session Topic / Notes</label>
            <input
              type="text"
              className="form-input"
              placeholder="e.g. Solving Unit 3 Network Layer Subnetting"
              value={sessionNotes}
              onChange={(e) => setSessionNotes(e.target.value)}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">Focus Duration</label>
              <select
                className="form-select"
                disabled={isRunning}
                value={focusDuration}
                onChange={(e) => setFocusDuration(Number(e.target.value))}
              >
                <option value={15}>15 Minutes</option>
                <option value={25}>25 Minutes (Standard)</option>
                <option value={45}>45 Minutes (Extended)</option>
                <option value={60}>60 Minutes (Deep)</option>
              </select>
            </div>
            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">Break Duration</label>
              <select
                className="form-select"
                disabled={isRunning}
                value={breakDuration}
                onChange={(e) => setBreakDuration(Number(e.target.value))}
              >
                <option value={5}>5 Minutes (Short)</option>
                <option value={10}>10 Minutes</option>
                <option value={15}>15 Minutes (Long)</option>
              </select>
            </div>
          </div>

          {/* Quick Stats Box */}
          <div style={{ marginTop: 'auto', padding: '16px', background: 'var(--slate-50)', borderRadius: 'var(--radius-md)', border: '1px solid var(--slate-200)' }}>
            <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--slate-800)', marginBottom: '8px' }}>
              Your Focus Track Record
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div>
                <div style={{ fontSize: '11px', color: 'var(--slate-500)' }}>Today's Focus Time</div>
                <div style={{ fontSize: '18px', fontWeight: 800, color: 'var(--primary-700)' }}>
                  {historyData?.stats?.today_focused_minutes || 0} mins
                </div>
              </div>
              <div>
                <div style={{ fontSize: '11px', color: 'var(--slate-500)' }}>Total Sessions Logged</div>
                <div style={{ fontSize: '18px', fontWeight: 800, color: 'var(--slate-900)' }}>
                  {historyData?.stats?.total_sessions_count || 0} sessions
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Focus History Table */}
      <div className="glass-card" style={{ padding: '24px' }}>
        <h3 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '16px' }}>
          Focus Study History (Stored in MySQL)
        </h3>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '30px' }}>Loading history...</div>
        ) : !historyData?.sessions || historyData.sessions.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '30px', color: 'var(--slate-500)' }}>
            No focus sessions logged yet. Complete your first Pomodoro session above!
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid var(--slate-200)', textAlign: 'left', color: 'var(--slate-500)' }}>
                  <th style={{ padding: '10px 14px' }}>Date & Time</th>
                  <th style={{ padding: '10px 14px' }}>Subject</th>
                  <th style={{ padding: '10px 14px' }}>Active Focus Duration</th>
                  <th style={{ padding: '10px 14px' }}>Status</th>
                  <th style={{ padding: '10px 14px' }}>Notes</th>
                </tr>
              </thead>
              <tbody>
                {historyData.sessions.map((sess) => (
                  <tr key={sess.id} style={{ borderBottom: '1px solid var(--slate-100)' }}>
                    <td style={{ padding: '12px 14px', color: 'var(--slate-700)' }}>
                      {sess.started_at ? new Date(sess.started_at).toLocaleString() : 'N/A'}
                    </td>
                    <td style={{ padding: '12px 14px', fontWeight: 600, color: 'var(--slate-900)' }}>
                      {sess.subject_name || 'General Study'}
                    </td>
                    <td style={{ padding: '12px 14px', color: 'var(--primary-700)', fontWeight: 700 }}>
                      {sess.actual_focused_minutes} mins ({sess.duration_minutes}m target)
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <span className="badge badge-success">{sess.session_status}</span>
                    </td>
                    <td style={{ padding: '12px 14px', color: 'var(--slate-500)' }}>
                      {sess.notes || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default FocusTimerPage;
