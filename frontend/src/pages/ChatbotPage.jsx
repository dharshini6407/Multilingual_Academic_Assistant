import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api';
import {
  Send,
  Sparkles,
  BookOpen,
  ThumbsUp,
  ThumbsDown,
  Info,
  Clock,
  CheckCircle,
  AlertCircle,
  HelpCircle,
  ChevronDown,
  Plus
} from 'lucide-react';

export const ChatbotPage = () => {
  const { user, language } = useAuth();
  const [conversations, setConversations] = useState([]);
  const [currentConvId, setCurrentConvId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState(null);
  const [feedbackSuccess, setFeedbackSuccess] = useState({});

  const messagesEndRef = useRef(null);

  // Suggested quick prompts in English, Tamil, and Tanglish
  const quickPrompts = [
    {
      label: '75% Attendance Rule',
      lang: 'EN',
      query: 'What is the minimum attendance requirement for semester examinations?'
    },
    {
      label: 'Tanglish: Condonation Fee',
      lang: 'Tanglish',
      query: 'attendance 70% irundha condonation apply panna mudiyuma fee evalo?'
    },
    {
      label: 'தமிழ்: தேர்வு விபரம்',
      lang: 'தமிழ்',
      query: 'செமஸ்டர் தேர்வுக்கான அகமதிப்பீடு மற்றும் தேர்ச்சி மதிப்பெண் எவ்வளவு?'
    },
    {
      label: 'Revaluation & Arrear',
      lang: 'EN',
      query: 'What is the procedure and timeline to apply for revaluation of exam answer sheets?'
    },
    {
      label: 'Tanglish: Fee Due Date',
      lang: 'Tanglish',
      query: 'semester fee eppo kattanum late fee fine evalo aagum?'
    }
  ];

  useEffect(() => {
    fetchConversations();
  }, []);

  useEffect(() => {
    if (currentConvId) {
      fetchMessages(currentConvId);
    }
  }, [currentConvId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const fetchConversations = async () => {
    try {
      const res = await api.get('/chat/conversations');
      if (res.success && res.conversations) {
        setConversations(res.conversations);
        if (res.conversations.length > 0 && !currentConvId) {
          setCurrentConvId(res.conversations[0].id);
        }
      }
    } catch (err) {
      console.error('Error fetching conversations:', err);
    }
  };

  const fetchMessages = async (convId) => {
    try {
      const res = await api.get(`/chat/conversations/${convId}/messages`);
      if (res.success) {
        setMessages(res.messages || []);
      }
    } catch (err) {
      console.error('Error fetching messages:', err);
    }
  };

  const handleCreateNewChat = async () => {
    try {
      const res = await api.post('/chat/conversations', {
        session_title: 'New Academic Query',
        language
      });
      if (res.success && res.conversation) {
        setConversations([res.conversation, ...conversations]);
        setCurrentConvId(res.conversation.id);
        setMessages([]);
      }
    } catch (err) {
      console.error('Failed to create new conversation:', err);
    }
  };

  const handleSendMessage = async (textToSend) => {
    const query = textToSend || inputQuery;
    if (!query.trim()) return;

    setInputQuery('');

    // Optimistically show user message
    const tempUserMsg = {
      id: `temp_${Date.now()}`,
      sender: 'user',
      message: query,
      created_at: new Date().toISOString()
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setLoading(true);

    try {
      const res = await api.post('/chat/message', {
        conversation_id: currentConvId,
        message: query
      });

      if (res.success) {
        if (!currentConvId && res.conversation_id) {
          setCurrentConvId(res.conversation_id);
          fetchConversations();
        }
        setMessages((prev) => [
          ...prev.filter((m) => m.id !== tempUserMsg.id),
          res.user_message,
          res.assistant_message
        ]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err_${Date.now()}`,
          sender: 'assistant',
          message: `Unable to process query: ${err.message}`,
          is_supported_by_docs: false
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (messageId, rating) => {
    try {
      await api.post('/chat/feedback', {
        message_id: messageId,
        rating
      });
      setFeedbackSuccess((prev) => ({ ...prev, [messageId]: rating }));
    } catch (err) {
      console.error('Feedback submission error:', err);
    }
  };

  return (
    <div style={{ display: 'flex', gap: '20px', height: 'calc(100vh - 120px)' }}>
      {/* Chat Sessions Sidebar */}
      <div
        className="glass-card"
        style={{
          width: '260px',
          display: 'flex',
          flexDirection: 'column',
          padding: '16px',
          borderRadius: '16px'
        }}
      >
        <button
          onClick={handleCreateNewChat}
          className="btn btn-primary btn-sm"
          style={{ width: '100%', marginBottom: '14px', gap: '6px' }}
        >
          <Plus size={16} />
          <span>New Academic Inquiry</span>
        </button>

        <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--slate-400)', textTransform: 'uppercase', marginBottom: '8px' }}>
          Recent Conversations
        </div>

        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {conversations.length === 0 ? (
            <div style={{ fontSize: '12px', color: 'var(--slate-400)', padding: '10px' }}>
              No previous conversations.
            </div>
          ) : (
            conversations.map((c) => (
              <div
                key={c.id}
                onClick={() => setCurrentConvId(c.id)}
                style={{
                  padding: '10px 12px',
                  borderRadius: 'var(--radius-md)',
                  background: currentConvId === c.id ? 'var(--primary-50)' : 'transparent',
                  border: `1px solid ${currentConvId === c.id ? 'var(--primary-200)' : 'transparent'}`,
                  cursor: 'pointer',
                  fontSize: '13px',
                  fontWeight: currentConvId === c.id ? 600 : 500,
                  color: currentConvId === c.id ? 'var(--primary-700)' : 'var(--slate-700)',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap'
                }}
              >
                💬 {c.session_title}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div
        className="glass-card"
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          borderRadius: '16px',
          overflow: 'hidden'
        }}
      >
        {/* Chat Header */}
        <div
          style={{
            padding: '14px 20px',
            borderBottom: '1px solid var(--slate-200)',
            background: 'var(--white)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '10px',
                background: 'linear-gradient(135deg, var(--primary-600), var(--accent-purple))',
                color: 'white',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <Sparkles size={18} />
            </div>
            <div>
              <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--slate-900)' }}>
                Official Academic RAG Assistant
              </div>
              <div style={{ fontSize: '11px', color: 'var(--slate-500)' }}>
                Powered by verified college regulations • English, தமிழ் & Tanglish
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '6px' }}>
            <span className="badge badge-info">PDF Citing</span>
            <span className="badge badge-primary">Zero Hallucination Policy</span>
          </div>
        </div>

        {/* Messages Stream */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {messages.length === 0 ? (
            <div style={{ margin: 'auto', maxWidth: '520px', textAlign: 'center', padding: '20px 0' }}>
              <div
                style={{
                  width: '56px',
                  height: '56px',
                  borderRadius: '18px',
                  background: 'var(--primary-50)',
                  color: 'var(--primary-600)',
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '14px'
                }}
              >
                <BookOpen size={28} />
              </div>
              <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--slate-800)' }}>
                Ask Any Academic Regulation or Examination Question
              </h3>
              <p style={{ fontSize: '13px', color: 'var(--slate-500)', marginTop: '6px' }}>
                Type your question in <strong>English</strong>, <strong>தமிழ்</strong>, or <strong>Tanglish</strong>.
                Answers are backed by official college handbooks with exact page citations.
              </p>

              {/* Quick Prompts */}
              <div style={{ marginTop: '20px', display: 'flex', flexWrap: 'wrap', gap: '8px', justifyContent: 'center' }}>
                {quickPrompts.map((p, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendMessage(p.query)}
                    className="btn btn-secondary btn-sm"
                    style={{ fontSize: '12px', background: 'var(--white)', padding: '6px 12px' }}
                  >
                    <span>{p.label}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((m) => {
              const isUser = m.sender === 'user';
              return (
                <div
                  key={m.id}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: isUser ? 'flex-end' : 'flex-start'
                  }}
                >
                  <div className={isUser ? 'chat-bubble-user' : 'chat-bubble-assistant'}>
                    <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.5', fontSize: '14px' }}>
                      {m.message}
                    </div>

                    {/* Citations section */}
                    {!isUser && m.retrieved_sources && m.retrieved_sources.length > 0 && (
                      <div style={{ marginTop: '12px', paddingTop: '10px', borderTop: '1px solid var(--slate-200)' }}>
                        <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--slate-500)', textTransform: 'uppercase', marginBottom: '4px' }}>
                          Verified Source Citations:
                        </div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                          {m.retrieved_sources.map((src, idx) => (
                            <button
                              key={idx}
                              onClick={() => setSelectedCitation(src)}
                              className="citation-pill"
                              style={{ border: 'none' }}
                            >
                              <BookOpen size={12} color="var(--primary-600)" />
                              <span>{src.document_name} • Page {src.page_number}</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Feedback buttons */}
                    {!isUser && m.id && typeof m.id === 'number' && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '10px', fontSize: '11px', color: 'var(--slate-400)' }}>
                        <span>Helpful?</span>
                        <button
                          onClick={() => handleFeedback(m.id, 'helpful')}
                          style={{
                            background: 'transparent',
                            border: 'none',
                            cursor: 'pointer',
                            color: feedbackSuccess[m.id] === 'helpful' ? 'var(--success)' : 'var(--slate-400)'
                          }}
                          title="Thumbs Up"
                        >
                          <ThumbsUp size={14} />
                        </button>
                        <button
                          onClick={() => handleFeedback(m.id, 'unhelpful')}
                          style={{
                            background: 'transparent',
                            border: 'none',
                            cursor: 'pointer',
                            color: feedbackSuccess[m.id] === 'unhelpful' ? 'var(--danger)' : 'var(--slate-400)'
                          }}
                          title="Thumbs Down"
                        >
                          <ThumbsDown size={14} />
                        </button>
                        {feedbackSuccess[m.id] && (
                          <span style={{ color: 'var(--success)', fontWeight: 600 }}>Recorded ✓</span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}

          {loading && (
            <div style={{ alignSelf: 'flex-start' }} className="chat-bubble-assistant">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--primary-600)', fontSize: '13px', fontWeight: 500 }}>
                <Sparkles size={16} />
                <span>Searching verified official documents & generating citations...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div style={{ padding: '14px 20px', background: 'var(--white)', borderTop: '1px solid var(--slate-200)' }}>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            style={{ display: 'flex', gap: '10px' }}
          >
            <input
              type="text"
              className="form-input"
              placeholder="Ask in English, தமிழ், or Tanglish (e.g. 'attendance evlo venum?', 'sem exam passing marks?')..."
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              disabled={loading}
              style={{ flex: 1, padding: '12px 16px' }}
            />
            <button
              type="submit"
              disabled={loading || !inputQuery.trim()}
              className="btn btn-primary"
              style={{ padding: '0 20px' }}
            >
              <Send size={16} />
              <span>Send</span>
            </button>
          </form>
        </div>
      </div>

      {/* Citations Preview Popover */}
      {selectedCitation && (
        <div className="modal-overlay" onClick={() => setSelectedCitation(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '600px' }}>
            <div style={{ padding: '18px 24px', borderBottom: '1px solid var(--slate-100)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <BookOpen size={18} color="var(--primary-600)" />
                <h3 style={{ fontSize: '16px', fontWeight: 700 }}>
                  {selectedCitation.document_name}
                </h3>
              </div>
              <span className="badge badge-primary">Page {selectedCitation.page_number}</span>
            </div>
            <div style={{ padding: '20px 24px', background: 'var(--slate-50)', fontSize: '13px', lineHeight: '1.6', color: 'var(--slate-700)' }}>
              <div style={{ fontWeight: 700, marginBottom: '6px', color: 'var(--slate-900)' }}>
                {selectedCitation.section_title || 'Official Document Excerpt'}
              </div>
              <div style={{ fontStyle: 'italic', background: 'white', padding: '14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--slate-200)' }}>
                "{selectedCitation.excerpt}"
              </div>
            </div>
            <div style={{ padding: '12px 24px', display: 'flex', justifyContent: 'flex-end', borderTop: '1px solid var(--slate-100)' }}>
              <button onClick={() => setSelectedCitation(null)} className="btn btn-secondary btn-sm">
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatbotPage;
