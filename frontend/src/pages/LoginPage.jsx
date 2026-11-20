import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { BookOpen, ShieldCheck, UserCheck, AlertCircle, Sparkles } from 'lucide-react';

export const LoginPage = () => {
  const { login, register } = useAuth();
  const [isRegister, setIsRegister] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Form states
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState('student');
  const [department, setDepartment] = useState('Computer Science and Engineering');
  const [yearOfStudy, setYearOfStudy] = useState(3);
  const [semester, setSemester] = useState(5);
  const [preferredLanguage, setPreferredLanguage] = useState('en');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isRegister) {
        await register({
          email,
          password,
          full_name: fullName,
          role,
          department,
          year_of_study: Number(yearOfStudy),
          semester: Number(semester),
          preferred_language: preferredLanguage
        });
      } else {
        await login(email, password);
      }
    } catch (err) {
      setError(err.message || 'Authentication failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = (demoEmail, demoPass) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setIsRegister(false);
    setError('');
    login(demoEmail, demoPass).catch((err) => setError(err.message));
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px',
        background: 'radial-gradient(circle at 10% 20%, rgba(37, 99, 235, 0.08) 0%, rgba(240, 247, 255, 0.9) 90%)'
      }}
    >
      <div
        className="glass-card"
        style={{
          width: '100%',
          maxWidth: isRegister ? '600px' : '460px',
          padding: '36px',
          borderRadius: '24px'
        }}
      >
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div
            style={{
              width: '54px',
              height: '54px',
              borderRadius: '16px',
              background: 'linear-gradient(135deg, var(--primary-600), var(--primary-800))',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              boxShadow: '0 8px 20px rgba(37, 99, 235, 0.3)',
              marginBottom: '16px'
            }}
          >
            <BookOpen size={28} />
          </div>
          <h2 style={{ fontSize: '24px', fontWeight: 800, color: 'var(--slate-900)' }}>
            Multilingual Academic Assistant
          </h2>
          <p style={{ fontSize: '14px', color: 'var(--slate-500)', marginTop: '6px' }}>
            Smart Academic Alerts & Personalized Study Planning
          </p>
        </div>

        {error && (
          <div
            style={{
              background: 'var(--danger-bg)',
              border: '1px solid #fecaca',
              color: '#991b1b',
              padding: '12px 16px',
              borderRadius: 'var(--radius-md)',
              fontSize: '13px',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              marginBottom: '20px'
            }}
          >
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {isRegister && (
            <>
              <div className="form-group">
                <label className="form-label">Full Name</label>
                <input
                  type="text"
                  required
                  className="form-input"
                  placeholder="e.g. Aravindhan Sundaram"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                <div className="form-group">
                  <label className="form-label">Account Role</label>
                  <select
                    className="form-select"
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                  >
                    <option value="student">Student</option>
                    <option value="admin">Administrator / Faculty</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Preferred Language</label>
                  <select
                    className="form-select"
                    value={preferredLanguage}
                    onChange={(e) => setPreferredLanguage(e.target.value)}
                  >
                    <option value="en">English</option>
                    <option value="ta">Tamil (தமிழ்)</option>
                    <option value="tanglish">Tanglish</option>
                  </select>
                </div>
              </div>

              {role === 'student' && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                  <div className="form-group">
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
                  <div className="form-group">
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
                </div>
              )}
            </>
          )}

          <div className="form-group">
            <label className="form-label">College Email Address</label>
            <input
              type="email"
              required
              className="form-input"
              placeholder="e.g. student@college.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              type="password"
              required
              className="form-input"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn btn-primary"
            style={{ width: '100%', padding: '12px', marginTop: '8px' }}
          >
            {loading ? 'Processing...' : isRegister ? 'Create Account' : 'Sign In to Portal'}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '16px' }}>
          <button
            onClick={() => {
              setIsRegister(!isRegister);
              setError('');
            }}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--primary-600)',
              fontSize: '13px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            {isRegister ? 'Already have an account? Sign In' : "Don't have an account? Register as Student"}
          </button>
        </div>

        {/* 1-Click Demo Evaluation Credentials */}
        <div style={{ marginTop: '28px', paddingTop: '20px', borderTop: '1px solid var(--slate-200)' }}>
          <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--slate-500)', textTransform: 'uppercase', marginBottom: '12px', letterSpacing: '0.05em' }}>
            Quick Demo Evaluation Credentials
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            <button
              type="button"
              onClick={() => handleQuickLogin('student@college.edu', 'Student@123')}
              className="btn btn-secondary btn-sm"
              style={{ padding: '8px 10px', fontSize: '12px', justifyContent: 'flex-start' }}
            >
              <UserCheck size={16} color="var(--primary-600)" />
              <div style={{ textAlign: 'left', lineHeight: '1.2' }}>
                <div style={{ fontWeight: 700 }}>Student Demo</div>
                <div style={{ fontSize: '10px', color: 'var(--slate-500)' }}>student@college.edu</div>
              </div>
            </button>
            <button
              type="button"
              onClick={() => handleQuickLogin('admin@college.edu', 'Admin@123')}
              className="btn btn-secondary btn-sm"
              style={{ padding: '8px 10px', fontSize: '12px', justifyContent: 'flex-start' }}
            >
              <ShieldCheck size={16} color="var(--primary-700)" />
              <div style={{ textAlign: 'left', lineHeight: '1.2' }}>
                <div style={{ fontWeight: 700 }}>Admin Demo</div>
                <div style={{ fontSize: '10px', color: 'var(--slate-500)' }}>admin@college.edu</div>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
