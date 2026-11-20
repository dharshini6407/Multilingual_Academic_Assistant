import React from 'react';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard,
  MessageSquare,
  Percent,
  Calendar,
  FileText,
  CheckSquare,
  Timer,
  Bell,
  ShieldCheck,
  User,
  LogOut,
  Sparkles,
  BookOpen
} from 'lucide-react';

export const Sidebar = ({ activeTab, setActiveTab, unreadCount = 0 }) => {
  const { user, isAdmin, logout, t } = useAuth();

  const navItems = [
    { id: 'dashboard', label: t.dashboard, icon: LayoutDashboard },
    { id: 'chat', label: t.chatbot, icon: MessageSquare, badge: 'RAG AI' },
    { id: 'attendance', label: t.attendance, icon: Percent },
    { id: 'exams', label: t.exams, icon: Calendar },
    { id: 'assignments', label: t.assignments, icon: FileText },
    { id: 'planner', label: t.planner, icon: CheckSquare },
    { id: 'timer', label: t.timer, icon: Timer },
    {
      id: 'notifications',
      label: t.notifications,
      icon: Bell,
      badge: unreadCount > 0 ? `${unreadCount}` : null,
      badgeColor: 'danger'
    }
  ];

  if (isAdmin) {
    navItems.push({
      id: 'admin',
      label: t.admin,
      icon: ShieldCheck,
      badge: 'Admin'
    });
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <BookOpen size={22} />
        </div>
        <div>
          <div className="sidebar-title">EduAssist AI</div>
          <div className="sidebar-subtitle">Academic Suite</div>
        </div>
      </div>

      <div className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`nav-link ${isActive ? 'active' : ''}`}
            >
              <Icon size={18} />
              <span>{item.label}</span>
              {item.badge && (
                <span
                  className="nav-badge"
                  style={item.badgeColor === 'danger' ? { background: '#fee2e2', color: '#b91c1c' } : {}}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* User profile footer */}
      <div style={{ padding: '16px 20px', borderTop: '1px solid var(--slate-100)', background: 'var(--slate-50)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, var(--primary-500), var(--primary-700))',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontWeight: 700,
              fontSize: '14px'
            }}
          >
            {user?.profile?.full_name ? user.profile.full_name[0].toUpperCase() : 'U'}
          </div>
          <div style={{ minWidth: 0, flex: 1 }}>
            <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--slate-900)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {user?.profile?.full_name || user?.email}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--slate-500)', textTransform: 'capitalize' }}>
              {user?.role} • {user?.profile?.semester ? `Sem ${user.profile.semester}` : 'CSE'}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={() => setActiveTab('profile')}
            className="btn btn-secondary btn-sm"
            style={{ flex: 1, padding: '6px' }}
            title="Profile & Settings"
          >
            <User size={14} />
            <span>Profile</span>
          </button>
          <button
            onClick={logout}
            className="btn btn-secondary btn-sm"
            style={{ padding: '6px 10px', color: 'var(--danger)' }}
            title="Log Out"
          >
            <LogOut size={14} />
          </button>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
