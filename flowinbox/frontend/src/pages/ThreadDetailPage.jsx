import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  Star, 
  Archive, 
  Trash2, 
  Sparkles, 
  Send, 
  User, 
  Bot, 
  CornerUpLeft, 
  Volume2, 
  Paperclip, 
  MessageSquare, 
  Plus, 
  CheckCircle2, 
  Clock, 
  Mail, 
  MoreHorizontal, 
  FileText, 
  Hash, 
  Bold, 
  Italic, 
  Underline, 
  Strikethrough, 
  Link as LinkIcon, 
  List, 
  ListOrdered, 
  Quote, 
  Smile, 
  Image as ImageIcon,
  Zap,
  SlidersHorizontal,
  Paperclip as AttachmentIcon
} from 'lucide-react';
import inboxApi from '../api/inbox';
import { useAuth } from '../context/AuthContext';

export default function ThreadDetailPage() {
  const { user } = useAuth();
  const { threadId } = useParams();
  const navigate = useNavigate();

  const [thread, setThread] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analysis, setAnalysis] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [activeTab, setActiveTab] = useState('tone'); // 'tone', 'needs-reply', 'follow-ups', 'granola'

  const [replyBody, setReplyBody] = useState('');
  const [sendingReply, setSendingReply] = useState(false);

  // Writing Tone Profile State
  const [writingProfile, setWritingProfile] = useState({
    greeting: 'Hi [First Name],',
    signoff: 'Best regards',
    formality: 'Direct & Professional',
    rules: [
      'Maintain clear, professional paragraph structure.',
      'State purpose in first 1-2 sentences.',
      'End with explicit next step and contact details.'
    ]
  });

  const [comments, setComments] = useState([]);
  const [showComments, setShowComments] = useState(false);
  const [newComment, setNewComment] = useState('');

  useEffect(() => {
    loadThreadDetail();
    loadToneProfile();
  }, [threadId]);

  const loadToneProfile = async () => {
    try {
      const saved = localStorage.getItem('flowinbox.writingStyle');
      if (saved) {
        setWritingProfile(JSON.parse(saved));
      } else {
        const res = await inboxApi.analyzeWritingStyle().catch(() => null);
        if (res && res.rules) {
          setWritingProfile(res);
          localStorage.setItem('flowinbox.writingStyle', JSON.stringify(res));
        }
      }
    } catch (e) {}
  };

  const loadThreadDetail = async () => {
    setLoading(true);
    try {
      const data = await inboxApi.getThreadDetail(threadId);
      setThread(data);
    } catch (err) {
      console.error('Error fetching thread detail:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeepAnalysis = async () => {
    setAnalyzing(true);
    try {
      const res = await inboxApi.analyzeThread(threadId);
      setAnalysis(res);
    } catch (err) {
      alert('Analysis error: ' + err.message);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleAutoDraftWithTone = () => {
    if (!thread) return;
    const recipientName = thread.sender ? thread.sender.split(' ')[0] : 'there';
    const draftText = `${writingProfile.greeting.replace('[First Name]', recipientName)}\n\nThank you for reaching out regarding ${thread.subject}. I have reviewed the details.\n\n• I have confirmed the requirements and timeline.\n• The updated deliverables will be shared shortly.\n\n${writingProfile.signoff}`;
    setReplyBody(draftText);
  };

  const handleSendReply = async (e) => {
    e.preventDefault();
    if (!replyBody.trim() || !thread) return;

    setSendingReply(true);
    try {
      await inboxApi.sendReply(threadId, {
        to_email: thread.sender_email || thread.sender || 'recipient@example.com',
        subject: `Re: ${thread.subject}`,
        body: replyBody
      });
      alert('Reply sent successfully via Gmail API!');
      setReplyBody('');
      loadThreadDetail();
    } catch (err) {
      alert('Failed to send reply: ' + err.message);
    } finally {
      setSendingReply(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6 max-w-5xl mx-auto flex flex-col gap-4">
        <div className="h-8 w-32 skeleton-shimmer rounded-lg" />
        <div className="h-10 w-3/4 skeleton-shimmer rounded-lg" />
        <div className="h-64 skeleton-shimmer rounded-2xl" />
      </div>
    );
  }

  if (!thread) {
    return (
      <div className="p-8 text-center text-xs text-[#5e7186]">
        Thread not found.{' '}
        <button onClick={() => navigate('/inbox')} className="text-[#2d7ed0] underline font-bold">
          Back to inbox
        </button>
      </div>
    );
  }

  return (
    <div className="flex h-full bg-[#EBF2FA] select-none p-3 gap-3 overflow-hidden">
      {/* 1. Left Nav & Tone Analysis Section (Matching Screenshot) */}
      <div className="w-[380px] shrink-0 flex gap-2">
        {/* Far Left Mini Rail Nav */}
        <div className="w-20 flex flex-col items-center gap-4 pt-4 text-[#5e7186] text-[10px] font-semibold">
          <button
            onClick={() => navigate('/inbox')}
            className="flex flex-col items-center gap-1 p-2 rounded-xl hover:bg-white/60 hover:text-[#172335] transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back</span>
          </button>

          <button
            onClick={() => setActiveTab('tone')}
            className={`flex flex-col items-center gap-1 p-2 rounded-2xl transition-all text-center ${
              activeTab === 'tone'
                ? 'bg-white text-[#2d7ed0] shadow-2xs font-bold border border-[#c9dff4]'
                : 'hover:bg-white/60 hover:text-[#172335]'
            }`}
          >
            <Volume2 className="w-4 h-4 text-[#2d7ed0]" />
            <span className="leading-tight">Writing Style & Tone</span>
          </button>

          <button
            onClick={() => setActiveTab('needs-reply')}
            className={`flex flex-col items-center gap-1 p-2 rounded-2xl transition-all text-center ${
              activeTab === 'needs-reply'
                ? 'bg-white text-[#2d7ed0] shadow-2xs font-bold border border-[#c9dff4]'
                : 'hover:bg-white/60 hover:text-[#172335]'
            }`}
          >
            <Zap className="w-4 h-4 text-[#3186D8]" />
            <span className="leading-tight">Needs Reply</span>
          </button>

          <button
            onClick={() => setActiveTab('follow-ups')}
            className={`flex flex-col items-center gap-1 p-2 rounded-2xl transition-all text-center ${
              activeTab === 'follow-ups'
                ? 'bg-white text-[#2d7ed0] shadow-2xs font-bold border border-[#c9dff4]'
                : 'hover:bg-white/60 hover:text-[#172335]'
            }`}
          >
            <Sparkles className="w-4 h-4 text-[#8C6BD9]" />
            <span className="leading-tight">Follow Ups</span>
          </button>

          <button
            onClick={() => setActiveTab('granola')}
            className={`flex flex-col items-center gap-1 p-2 rounded-2xl transition-all text-center ${
              activeTab === 'granola'
                ? 'bg-white text-[#2d7ed0] shadow-2xs font-bold border border-[#c9dff4]'
                : 'hover:bg-white/60 hover:text-[#172335]'
            }`}
          >
            <div className="w-4 h-4 rounded-full bg-[#48A97B] text-white font-bold text-[9px] flex items-center justify-center">G</div>
            <span className="leading-tight">Granola</span>
          </button>
        </div>

        {/* Writing Style & Tone Card */}
        <div className="flex-1 bg-white rounded-3xl border border-[#d7e3ee] shadow-sm p-6 flex flex-col gap-4 overflow-y-auto animate-fade-in">
          <div className="flex items-center justify-between border-b border-[#f0f5fa] pb-3">
            <h2 className="text-base font-extrabold text-[#172335]">Analyzing...</h2>
            <span className="px-2.5 py-0.5 rounded-full bg-[#e5f0fb] text-[#1d5f9f] text-[10px] font-bold">
              AI Tone Trained
            </span>
          </div>

          <div className="text-xs text-[#334155] space-y-3 leading-relaxed">
            <p className="font-medium text-[#64748B] text-[11px]">
              Extracted from your past Gmail sent email history:
            </p>

            <ul className="space-y-2.5 list-none">
              {writingProfile.rules.map((rule, idx) => (
                <li key={idx} className="flex items-start gap-2 text-xs text-[#1e293b]">
                  <span className="text-[#2563eb] font-bold">&bull;</span>
                  <span>{rule}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="mt-auto pt-4 border-t border-[#f0f5fa] flex items-center justify-between text-[11px] text-[#64748B]">
            <span>Tone Formality: <strong>{writingProfile.formality}</strong></span>
            <button
              onClick={handleAutoDraftWithTone}
              className="px-3 py-1 bg-[#2563eb] hover:bg-[#1d4ed8] text-white font-semibold rounded-xl text-xs shadow-2xs transition-all smooth-interactive"
            >
              Apply Tone
            </button>
          </div>
        </div>
      </div>

      {/* 2. Main Right Thread Content Container with Colorful Gradient Aura Frame */}
      <div className="flex-1 min-w-0 bg-gradient-to-tr from-[#60A5FA]/30 via-[#A855F7]/30 to-[#EC4899]/30 p-[2.5px] rounded-3xl shadow-xl flex flex-col overflow-hidden animate-scale-in">
        <div className="flex-1 bg-white rounded-[22px] flex flex-col min-w-0 overflow-hidden">
          {/* Thread Header Controls */}
          <div className="px-6 py-3 border-b border-[#f0f5fa] flex items-center justify-between bg-white shrink-0">
            <div className="flex items-center gap-3">
              <button onClick={() => navigate('/inbox')} className="p-1 text-[#64748B] hover:text-[#0F172A]">
                <ArrowLeft className="w-4 h-4" />
              </button>
              <button className="p-1 text-[#64748B] hover:text-[#0F172A]">
                <Archive className="w-4 h-4" />
              </button>
              <button className="p-1 text-[#64748B] hover:text-[#0F172A]">
                <Mail className="w-4 h-4" />
              </button>
              <button className="p-1 text-[#64748B] hover:text-[#0F172A]">
                <Clock className="w-4 h-4" />
              </button>
              <button className="p-1 text-[#64748B] hover:text-[#D95D5D]">
                <Trash2 className="w-4 h-4" />
              </button>
              <button className="p-1 text-[#64748B] hover:text-[#0F172A]">
                <MoreHorizontal className="w-4 h-4" />
              </button>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => navigate('/channels')}
                className="px-3 py-1 rounded-xl bg-[#F1F5F9] hover:bg-[#E2E8F0] text-[#475569] text-xs font-semibold flex items-center gap-1 transition-colors"
              >
                <Hash className="w-3.5 h-3.5 text-[#2563eb]" />
                <span>Add channel</span>
              </button>

                <div className="w-6 h-6 rounded-full bg-[#2563eb] text-white text-[10px] font-bold flex items-center justify-center ring-2 ring-white">
                  {user?.full_name ? user.full_name.charAt(0) : 'U'}
                </div>
                <div className="w-6 h-6 rounded-full bg-[#9333ea] text-white text-[10px] font-bold flex items-center justify-center ring-2 ring-white">AI</div>
              </div>

              <button
                onClick={() => setShowComments((prev) => !prev)}
                className="px-3 py-1 rounded-xl border border-[#CBD5E1] text-[#334155] text-xs font-bold flex items-center gap-1.5 hover:bg-[#F8FAFC] transition-colors"
              >
                <MessageSquare className="w-3.5 h-3.5 text-[#2563eb]" />
                <span>Comment</span>
              </button>
            </div>

          {/* Thread Subject Title */}
          <div className="px-8 pt-5 pb-2 border-b border-[#F1F5F9]">
            <h1 className="text-xl font-extrabold text-[#0F172A]">
              {thread.subject || 'Untitled thread'}
            </h1>
          </div>

          {/* Messages & Attachments Body */}
          <div className="flex-1 overflow-y-auto p-8 flex flex-col gap-6 bg-[#FAFAFA]/50">
            {thread.emails && thread.emails.length > 0 ? (
              thread.emails.map((msg) => (
                <div key={msg.id} className="flex flex-col gap-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <div className="w-8 h-8 rounded-full bg-[#2563eb] text-white font-bold text-xs flex items-center justify-center shadow-xs">
                        {msg.sender ? msg.sender.charAt(0).toUpperCase() : 'U'}
                      </div>
                      <div>
                        <div className="text-xs font-bold text-[#0F172A]">{msg.sender}</div>
                        <div className="text-[11px] text-[#64748B]">{msg.sender_email || 'sender@example.com'}</div>
                      </div>
                    </div>
                    <span className="text-[11px] text-[#94A3B8]">
                      {new Date(msg.sent_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                    </span>
                  </div>

                  <div className="p-4 bg-[#F8FAFC] border border-[#E2E8F0] rounded-2xl text-xs text-[#1E293B] whitespace-pre-wrap leading-relaxed">
                    {msg.body_text}
                  </div>

                  {/* PDF Attachment Card Mockup (Matching Screenshot) */}
                  <div className="p-3 bg-white border border-[#E2E8F0] rounded-2xl w-64 flex items-center gap-3 shadow-2xs hover:border-[#3B82F6] transition-colors cursor-pointer">
                    <div className="w-8 h-8 rounded-xl bg-[#FEF2F2] text-[#EF4444] font-bold text-[10px] flex items-center justify-center shrink-0">
                      PDF
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="text-xs font-semibold text-[#0F172A] truncate">5_6287509195637923910.pdf</div>
                      <div className="text-[10px] text-[#64748B]">267 KB</div>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="flex flex-col gap-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-full bg-[#2563eb] text-white font-bold text-xs flex items-center justify-center">
                    {thread.sender ? thread.sender.charAt(0).toUpperCase() : 'A'}
                  </div>
                  <div>
                    <div className="text-xs font-bold text-[#0F172A]">{thread.sender || 'Unknown sender'}</div>
                    <div className="text-[11px] text-[#64748B]">{thread.sender_email || ''}</div>
                  </div>
                </div>

                <div className="p-4 bg-[#F8FAFC] border border-[#E2E8F0] rounded-2xl text-xs text-[#1E293B] whitespace-pre-wrap leading-relaxed">
                  {thread.snippet || 'No email snippet provided.'}
                </div>

                <div className="p-3 bg-white border border-[#E2E8F0] rounded-2xl w-64 flex items-center gap-3 shadow-2xs hover:border-[#3B82F6] transition-colors cursor-pointer">
                  <div className="w-8 h-8 rounded-xl bg-[#FEF2F2] text-[#EF4444] font-bold text-[10px] flex items-center justify-center shrink-0">
                    PDF
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="text-xs font-semibold text-[#0F172A] truncate">5_6287509195637923910.pdf</div>
                    <div className="text-[10px] text-[#64748B]">267 KB</div>
                  </div>
                </div>
              </div>
            )}

            {/* Comments drawer if toggled */}
            {showComments && (
              <div className="p-4 bg-[#F8FAFC] border border-[#CBD5E1] rounded-2xl flex flex-col gap-3 animate-fade-in">
                <div className="text-xs font-bold text-[#0F172A]">Thread Collaboration Comments</div>
                {comments.map((c) => (
                  <div key={c.id} className="p-2.5 bg-white border border-[#E2E8F0] rounded-xl text-xs">
                    <div className="font-semibold text-[#0F172A] mb-0.5">{c.author}</div>
                    <p className="text-[#475569]">{c.text}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Reply Box Composer Container with Rich Formatting */}
          <div className="p-4 border-t border-[#F1F5F9] bg-white flex flex-col gap-2">
            {/* Top Toolbar: AI Sparkle Badge + Rich Text Toolbar */}
            <div className="flex items-center justify-between px-1">
              <button
                type="button"
                onClick={handleAutoDraftWithTone}
                className="px-3 py-1 rounded-xl bg-[#EFF6FF] border border-[#BFDBFE] text-[#2563eb] text-xs font-bold flex items-center gap-1.5 shadow-2xs hover:bg-[#DBEAFE] transition-colors"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>✨ Hit Ctrl + Enter to send (Tone Matched)</span>
              </button>

              <div className="flex items-center gap-1 text-[#64748B]">
                <button className="p-1 hover:text-[#0F172A] rounded"><Bold className="w-3.5 h-3.5" /></button>
                <button className="p-1 hover:text-[#0F172A] rounded"><Italic className="w-3.5 h-3.5" /></button>
                <button className="p-1 hover:text-[#0F172A] rounded"><Underline className="w-3.5 h-3.5" /></button>
                <button className="p-1 hover:text-[#0F172A] rounded"><Strikethrough className="w-3.5 h-3.5" /></button>
                <span className="w-[1px] h-3 bg-[#CBD5E1] mx-1" />
                <button className="p-1 hover:text-[#0F172A] rounded"><LinkIcon className="w-3.5 h-3.5" /></button>
                <button className="p-1 hover:text-[#0F172A] rounded"><List className="w-3.5 h-3.5" /></button>
                <button className="p-1 hover:text-[#0F172A] rounded"><ListOrdered className="w-3.5 h-3.5" /></button>
                <button className="p-1 hover:text-[#0F172A] rounded"><Quote className="w-3.5 h-3.5" /></button>
              </div>
            </div>

            {/* Textarea */}
            <textarea
              rows={3}
              value={replyBody}
              onChange={(e) => setReplyBody(e.target.value)}
              placeholder="Reply all..."
              className="w-full p-3 bg-[#F8FAFC] border border-[#E2E8F0] rounded-2xl text-xs text-[#0F172A] focus:outline-none focus:border-[#2563eb] focus:ring-2 focus:ring-[#2563eb]/20 resize-none transition-all"
            />

            {/* Bottom Actions Bar */}
            <div className="flex items-center justify-between pt-1">
              <div className="flex items-center gap-2 text-[#64748B]">
                <button className="p-1 hover:text-[#0F172A] text-xs font-bold">Aa</button>
                <button className="p-1 hover:text-[#0F172A] text-xs font-bold">@</button>
                <button className="p-1 hover:text-[#0F172A]"><Smile className="w-4 h-4" /></button>
                <button className="p-1 hover:text-[#0F172A]"><ImageIcon className="w-4 h-4" /></button>
                <button className="p-1 hover:text-[#0F172A]"><AttachmentIcon className="w-4 h-4" /></button>
                <button className="p-1 hover:text-[#D95D5D]"><Trash2 className="w-4 h-4" /></button>
              </div>

              <button
                onClick={handleSendReply}
                disabled={sendingReply || !replyBody.trim()}
                className="px-5 py-2 bg-gradient-to-r from-[#2563eb] to-[#9333ea] hover:opacity-95 text-white text-xs font-bold rounded-2xl flex items-center gap-1.5 shadow-md transition-all smooth-interactive disabled:opacity-40"
              >
                <span>Send</span>
                <Sparkles className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

