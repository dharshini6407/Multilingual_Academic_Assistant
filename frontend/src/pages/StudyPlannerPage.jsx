import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api';
import {
  CheckSquare,
  Sparkles,
  Calendar,
  Clock,
  Plus,
  Trash2,
  CheckCircle,
  Circle,
  Sliders,
  TrendingUp,
  AlertCircle
} from 'lucide-react';

export const StudyPlannerPage = () => {
  const { user } = useAuth();
  const [plans, setPlans] = useState([]);
  const [currentPlan, setCurrentPlan] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  // Modals & form
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [taskTitle, setTaskTitle] = useState('');
  const [taskSubjectId, setTaskSubjectId] = useState('');
  const [taskEstMinutes, setTaskEstMinutes] = useState(45);
  const [taskPriority, setTaskPriority] = useState('medium');
  const [taskDate, setTaskDate] = useState('');
  const [taskTime, setTaskTime] = useState('18:00:00');

  useEffect(() => {
    fetchPlans();
    fetchSubjects();
  }, []);

  useEffect(() => {
    if (currentPlan) {
      fetchPlanTasks(currentPlan.id);
    }
  }, [currentPlan]);

  const fetchPlans = async () => {
    try {
      setLoading(true);
      const res = await api.get('/planner/plans');
      if (res.success && res.plans) {
        setPlans(res.plans);
        if (res.plans.length > 0 && !currentPlan) {
          setCurrentPlan(res.plans[0]);
        }
      }
    } catch (err) {
      console.error('Failed to fetch study plans:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchSubjects = async () => {
    try {
      const res = await api.get('/admin/subjects');
      if (res.success && res.subjects) {
        setSubjects(res.subjects);
        if (res.subjects.length > 0 && !taskSubjectId) {
          setTaskSubjectId(res.subjects[0].id);
        }
      }
    } catch {
      // Ignored for student
    }
  };

  const fetchPlanTasks = async (planId) => {
    try {
      const res = await api.get(`/planner/plans/${planId}/tasks`);
      if (res.success) {
        setTasks(res.tasks || []);
        if (res.plan) {
          setCurrentPlan(res.plan);
        }
      }
    } catch (err) {
      console.error('Failed to fetch tasks:', err);
    }
  };

  const handleToggleTask = async (taskId, currentCompleted) => {
    try {
      const res = await api.put(`/planner/tasks/${taskId}`, {
        is_completed: !currentCompleted
      });
      if (res.success) {
        setTasks((prev) =>
          prev.map((t) => (t.id === taskId ? res.task : t))
        );
        if (currentPlan) {
          setCurrentPlan((p) => ({
            ...p,
            completion_percentage: res.plan_completion_percentage
          }));
        }
      }
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDeleteTask = async (taskId) => {
    try {
      const res = await api.delete(`/planner/tasks/${taskId}`);
      if (res.success) {
        setTasks((prev) => prev.filter((t) => t.id !== taskId));
        if (currentPlan) {
          setCurrentPlan((p) => ({
            ...p,
            completion_percentage: res.plan_completion_percentage
          }));
        }
      }
    } catch (err) {
      alert(err.message);
    }
  };

  const handleSmartGenerate = async () => {
    setGenerating(true);
    try {
      const res = await api.post('/planner/generate', {
        plan_id: currentPlan?.id,
        target_hours_per_day: currentPlan?.target_hours_per_day || 3.0,
        include_upcoming_deadlines: true
      });
      if (res.success) {
        setCurrentPlan(res.plan);
        setTasks(res.tasks || []);
        fetchPlans();
      }
    } catch (err) {
      alert(err.message);
    } finally {
      setGenerating(false);
    }
  };

  const handleAddTask = async (e) => {
    e.preventDefault();
    if (!currentPlan) return;
    try {
      await api.post('/planner/tasks', {
        plan_id: currentPlan.id,
        subject_id: taskSubjectId ? Number(taskSubjectId) : null,
        title: taskTitle,
        estimated_minutes: Number(taskEstMinutes),
        priority: taskPriority,
        scheduled_date: taskDate || currentPlan.start_date,
        start_time: taskTime
      });
      setShowTaskModal(false);
      setTaskTitle('');
      fetchPlanTasks(currentPlan.id);
    } catch (err) {
      alert(err.message);
    }
  };

  // Group tasks by scheduled date
  const groupedTasks = tasks.reduce((acc, t) => {
    const d = t.scheduled_date || 'Unscheduled';
    if (!acc[d]) acc[d] = [];
    acc[d].push(t);
    return acc;
  }, {});

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Banner & Smart Generator */}
      <div
        className="glass-card"
        style={{
          padding: '24px 30px',
          background: 'linear-gradient(135deg, #4338ca, #6366f1)',
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
            Personalized Academic Study Planner
          </div>
          <h2 style={{ fontSize: '24px', fontWeight: 800, marginTop: '4px' }}>
            {currentPlan?.title || 'Weekly Study Strategy'}
          </h2>
          <div style={{ display: 'flex', gap: '16px', fontSize: '13px', opacity: 0.9, marginTop: '6px' }}>
            <span>Target: {currentPlan?.target_hours_per_day || 3.0} hrs/day</span>
            <span>Period: {currentPlan?.start_date} to {currentPlan?.end_date}</span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <button
            onClick={handleSmartGenerate}
            disabled={generating}
            style={{
              background: 'white',
              color: 'var(--primary-700)',
              border: 'none',
              padding: '12px 22px',
              borderRadius: 'var(--radius-full)',
              fontWeight: 700,
              fontSize: '14px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              cursor: 'pointer',
              boxShadow: '0 4px 14px rgba(0,0,0,0.15)'
            }}
          >
            <Sparkles size={16} color="var(--primary-600)" />
            <span>{generating ? 'Calculating Schedule...' : 'Regenerate Smart Schedule'}</span>
          </button>
          <button
            onClick={() => setShowTaskModal(true)}
            className="btn btn-secondary btn-sm"
            style={{ padding: '12px 18px', borderRadius: 'var(--radius-full)', background: 'rgba(255,255,255,0.18)', color: 'white', border: '1px solid rgba(255,255,255,0.3)' }}
          >
            <Plus size={16} />
            <span>Add Custom Task</span>
          </button>
        </div>
      </div>

      {/* Completion Metric Card */}
      <div className="glass-card" style={{ padding: '20px 26px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
          <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--slate-800)' }}>
            Plan Completion Percentage: {currentPlan?.completion_percentage || 0}%
          </span>
          <span style={{ fontSize: '12px', color: 'var(--slate-500)' }}>
            {tasks.filter((t) => t.is_completed).length} of {tasks.length} tasks finished
          </span>
        </div>
        <div className="progress-container" style={{ height: '10px' }}>
          <div
            className="progress-bar"
            style={{
              width: `${currentPlan?.completion_percentage || 0}%`,
              background: 'linear-gradient(90deg, #6366f1, #10b981)'
            }}
          />
        </div>
      </div>

      {/* Scheduled Tasks by Calendar Date */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px' }}>Loading study schedule...</div>
        ) : Object.keys(groupedTasks).length === 0 ? (
          <div className="glass-card" style={{ padding: '40px', textAlign: 'center', color: 'var(--slate-500)' }}>
            No study tasks in this plan. Click "Regenerate Smart Schedule" to auto-balance tasks based on upcoming exams and assignments!
          </div>
        ) : (
          Object.keys(groupedTasks).sort().map((dateKey) => (
            <div key={dateKey}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                <Calendar size={16} color="var(--primary-600)" />
                <h4 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--slate-900)' }}>
                  {dateKey}
                </h4>
                <span className="badge badge-info" style={{ fontSize: '11px' }}>
                  {groupedTasks[dateKey].length} {groupedTasks[dateKey].length === 1 ? 'task' : 'tasks'}
                </span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {groupedTasks[dateKey].map((task) => (
                  <div
                    key={task.id}
                    className="glass-card"
                    style={{
                      padding: '14px 20px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      background: task.is_completed ? 'var(--slate-50)' : 'var(--white)',
                      borderLeft: `5px solid ${task.is_completed ? 'var(--success)' : task.priority === 'high' ? 'var(--danger)' : 'var(--primary-500)'}`,
                      opacity: task.is_completed ? 0.8 : 1
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flex: 1, minWidth: 0 }}>
                      <button
                        onClick={() => handleToggleTask(task.id, task.is_completed)}
                        style={{
                          background: 'transparent',
                          border: 'none',
                          cursor: 'pointer',
                          color: task.is_completed ? 'var(--success)' : 'var(--slate-400)'
                        }}
                      >
                        {task.is_completed ? <CheckCircle size={22} /> : <Circle size={22} />}
                      </button>

                      <div style={{ minWidth: 0, flex: 1 }}>
                        <div
                          style={{
                            fontSize: '14px',
                            fontWeight: 700,
                            color: task.is_completed ? 'var(--slate-500)' : 'var(--slate-900)',
                            textDecoration: task.is_completed ? 'line-through' : 'none'
                          }}
                        >
                          {task.title}
                        </div>
                        <div style={{ display: 'flex', gap: '12px', fontSize: '12px', color: 'var(--slate-500)', marginTop: '2px' }}>
                          {task.subject_code && <span>{task.subject_code}</span>}
                          <span>Start: {task.start_time}</span>
                          <span>Est: {task.estimated_minutes} mins</span>
                        </div>
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span className={`badge ${task.priority === 'high' ? 'badge-danger' : task.priority === 'medium' ? 'badge-warning' : 'badge-info'}`}>
                        {task.priority}
                      </span>
                      <button
                        onClick={() => handleDeleteTask(task.id)}
                        style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--slate-400)' }}
                        title="Delete Task"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Add Custom Task Modal */}
      {showTaskModal && (
        <div className="modal-overlay" onClick={() => setShowTaskModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '520px' }}>
            <form onSubmit={handleAddTask}>
              <div style={{ padding: '18px 24px', borderBottom: '1px solid var(--slate-100)' }}>
                <h3 style={{ fontSize: '18px', fontWeight: 700 }}>Add Study Task</h3>
              </div>

              <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div className="form-group" style={{ margin: 0 }}>
                  <label className="form-label">Subject</label>
                  <select
                    className="form-select"
                    value={taskSubjectId}
                    onChange={(e) => setTaskSubjectId(e.target.value)}
                  >
                    <option value="">General Study</option>
                    {subjects.map((s) => (
                      <option key={s.id} value={s.id}>{s.code} - {s.name}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group" style={{ margin: 0 }}>
                  <label className="form-label">Task Title</label>
                  <input
                    type="text"
                    required
                    className="form-input"
                    placeholder="e.g. Solve Previous Year Question Paper"
                    value={taskTitle}
                    onChange={(e) => setTaskTitle(e.target.value)}
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label">Estimated Duration (mins)</label>
                    <input
                      type="number"
                      min="15"
                      step="15"
                      className="form-input"
                      value={taskEstMinutes}
                      onChange={(e) => setTaskEstMinutes(e.target.value)}
                    />
                  </div>
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label">Priority</label>
                    <select
                      className="form-select"
                      value={taskPriority}
                      onChange={(e) => setTaskPriority(e.target.value)}
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                    </select>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label">Scheduled Date</label>
                    <input
                      type="date"
                      className="form-input"
                      value={taskDate}
                      onChange={(e) => setTaskDate(e.target.value)}
                    />
                  </div>
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label">Start Time</label>
                    <input
                      type="time"
                      className="form-input"
                      value={taskTime}
                      onChange={(e) => setTaskTime(e.target.value)}
                    />
                  </div>
                </div>
              </div>

              <div style={{ padding: '16px 24px', background: 'var(--slate-50)', borderTop: '1px solid var(--slate-100)', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button type="button" onClick={() => setShowTaskModal(false)} className="btn btn-secondary btn-sm">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary btn-sm">
                  Add to Schedule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default StudyPlannerPage;
