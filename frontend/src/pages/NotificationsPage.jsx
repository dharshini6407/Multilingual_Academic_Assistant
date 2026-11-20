import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api';
import {
  Bell,
  CheckCircle,
  Clock,
  Trash2,
  Calendar,
  FileText,
  AlertTriangle,
  Sparkles,
  Inbox
} from 'lucide-react';

export const NotificationsPage = () => {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [filterType, setFilterType] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchNotifications();
  }, [filterType]);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const params = filterType !== 'all' ? { type: filterType } : {};
      const res = await api.get('/notifications', params);
      if (res.success) {
        setNotifications(res.notifications || []);
        setUnreadCount(res.unread_count || 0);
      }
    } catch (err) {
      console.error('Error fetching notifications:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAsRead = async (notifId) => {
    try {
      await api.put(`/notifications/${notifId}/read`);
      setNotifications((prev) =>
        prev.map((n) => (n.id === notifId ? { ...n, is_read: true } : n))
      );
      setUnreadCount((c) => Math.max(0, c - 1));
    } catch (err) {
      alert(err.message);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.put('/notifications/read-all');
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDeleteNotif = async (notifId) => {
    try {
      await api.delete(`/notifications/${notifId}`);
      setNotifications((prev) => prev.filter((n) => n.id !== notifId));
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
            Smart Academic Alert Center
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--slate-500)', marginTop: '2px' }}>
            In-app notifications for examinations (7d, 3d, 1d & exam day), assignment deadlines, and activities.
          </p>
        </div>

        {unreadCount > 0 && (
          <button onClick={handleMarkAllRead} className="btn btn-secondary btn-sm">
            <CheckCircle size={15} />
            <span>Mark All as Read ({unreadCount})</span>
          </button>
        )}
      </div>

      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '4px' }}>
        {[
          { id: 'all', label: 'All Alerts' },
          { id: 'exam', label: 'Exam Alerts 🎓' },
          { id: 'assignment', label: 'Assignments' },
          { id: 'activity', label: 'Activities' },
          { id: 'system', label: 'System' }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setFilterType(tab.id)}
            className="btn btn-sm"
            style={{
              background: filterType === tab.id ? 'var(--primary-700)' : 'var(--white)',
              color: filterType === tab.id ? 'white' : 'var(--slate-700)',
              border: `1px solid ${filterType === tab.id ? 'var(--primary-700)' : 'var(--slate-200)'}`,
              borderRadius: 'var(--radius-full)'
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Notifications List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px' }}>Loading alerts...</div>
        ) : notifications.length === 0 ? (
          <div className="glass-card" style={{ padding: '40px', textAlign: 'center', color: 'var(--slate-500)' }}>
            <Inbox size={36} color="var(--slate-400)" style={{ margin: '0 auto 12px' }} />
            <div style={{ fontWeight: 600 }}>No alerts in this category.</div>
          </div>
        ) : (
          notifications.map((n) => {
            const isExamDay = n.title?.includes('All the Best for Your Exam');
            return (
              <div
                key={n.id}
                className="glass-card glass-card-hover"
                style={{
                  padding: '18px 22px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  gap: '16px',
                  background: isExamDay
                    ? 'linear-gradient(135deg, rgba(239, 246, 255, 0.95), rgba(219, 234, 254, 0.95))'
                    : n.is_read ? 'var(--white)' : 'rgba(240, 247, 255, 0.85)',
                  borderLeft: `5px solid ${
                    isExamDay ? 'var(--primary-600)' :
                    n.priority === 'urgent' ? 'var(--danger)' :
                    n.priority === 'high' ? 'var(--warning)' : 'var(--primary-500)'
                  }`
                }}
              >
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <span className={`badge ${
                      n.notification_type === 'exam' ? 'badge-primary' :
                      n.notification_type === 'assignment' ? 'badge-warning' : 'badge-info'
                    }`}>
                      {n.notification_type.toUpperCase()}
                    </span>
                    {!n.is_read && (
                      <span className="badge badge-danger" style={{ fontSize: '10px' }}>
                        UNREAD
                      </span>
                    )}
                    <span style={{ fontSize: '12px', color: 'var(--slate-400)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Clock size={12} />
                      {n.created_at ? new Date(n.created_at).toLocaleString() : ''}
                    </span>
                  </div>

                  <h4 style={{ fontSize: '16px', fontWeight: 800, color: 'var(--slate-900)' }}>
                    {n.title}
                  </h4>
                  <p style={{ fontSize: '13px', color: 'var(--slate-700)', marginTop: '4px', lineHeight: '1.5' }}>
                    {n.message}
                  </p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {!n.is_read && (
                    <button
                      onClick={() => handleMarkAsRead(n.id)}
                      className="btn btn-secondary btn-sm"
                      title="Mark as Read"
                      style={{ padding: '6px 12px' }}
                    >
                      <CheckCircle size={14} color="var(--success)" />
                      <span>Mark Read</span>
                    </button>
                  )}
                  <button
                    onClick={() => handleDeleteNotif(n.id)}
                    className="btn btn-secondary btn-sm"
                    title="Delete Notification"
                    style={{ padding: '6px 8px', color: 'var(--slate-400)' }}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

export default NotificationsPage;
