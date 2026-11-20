import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Bell, Globe, Clock, ShieldCheck, User } from 'lucide-react';

export const Navbar = ({ activeTab, setActiveTab, unreadCount = 0 }) => {
  const { user, language, setLanguage, t } = useAuth();

  const getPageTitle = () => {
    switch (activeTab) {
      case 'dashboard': return t.dashboard;
      case 'chat': return t.chatbot;
      case 'attendance': return t.attendance;
      case 'exams': return t.exams;
      case 'assignments': return t.assignments;
      case 'planner': return t.planner;
      case 'timer': return t.timer;
      case 'notifications': return t.notifications;
      case 'admin': return t.admin;
      case 'profile': return t.profile;
      default: return 'Academic Portal';
    }
  };

  return (
    <header className="navbar">
      <div className="nav-left">
        <h1 className="nav-page-title">{getPageTitle()}</h1>
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '12px',
            color: 'var(--slate-500)',
            background: 'var(--slate-100)',
            padding: '4px 10px',
            borderRadius: 'var(--radius-full)'
          }}
        >
          <Clock size={12} />
          <span>Asia/Kolkata (IST)</span>
        </span>
      </div>

      <div className="nav-actions">
        {/* Multilingual Selector: English, தமிழ், Tanglish */}
        <div className="lang-selector">
          <button
            onClick={() => setLanguage('en')}
            className={`lang-btn ${language === 'en' ? 'active' : ''}`}
            title="English"
          >
            English
          </button>
          <button
            onClick={() => setLanguage('ta')}
            className={`lang-btn ${language === 'ta' ? 'active' : ''}`}
            title="Tamil தமிழ்"
          >
            தமிழ்
          </button>
          <button
            onClick={() => setLanguage('tanglish')}
            className={`lang-btn ${language === 'tanglish' ? 'active' : ''}`}
            title="Tanglish"
          >
            Tanglish
          </button>
        </div>

        {/* Notifications Icon with Unread Counter */}
        <button
          onClick={() => setActiveTab('notifications')}
          style={{
            position: 'relative',
            background: activeTab === 'notifications' ? 'var(--primary-100)' : 'var(--white)',
            border: '1px solid var(--slate-200)',
            borderRadius: '50%',
            width: '40px',
            height: '40px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: activeTab === 'notifications' ? 'var(--primary-700)' : 'var(--slate-700)',
            cursor: 'pointer',
            transition: 'all 0.18s ease'
          }}
          title={`${unreadCount} Unread Notifications`}
        >
          <Bell size={18} />
          {unreadCount > 0 && (
            <span
              style={{
                position: 'absolute',
                top: '-4px',
                right: '-4px',
                background: 'var(--danger)',
                color: 'white',
                fontSize: '11px',
                fontWeight: 700,
                width: '18px',
                height: '18px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 2px 6px rgba(239, 68, 68, 0.4)'
              }}
            >
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </button>

        {/* Role Pill */}
        <div
          onClick={() => setActiveTab('profile')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 12px',
            background: user?.role === 'admin' ? '#eff6ff' : 'var(--white)',
            border: '1px solid var(--slate-200)',
            borderRadius: 'var(--radius-full)',
            cursor: 'pointer'
          }}
        >
          {user?.role === 'admin' ? (
            <ShieldCheck size={16} color="var(--primary-700)" />
          ) : (
            <User size={16} color="var(--slate-600)" />
          )}
          <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--slate-800)' }}>
            {user?.profile?.full_name?.split(' ')[0] || user?.email?.split('@')[0]}
          </span>
          <span
            style={{
              fontSize: '10px',
              fontWeight: 700,
              textTransform: 'uppercase',
              background: user?.role === 'admin' ? 'var(--primary-600)' : 'var(--slate-200)',
              color: user?.role === 'admin' ? 'white' : 'var(--slate-700)',
              padding: '2px 6px',
              borderRadius: 'var(--radius-full)'
            }}
          >
            {user?.role}
          </span>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
