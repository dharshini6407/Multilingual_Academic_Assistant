import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api';
import ConfirmationModal from '../components/ConfirmationModal';
import {
  ShieldCheck,
  Users,
  FileText,
  HelpCircle,
  Clock,
  Upload,
  RefreshCw,
  Trash2,
  CheckCircle,
  XCircle,
  MessageSquare,
  BookOpen,
  Send,
  Eye,
  EyeOff
} from 'lucide-react';

export const AdminPage = () => {
  const { isAdmin } = useAuth();
  const [activeTab, setActiveTab] = useState('documents'); // 'users', 'documents', 'unanswered', 'logs'
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  // Tab Data States
  const [users, setUsers] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [unanswered, setUnanswered] = useState([]);
  const [feedbacks, setFeedbacks] = useState([]);
  const [deliveryLogs, setDeliveryLogs] = useState([]);

  // Upload Form
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploadCategory, setUploadCategory] = useState('curriculum');
  const [uploadDesc, setUploadDesc] = useState('');
  const [uploading, setUploading] = useState(false);
  const [reindexing, setReindexing] = useState(false);

  // Reply Form
  const [replyTargetId, setReplyTargetId] = useState(null);
  const [replyText, setReplyText] = useState('');

  // Delete modal
  const [deleteDocTarget, setDeleteDocTarget] = useState(null);

  useEffect(() => {
    fetchAdminOverview();
  }, []);

  useEffect(() => {
    if (activeTab === 'users') fetchUsers();
    if (activeTab === 'documents') fetchDocuments();
    if (activeTab === 'unanswered') fetchUnansweredAndFeedback();
    if (activeTab === 'logs') fetchDeliveryLogs();
  }, [activeTab]);

  const fetchAdminOverview = async () => {
    try {
      setLoading(true);
      const res = await api.get('/admin/stats');
      if (res.success) {
        setStats(res.stats);
      }
    } catch (err) {
      console.error('Error fetching admin stats:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async () => {
    try {
      const res = await api.get('/admin/users');
      if (res.success) setUsers(res.users || []);
    } catch (err) {
      alert(err.message);
    }
  };

  const fetchDocuments = async () => {
    try {
      const res = await api.get('/documents');
      if (res.success) setDocuments(res.documents || []);
    } catch (err) {
      alert(err.message);
    }
  };

  const fetchUnansweredAndFeedback = async () => {
    try {
      const [uRes, fRes] = await Promise.all([
        api.get('/admin/unanswered'),
        api.get('/admin/feedback')
      ]);
      if (uRes.success) setUnanswered(uRes.questions || []);
      if (fRes.success) setFeedbacks(fRes.feedbacks || []);
    } catch (err) {
      alert(err.message);
    }
  };

  const fetchDeliveryLogs = async () => {
    try {
      const res = await api.get('/admin/delivery-logs');
      if (res.success) setDeliveryLogs(res.logs || []);
    } catch (err) {
      alert(err.message);
    }
  };

  const handleToggleUserRole = async (userId, currentRole) => {
    const nextRole = currentRole === 'admin' ? 'student' : 'admin';
    try {
      await api.put(`/admin/users/${userId}/role`, { role: nextRole });
      fetchUsers();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleToggleUserStatus = async (userId) => {
    try {
      await api.put(`/admin/users/${userId}/status`);
      fetchUsers();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleUploadDocument = async (e) => {
    e.preventDefault();
    if (!uploadFile) {
      alert('Please select a PDF document.');
      return;
    }

    const formData = new FormData();
    formData.append('file', uploadFile);
    formData.append('title', uploadTitle);
    formData.append('category', uploadCategory);
    formData.append('description', uploadDesc);

    setUploading(true);
    try {
      const res = await api.upload('/documents/upload', formData);
      if (res.success) {
        alert(res.message);
        setUploadFile(null);
        setUploadTitle('');
        setUploadDesc('');
        fetchDocuments();
        fetchAdminOverview();
      }
    } catch (err) {
      alert(err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleToggleDocStatus = async (docId) => {
    try {
      await api.put(`/documents/${docId}/toggle-status`);
      fetchDocuments();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDeleteDocument = async () => {
    if (!deleteDocTarget) return;
    try {
      await api.delete(`/documents/${deleteDocTarget.id}`);
      setDeleteDocTarget(null);
      fetchDocuments();
      fetchAdminOverview();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleReindex = async () => {
    setReindexing(true);
    try {
      const res = await api.post('/documents/reindex');
      if (res.success) {
        alert(res.message);
        fetchDocuments();
        fetchAdminOverview();
      }
    } catch (err) {
      alert(err.message);
    } finally {
      setReindexing(false);
    }
  };

  const handleReplyToQuestion = async (qId) => {
    if (!replyText.trim()) return;
    try {
      await api.post(`/admin/unanswered/${qId}/reply`, { reply: replyText });
      setReplyTargetId(null);
      setReplyText('');
      fetchUnansweredAndFeedback();
      alert('Official reply sent to student as an in-app alert!');
    } catch (err) {
      alert(err.message);
    }
  };

  if (!isAdmin) {
    return (
      <div className="glass-card" style={{ padding: '60px', textAlign: 'center', color: 'var(--danger)' }}>
        <ShieldCheck size={48} style={{ margin: '0 auto 16px' }} />
        <h2>Access Restricted</h2>
        <p style={{ marginTop: '8px' }}>Administrative role is required to access the central management console.</p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Header */}
      <div>
        <h2 style={{ fontSize: '22px', fontWeight: 800, color: 'var(--slate-900)' }}>
          College Administration & System Control Center
        </h2>
        <p style={{ fontSize: '13px', color: 'var(--slate-500)', marginTop: '2px' }}>
          Manage user credentials, upload & reindex official academic PDFs, resolve student queries, and monitor alert delivery.
        </p>
      </div>

      {/* Overview Stat Cards */}
      {stats && (
        <div className="grid-4">
          <div className="glass-card" style={{ padding: '18px' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--slate-500)' }}>Registered Students</div>
            <div style={{ fontSize: '28px', fontWeight: 800, color: 'var(--primary-700)', marginTop: '4px' }}>
              {stats.total_students}
            </div>
          </div>
          <div className="glass-card" style={{ padding: '18px' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--slate-500)' }}>Official PDF Documents</div>
            <div style={{ fontSize: '28px', fontWeight: 800, color: 'var(--slate-900)', marginTop: '4px' }}>
              {stats.total_documents} ({stats.total_indexed_chunks} chunks)
            </div>
          </div>
          <div className="glass-card" style={{ padding: '18px' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--slate-500)' }}>Pending Unanswered Queries</div>
            <div style={{ fontSize: '28px', fontWeight: 800, color: stats.pending_unanswered_questions > 0 ? 'var(--warning)' : 'var(--slate-900)', marginTop: '4px' }}>
              {stats.pending_unanswered_questions}
            </div>
          </div>
          <div className="glass-card" style={{ padding: '18px' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--slate-500)' }}>Smart Alerts Delivered</div>
            <div style={{ fontSize: '28px', fontWeight: 800, color: 'var(--success)', marginTop: '4px' }}>
              {stats.total_smart_alerts_delivered}
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--slate-200)', paddingBottom: '12px', overflowX: 'auto' }}>
        {[
          { id: 'documents', label: 'Academic PDFs & RAG Knowledge Base', icon: BookOpen },
          { id: 'users', label: 'User Accounts & Roles', icon: Users },
          { id: 'unanswered', label: 'Unanswered Queries & Feedback', icon: HelpCircle },
          { id: 'logs', label: 'Smart Alert Delivery Log', icon: Clock }
        ].map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className="btn btn-sm"
              style={{
                background: activeTab === tab.id ? 'var(--primary-700)' : 'var(--white)',
                color: activeTab === tab.id ? 'white' : 'var(--slate-700)',
                border: '1px solid var(--slate-200)'
              }}
            >
              <Icon size={15} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* TAB 1: Academic PDFs & RAG Knowledge Base */}
      {activeTab === 'documents' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Upload Form Box */}
          <div className="glass-card" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '17px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Upload size={18} color="var(--primary-600)" />
                <span>Upload Official College Academic PDF</span>
              </h3>
              <button
                onClick={handleReindex}
                disabled={reindexing}
                className="btn btn-secondary btn-sm"
                title="Re-extract and index all active PDF documents"
              >
                <RefreshCw size={14} className={reindexing ? 'spin' : ''} />
                <span>{reindexing ? 'Reindexing...' : 'Reindex All Documents'}</span>
              </button>
            </div>

            <form onSubmit={handleUploadDocument} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '14px' }}>
                <div className="form-group" style={{ margin: 0 }}>
                  <label className="form-label">Select PDF Document</label>
                  <input
                    type="file"
                    accept=".pdf"
                    required
                    className="form-input"
                    onChange={(e) => {
                      const file = e.target.files[0];
                      setUploadFile(file);
                      if (file && !uploadTitle) {
                        setUploadTitle(file.name.replace(/\.pdf$/i, '').replace(/_/g, ' '));
                      }
                    }}
                  />
                </div>
                <div className="form-group" style={{ margin: 0 }}>
                  <label className="form-label">Category</label>
                  <select
                    className="form-select"
                    value={uploadCategory}
                    onChange={(e) => setUploadCategory(e.target.value)}
                  >
                    <option value="curriculum">Curriculum & Regulations</option>
                    <option value="exam_regulations">Exam Regulations</option>
                    <option value="academic_calendar">Academic Calendar</option>
                    <option value="syllabus">Syllabus</option>
                    <option value="code_of_conduct">Code of Conduct</option>
                    <option value="hostel_rules">Hostel Rules & Fees</option>
                    <option value="scholarships">Scholarships</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                <div className="form-group" style={{ margin: 0 }}>
                  <label className="form-label">Document Title</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Autonomous Regulations 2026"
                    className="form-input"
                    value={uploadTitle}
                    onChange={(e) => setUploadTitle(e.target.value)}
                  />
                </div>
                <div className="form-group" style={{ margin: 0 }}>
                  <label className="form-label">Description</label>
                  <input
                    type="text"
                    placeholder="Summary of handbook contents..."
                    className="form-input"
                    value={uploadDesc}
                    onChange={(e) => setUploadDesc(e.target.value)}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '6px' }}>
                <button type="submit" disabled={uploading} className="btn btn-primary btn-sm">
                  <Upload size={14} />
                  <span>{uploading ? 'Parsing & Indexing PDF...' : 'Upload & Index PDF'}</span>
                </button>
              </div>
            </form>
          </div>

          {/* Document List Table */}
          <div className="glass-card" style={{ padding: '24px' }}>
            <h3 style={{ fontSize: '17px', fontWeight: 700, marginBottom: '16px' }}>
              Indexed Knowledge Base Documents
            </h3>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid var(--slate-200)', textAlign: 'left', color: 'var(--slate-500)' }}>
                    <th style={{ padding: '10px 14px' }}>Document Name</th>
                    <th style={{ padding: '10px 14px' }}>Category</th>
                    <th style={{ padding: '10px 14px' }}>Pages / Chunks</th>
                    <th style={{ padding: '10px 14px' }}>Status</th>
                    <th style={{ padding: '10px 14px' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {documents.map((doc) => (
                    <tr key={doc.id} style={{ borderBottom: '1px solid var(--slate-100)' }}>
                      <td style={{ padding: '12px 14px' }}>
                        <div style={{ fontWeight: 700, color: 'var(--slate-900)' }}>{doc.title}</div>
                        <div style={{ fontSize: '11px', color: 'var(--slate-500)' }}>{doc.file_name}</div>
                      </td>
                      <td style={{ padding: '12px 14px' }}>
                        <span className="badge badge-info">{doc.category}</span>
                      </td>
                      <td style={{ padding: '12px 14px', color: 'var(--slate-700)' }}>
                        {doc.total_pages} pages • {doc.total_chunks} searchable chunks
                      </td>
                      <td style={{ padding: '12px 14px' }}>
                        <span className={`badge ${doc.is_active ? 'badge-success' : 'badge-danger'}`}>
                          {doc.is_active ? 'Active (Searchable)' : 'Inactive (Excluded)'}
                        </span>
                      </td>
                      <td style={{ padding: '12px 14px' }}>
                        <div style={{ display: 'flex', gap: '8px' }}>
                          <button
                            onClick={() => handleToggleDocStatus(doc.id)}
                            className="btn btn-secondary btn-sm"
                            style={{ padding: '4px 8px', fontSize: '11px' }}
                            title={doc.is_active ? 'Deactivate (exclude from retrieval)' : 'Activate (include in retrieval)'}
                          >
                            {doc.is_active ? <EyeOff size={13} /> : <Eye size={13} />}
                          </button>
                          <button
                            onClick={() => setDeleteDocTarget(doc)}
                            className="btn btn-secondary btn-sm"
                            style={{ padding: '4px 8px', fontSize: '11px', color: 'var(--danger)' }}
                            title="Delete Document"
                          >
                            <Trash2 size={13} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: User Accounts & Roles */}
      {activeTab === 'users' && (
        <div className="glass-card" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '17px', fontWeight: 700, marginBottom: '16px' }}>
            Student & Faculty Accounts
          </h3>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid var(--slate-200)', textAlign: 'left', color: 'var(--slate-500)' }}>
                  <th style={{ padding: '10px 14px' }}>User Details</th>
                  <th style={{ padding: '10px 14px' }}>Email</th>
                  <th style={{ padding: '10px 14px' }}>Department</th>
                  <th style={{ padding: '10px 14px' }}>Role</th>
                  <th style={{ padding: '10px 14px' }}>Status</th>
                  <th style={{ padding: '10px 14px' }}>Manage</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} style={{ borderBottom: '1px solid var(--slate-100)' }}>
                    <td style={{ padding: '12px 14px' }}>
                      <div style={{ fontWeight: 700, color: 'var(--slate-900)' }}>
                        {u.profile?.full_name || 'Academic User'}
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--slate-500)' }}>
                        {u.profile?.register_number || `UID #${u.id}`}
                      </div>
                    </td>
                    <td style={{ padding: '12px 14px', color: 'var(--slate-700)' }}>
                      {u.email}
                    </td>
                    <td style={{ padding: '12px 14px', color: 'var(--slate-600)' }}>
                      {u.profile?.department || 'CSE'}
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <span className={`badge ${u.role === 'admin' ? 'badge-primary' : 'badge-info'}`}>
                        {u.role.toUpperCase()}
                      </span>
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <span className={`badge ${u.is_active ? 'badge-success' : 'badge-danger'}`}>
                        {u.is_active ? 'Active' : 'Disabled'}
                      </span>
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <div style={{ display: 'flex', gap: '6px' }}>
                        <button
                          onClick={() => handleToggleUserRole(u.id, u.role)}
                          className="btn btn-secondary btn-sm"
                          style={{ padding: '4px 8px', fontSize: '11px' }}
                        >
                          Make {u.role === 'admin' ? 'Student' : 'Admin'}
                        </button>
                        <button
                          onClick={() => handleToggleUserStatus(u.id)}
                          className="btn btn-secondary btn-sm"
                          style={{ padding: '4px 8px', fontSize: '11px', color: u.is_active ? 'var(--danger)' : 'var(--success)' }}
                        >
                          {u.is_active ? 'Disable' : 'Enable'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 3: Unanswered Queries & Feedback */}
      {activeTab === 'unanswered' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div className="glass-card" style={{ padding: '24px' }}>
            <h3 style={{ fontSize: '17px', fontWeight: 700, marginBottom: '14px' }}>
              Unanswered Chatbot Queries (Official Department Review)
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--slate-500)', marginBottom: '16px' }}>
              When official documents do not contain an answer, queries are routed here so administrators can supply official answers.
            </p>

            {unanswered.length === 0 ? (
              <div style={{ padding: '30px', textAlign: 'center', color: 'var(--slate-400)' }}>
                No unanswered queries pending review!
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {unanswered.map((q) => (
                  <div
                    key={q.id}
                    style={{
                      padding: '16px',
                      background: 'var(--slate-50)',
                      border: '1px solid var(--slate-200)',
                      borderRadius: 'var(--radius-md)'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div>
                        <span className="badge badge-warning" style={{ fontSize: '11px', marginRight: '8px' }}>
                          Lang: {q.detected_language}
                        </span>
                        <span className={`badge ${q.status === 'resolved' ? 'badge-success' : 'badge-danger'}`} style={{ fontSize: '11px' }}>
                          {q.status}
                        </span>
                      </div>
                      <span style={{ fontSize: '12px', color: 'var(--slate-400)' }}>{q.created_at}</span>
                    </div>

                    <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--slate-900)', marginTop: '8px' }}>
                      "{q.question}"
                    </div>

                    {q.admin_reply ? (
                      <div style={{ marginTop: '10px', padding: '10px 14px', background: '#ecfdf5', borderRadius: 'var(--radius-md)', fontSize: '13px', color: '#065f46' }}>
                        <strong>Official Reply Provided:</strong> {q.admin_reply}
                      </div>
                    ) : (
                      <div style={{ marginTop: '12px' }}>
                        {replyTargetId === q.id ? (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            <textarea
                              rows="2"
                              className="form-textarea"
                              placeholder="Write official answer from academic affairs..."
                              value={replyText}
                              onChange={(e) => setReplyText(e.target.value)}
                            />
                            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                              <button onClick={() => setReplyTargetId(null)} className="btn btn-secondary btn-sm">
                                Cancel
                              </button>
                              <button onClick={() => handleReplyToQuestion(q.id)} className="btn btn-primary btn-sm">
                                <Send size={13} />
                                <span>Send Official Reply</span>
                              </button>
                            </div>
                          </div>
                        ) : (
                          <button
                            onClick={() => {
                              setReplyTargetId(q.id);
                              setReplyText('');
                            }}
                            className="btn btn-primary btn-sm"
                            style={{ fontSize: '12px' }}
                          >
                            Reply Officially
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Student Feedback Table */}
          <div className="glass-card" style={{ padding: '24px' }}>
            <h3 style={{ fontSize: '17px', fontWeight: 700, marginBottom: '14px' }}>
              Student Chatbot Ratings & Feedback
            </h3>
            {feedbacks.length === 0 ? (
              <div style={{ padding: '20px', textAlign: 'center', color: 'var(--slate-400)' }}>
                No ratings recorded yet.
              </div>
            ) : (
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid var(--slate-200)', textAlign: 'left', color: 'var(--slate-500)' }}>
                    <th style={{ padding: '8px 12px' }}>Rating</th>
                    <th style={{ padding: '8px 12px' }}>User Comments</th>
                    <th style={{ padding: '8px 12px' }}>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {feedbacks.map((f) => (
                    <tr key={f.id} style={{ borderBottom: '1px solid var(--slate-100)' }}>
                      <td style={{ padding: '10px 12px' }}>
                        <span className={`badge ${f.rating === 'helpful' ? 'badge-success' : 'badge-danger'}`}>
                          {f.rating}
                        </span>
                      </td>
                      <td style={{ padding: '10px 12px', color: 'var(--slate-700)' }}>
                        {f.comments || '—'}
                      </td>
                      <td style={{ padding: '10px 12px', color: 'var(--slate-400)' }}>
                        {f.created_at}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* TAB 4: Smart Alert Delivery Log (Deduplication Verification) */}
      {activeTab === 'logs' && (
        <div className="glass-card" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '17px', fontWeight: 700, marginBottom: '8px' }}>
            Smart Academic Alert Delivery Audit Trail
          </h3>
          <p style={{ fontSize: '13px', color: 'var(--slate-500)', marginBottom: '16px' }}>
            Inspect delivery records verifying deduplication, restart recovery, and exact day intervals (7d, 3d, 1d, 0d).
          </p>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid var(--slate-200)', textAlign: 'left', color: 'var(--slate-500)' }}>
                  <th style={{ padding: '10px 14px' }}>Deduplication Key</th>
                  <th style={{ padding: '10px 14px' }}>Target Entity</th>
                  <th style={{ padding: '10px 14px' }}>Recipient User ID</th>
                  <th style={{ padding: '10px 14px' }}>Days Before Trigger</th>
                  <th style={{ padding: '10px 14px' }}>Delivered Timestamp</th>
                  <th style={{ padding: '10px 14px' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {deliveryLogs.map((log) => (
                  <tr key={log.id} style={{ borderBottom: '1px solid var(--slate-100)' }}>
                    <td style={{ padding: '10px 14px', fontFamily: 'monospace', color: 'var(--primary-700)' }}>
                      {log.dedup_key}
                    </td>
                    <td style={{ padding: '10px 14px', textTransform: 'capitalize' }}>
                      {log.entity_type} #{log.entity_id}
                    </td>
                    <td style={{ padding: '10px 14px', color: 'var(--slate-700)' }}>
                      Student #{log.user_id}
                    </td>
                    <td style={{ padding: '10px 14px' }}>
                      <span className="badge badge-info">
                        {log.days_before === 0 ? 'Exam Day (0d)' : `${log.days_before} days before`}
                      </span>
                    </td>
                    <td style={{ padding: '10px 14px', color: 'var(--slate-500)' }}>
                      {log.delivered_at}
                    </td>
                    <td style={{ padding: '10px 14px' }}>
                      <span className="badge badge-success">{log.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Delete Document Confirmation Modal */}
      <ConfirmationModal
        isOpen={!!deleteDocTarget}
        title="Delete Official Academic PDF"
        message={`Are you sure you want to permanently delete "${deleteDocTarget?.title}"? All indexed RAG text chunks and citations associated with this document will be removed from the searchable knowledge base.`}
        confirmText="Confirm Permanent Deletion"
        onConfirm={handleDeleteDocument}
        onClose={() => setDeleteDocTarget(null)}
      />
    </div>
  );
};

export default AdminPage;
