import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../api';

const AuthContext = createContext(null);

export const translations = {
  en: {
    dashboard: 'Dashboard',
    chatbot: 'Academic Chatbot',
    attendance: 'Attendance Tracker',
    exams: 'Exam Calendar',
    assignments: 'Assignments',
    planner: 'Study Planner',
    timer: 'Focus Timer',
    notifications: 'Notifications',
    admin: 'Admin Control',
    profile: 'Profile Settings',
    logout: 'Logout',
    welcome: 'Welcome back',
    role: 'Role',
    student: 'Student',
    adminRole: 'Administrator',
    overallAttendance: 'Overall Attendance',
    upcomingExams: 'Upcoming Examinations',
    pendingAssignments: 'Pending Assignments',
    studyProgress: 'Study Plan Progress',
    unreadAlerts: 'Unread Smart Alerts'
  },
  ta: {
    dashboard: 'டாஷ்போர்டு',
    chatbot: 'கல்வி சாட்பாட்',
    attendance: 'வருகைப் பதிவு',
    exams: 'தேர்வு அட்டவணை',
    assignments: 'ஒப்படைப்புகள்',
    planner: 'படிப்புத் திட்டம்',
    timer: 'கவன டைமர்',
    notifications: 'அறிவிப்புகள்',
    admin: 'நிர்வாக மையம்',
    profile: 'சுயவிவர அமைப்புகள்',
    logout: 'வெளியேறு',
    welcome: 'வணக்கம்',
    role: 'பொறுப்பு',
    student: 'மாணவர்',
    adminRole: 'நிர்வாகி',
    overallAttendance: 'மொத்த வருகை',
    upcomingExams: 'வரவிருக்கும் தேர்வுகள்',
    pendingAssignments: 'நிலுவையிலுள்ள பணிகள்',
    studyProgress: 'படிப்புத் திட்ட முன்னேற்றம்',
    unreadAlerts: 'படிக்காத எச்சரிக்கைகள்'
  },
  tanglish: {
    dashboard: 'Dashboard',
    chatbot: 'Academic Chatbot',
    attendance: 'Attendance Tracker',
    exams: 'Exam Calendar',
    assignments: 'Assignments & Work',
    planner: 'Study Planner',
    timer: 'Focus Pomodoro',
    notifications: 'Academic Alerts',
    admin: 'Admin Control',
    profile: 'Profile & Settings',
    logout: 'Sign Out',
    welcome: 'Vanakkam',
    role: 'Role',
    student: 'Student',
    adminRole: 'Staff / Admin',
    overallAttendance: 'Overall Attendance',
    upcomingExams: 'Upcoming Exams',
    pendingAssignments: 'Pending Assignments',
    studyProgress: 'Study Plan Progress',
    unreadAlerts: 'Smart Alerts'
  }
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem('academic_assistant_user');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  const [token, setToken] = useState(() => localStorage.getItem('academic_assistant_token') || null);
  const [language, setLanguageState] = useState(() => {
    return localStorage.getItem('academic_assistant_lang') || 'en';
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const handleAuthChange = () => {
      const curToken = localStorage.getItem('academic_assistant_token');
      const curUser = localStorage.getItem('academic_assistant_user');
      setToken(curToken);
      setUser(curUser ? JSON.parse(curUser) : null);
    };

    window.addEventListener('auth_state_change', handleAuthChange);
    return () => window.removeEventListener('auth_state_change', handleAuthChange);
  }, []);

  useEffect(() => {
    // Validate session on load
    const verifyUser = async () => {
      if (token) {
        try {
          const res = await api.get('/auth/me');
          if (res.success && res.user) {
            setUser(res.user);
            localStorage.setItem('academic_assistant_user', JSON.stringify(res.user));
            if (res.user.profile?.preferred_language) {
              setLanguageState(res.user.profile.preferred_language);
              localStorage.setItem('academic_assistant_lang', res.user.profile.preferred_language);
            }
          }
        } catch {
          // Token invalid, logout
          logout();
        }
      }
      setLoading(false);
    };
    verifyUser();
  }, [token]);

  const login = async (email, password) => {
    const res = await api.post('/auth/login', { email, password });
    if (res.success && res.access_token) {
      localStorage.setItem('academic_assistant_token', res.access_token);
      localStorage.setItem('academic_assistant_user', JSON.stringify(res.user));
      setToken(res.access_token);
      setUser(res.user);
      if (res.user.profile?.preferred_language) {
        setLanguageState(res.user.profile.preferred_language);
      }
      return res;
    }
    throw new Error(res.message || 'Login failed');
  };

  const register = async (userData) => {
    const res = await api.post('/auth/register', userData);
    if (res.success && res.access_token) {
      localStorage.setItem('academic_assistant_token', res.access_token);
      localStorage.setItem('academic_assistant_user', JSON.stringify(res.user));
      setToken(res.access_token);
      setUser(res.user);
      return res;
    }
    throw new Error(res.message || 'Registration failed');
  };

  const logout = () => {
    localStorage.removeItem('academic_assistant_token');
    localStorage.removeItem('academic_assistant_user');
    setToken(null);
    setUser(null);
  };

  const setLanguage = (newLang) => {
    setLanguageState(newLang);
    localStorage.setItem('academic_assistant_lang', newLang);
    if (user && token) {
      api.put('/auth/profile', { preferred_language: newLang }).catch(() => {});
    }
  };

  const t = translations[language] || translations.en;

  return (
    <AuthContext.Provider value={{
      user,
      token,
      role: user?.role || 'student',
      isAdmin: user?.role === 'admin',
      language,
      setLanguage,
      t,
      login,
      register,
      logout,
      loading
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
