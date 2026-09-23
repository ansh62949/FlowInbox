import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { 
  Star, 
  Search,
  Sparkles,
  RotateCw,
  X,
  Calendar as CalendarIcon,
  Users,
  Clock
} from 'lucide-react';
import inboxApi from '../api/inbox';
import calendarApi from '../api/calendar';

export default function InboxPage() {
  const navigate = useNavigate();
  const { category: filterCategory } = useParams();

  const [threads, setThreads] = useState([]);
  const [calendarEvents, setCalendarEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('primary');
  const [showNotificationBanner, setShowNotificationBanner] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);
  const pollCountRef = useRef(0);

  const isFolderView = ['starred', 'sent', 'drafts', 'snoozed', 'trash', 'spam', 'all'].includes(filterCategory);

  const folderTitles = {
    starred: { label: 'Starred Emails', icon: '⭐' },
    sent: { label: 'Sent Mail', icon: '📤' },
    drafts: { label: 'Drafts', icon: '📝' },
    snoozed: { label: 'Snoozed Emails', icon: '⏰' },
    trash: { label: 'Trash', icon: '🗑️' },
    spam: { label: 'Spam', icon: '🚫' },
    all: { label: 'All Mail', icon: '📬' },
  };

  useEffect(() => {
    if (filterCategory) {
      if (['primary', 'needs-reply', 'follow-ups', 'calendar', 'promotions', 'social', 'noise'].includes(filterCategory)) {
        setActiveTab(filterCategory);
      }
    }
  }, [filterCategory]);

  useEffect(() => {
    if (activeTab === 'calendar' || filterCategory === 'calendar') {
      calendarApi.getEvents()
        .then((res) => setCalendarEvents(Array.isArray(res) ? res : []))
        .catch((err) => console.warn('Failed to load calendar events:', err));
    }
  }, [activeTab, filterCategory]);

  useEffect(() => {
    loadThreads(true);
    const interval = setInterval(async () => {
      pollCountRef.current += 1;
      // Every 5th poll (~40s), trigger background sync from Gmail API
      if (pollCountRef.current % 5 === 0) {
        try {
          await inboxApi.syncInbox();
        } catch (e) {
          console.warn('[InboxPage] Periodic background sync fallback:', e);
        }
      }
      loadThreads(false);
    }, 8000);
    return () => clearInterval(interval);
  }, [activeTab, filterCategory]);

  const loadThreads = async (showLoading = true) => {
    if (showLoading) setLoading(true);
    try {
      let params = {};
      const knownFolders = ['starred', 'sent', 'drafts', 'snoozed', 'trash', 'spam', 'all', 'inbox'];
      const knownCategories = ['primary', 'needs-reply', 'follow-ups', 'calendar', 'promotions', 'social', 'noise'];

      if (filterCategory && knownFolders.includes(filterCategory)) {
        params.folder = filterCategory;
      } else if (filterCategory && knownCategories.includes(filterCategory)) {
        params.category = filterCategory;
        params.folder = 'inbox';
      } else if (activeTab === 'needs-reply') {
        params.category = 'needs-reply';
      } else if (activeTab === 'follow-ups') {
        params.category = 'follow-ups';
      } else if (activeTab === 'calendar') {
        params.folder = 'all';
      } else if (activeTab && knownCategories.includes(activeTab)) {
        params.category = activeTab;
      }

      const data = await inboxApi.getThreads(params);
      let list = Array.isArray(data) ? data : [];

      if (activeTab === 'calendar' || filterCategory === 'calendar') {
        const keywords = ['interview', 'meeting', 'calendar', 'schedule', 'call', 'google meet', 'zoom', 'invitation', 'event', 'sync'];
        list = list.filter((t) => {
          const text = `${t.subject || ''} ${t.snippet || ''}`.toLowerCase();
          return keywords.some((k) => text.includes(k));
        });
      }

      setThreads(list);
    } catch (err) {
      console.error('Failed to load threads:', err);
      if (showLoading) setThreads([]);
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  const handleManualSync = async () => {
    setIsSyncing(true);
    try {
      await inboxApi.syncInbox();
      await loadThreads(false);
    } catch (err) {
      console.warn('Manual sync fallback:', err);
    } finally {
      setIsSyncing(false);
    }
  };

  const handleToggleStar = async (e, threadId, currentStarred) => {
    e.stopPropagation();
    try {
      await inboxApi.starThread(threadId, !currentStarred);
      setThreads((prev) =>
        prev.map((t) => (t.id === threadId ? { ...t, is_starred: !currentStarred } : t))
      );
    } catch (err) {
      console.error('Star error:', err);
    }
  };

  const formatTime = (isoString) => {
    if (!isoString) return '';
    if (isoString.includes('/')) return isoString;
    const date = new Date(isoString);
    const now = new Date();
    if (date.toDateString() === now.toDateString()) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
  };

  const getAvatarColor = (name) => {
    const colors = ['bg-[#3186D8]', 'bg-[#8C6BD9]', 'bg-[#48A97B]', 'bg-[#E5A93A]', 'bg-[#D77BB5]'];
    const charCode = name ? name.charCodeAt(0) : 0;
    return colors[charCode % colors.length];
  };

  const currentFolderInfo = folderTitles[filterCategory] || { label: 'Folder View', icon: '📁' };

  return (
    <div className="flex flex-col h-full bg-white select-none overflow-hidden rounded-tl-3xl border-l border-t border-[#d7e3ee] shadow-2xs">
      {/* Header Bar */}
      <div className="px-6 pt-3 border-b border-[#d7e3ee] flex items-center justify-between bg-white shrink-0">
        {isFolderView ? (
          <div className="flex items-center justify-between w-full py-2.5">
            <div className="flex items-center gap-2">
              <span className="text-base">{currentFolderInfo.icon}</span>
              <h2 className="text-sm font-bold text-[#172335]">{currentFolderInfo.label}</h2>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-[#f0f4f8] text-[#536176]">
                {threads.length} {threads.length === 1 ? 'thread' : 'threads'}
              </span>
            </div>
            <button
              onClick={() => navigate('/inbox')}
              className="text-xs font-bold text-[#2d7ed0] hover:underline"
            >
              ← Back to Inbox
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-6">
            {[
              { id: 'primary', label: 'Primary', color: 'text-[#2d7ed0]' },
              { id: 'needs-reply', label: 'Needs Reply', icon: '⚡', color: 'text-[#48A97B]' },
              { id: 'follow-ups', label: 'Follow Ups', icon: '✨', color: 'text-[#8C6BD9]' },
              { id: 'calendar', label: 'Calendar', icon: '📅', color: 'text-[#D97706]' },
              { id: 'promotions', label: 'Promotions', color: 'text-[#64788c]' },
              { id: 'social', label: 'Social', color: 'text-[#64788c]' },
              { id: 'noise', label: 'Noise', color: 'text-[#64788c]' }
            ].map((tab) => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => {
                    setActiveTab(tab.id);
                    navigate(`/inbox/${tab.id}`);
                  }}
                  className={`py-3 border-b-2 text-xs font-bold transition-all flex items-center gap-1.5 ${
                    isActive
                      ? 'border-[#2d7ed0] text-[#172335]'
                      : 'border-transparent text-[#64788c] hover:text-[#172335]'
                  }`}
                >
                  {tab.icon && <span>{tab.icon}</span>}
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Email List Table Pane */}
      <div className="flex-1 overflow-y-auto divide-y divide-[#f0f5fa]">
        {/* Calendar Strip (when Calendar tab is active) */}
        {(activeTab === 'calendar' || filterCategory === 'calendar') && (
          <div className="p-4 bg-gradient-to-r from-[#FFFBEB] via-[#FEF3C7] to-[#FFFBEB] border-b border-[#FCD34D] flex flex-col gap-2.5 shadow-2xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-bold text-[#92400E]">
                <CalendarIcon className="w-4 h-4 text-[#D97706]" />
                <span>Upcoming Google Calendar Events ({calendarEvents.length})</span>
              </div>
              <span className="text-[10px] text-[#B45309] font-bold px-2 py-0.5 bg-white/80 rounded-md border border-[#FCD34D]">
                Synced with Workspace Calendar
              </span>
            </div>

            {calendarEvents.length === 0 ? (
              <p className="text-xs text-[#B45309]">No upcoming events scheduled for today.</p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-0.5">
                {calendarEvents.map((evt) => (
                  <div key={evt.id} className="p-2.5 bg-white border border-[#FCD34D]/60 rounded-xl flex flex-col gap-1 shadow-2xs">
                    <div className="flex items-center justify-between text-xs font-bold text-[#172335]">
                      <span className="truncate">{evt.title}</span>
                      <span className="px-2 py-0.5 rounded-md bg-[#FEF3C7] text-[#D97706] text-[10px] font-bold shrink-0 ml-2">
                        {new Date(evt.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    {evt.attendees && evt.attendees.length > 0 && (
                      <div className="flex items-center gap-1 text-[10px] text-[#536176]">
                        <Users className="w-3 h-3 text-[#8995A7] shrink-0" />
                        <span className="truncate">{evt.attendees.join(', ')}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        {loading ? (
          <div className="p-4 flex flex-col gap-3">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-14 rounded-xl skeleton-shimmer" />
            ))}
          </div>
        ) : threads.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-center p-6">
            <p className="text-xs text-[#536176] mb-3">No emails in this view.</p>
            <button
              onClick={loadThreads}
              className="px-3.5 h-8 bg-[#3186D8] hover:bg-[#2366A8] text-white text-xs font-semibold rounded-lg shadow-2xs transition-colors"
            >
              Refresh Mailbox
            </button>
          </div>
        ) : (
          threads.map((thread, index) => {
            const isUnread = !thread.is_read;

            return (
              <div
                key={thread.id}
                onClick={() => navigate(`/thread/${thread.id}`)}
                style={{ animationDelay: `${index * 40}ms` }}
                className={`h-[54px] px-6 flex items-center justify-between gap-4 cursor-pointer transition-colors animate-row-stagger ${
                  isUnread ? 'bg-[#f8fbfe] font-semibold hover:bg-[#edf5fc]' : 'bg-white hover:bg-[#f4f8fc]'
                }`}
              >
                {/* Left: Star + Avatar + Sender + Subject */}
                <div className="flex items-center gap-3.5 min-w-0 flex-1">
                  {/* Unread Indicator Dot / Star */}
                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      onClick={(e) => handleToggleStar(e, thread.id, thread.is_starred)}
                      className="shrink-0"
                    >
                      <Star
                        className={`w-3.5 h-3.5 ${
                          thread.is_starred ? 'fill-[#E5A93A] text-[#E5A93A]' : 'text-[#d7e3ee] hover:text-[#E5A93A]'
                        }`}
                      />
                    </button>

                    <div className={`w-7 h-7 rounded-full ${getAvatarColor(thread.sender)} text-white text-[11px] font-bold flex items-center justify-center shrink-0 shadow-2xs`}>
                      {thread.sender ? thread.sender.charAt(0).toUpperCase() : 'U'}
                    </div>
                  </div>

                  {/* Sender Name */}
                  <div className="w-36 shrink-0 truncate text-xs font-bold text-[#172335]">
                    {thread.sender || 'Unknown Sender'}
                  </div>

                  {/* Subject & Snippet Line (with Draft Badge if applicable) */}
                  <div className="min-w-0 flex-1 flex items-center gap-2 truncate text-xs">
                    {thread.isDraft && (
                      <span className="px-1.5 py-0.2 bg-[#e8f5e9] text-[#2e7d32] border border-[#a5d6a7] font-bold text-[10px] rounded flex items-center gap-0.5 shrink-0">
                        <Sparkles className="w-2.5 h-2.5" />
                        <span>Draft</span>
                      </span>
                    )}

                    <span className={`truncate ${isUnread ? 'font-bold text-[#172335]' : 'text-[#31516e]'}`}>
                      {thread.subject}
                    </span>

                    {thread.snippet && (
                      <span className="text-[#8fa0b1] truncate font-normal hidden md:inline">
                        — {thread.snippet}
                      </span>
                    )}

                    {thread.attachmentTag && (
                      <span className="px-2 py-0.5 bg-[#f0f4f8] text-[#d32f2f] text-[10px] font-bold rounded-md flex items-center gap-1 shrink-0">
                        <span>🔴</span>
                        <span>{thread.attachmentTag}</span>
                      </span>
                    )}
                  </div>
                </div>

                {/* Right: Timestamp */}
                <div className="text-[11px] text-[#8fa0b1] shrink-0 font-medium">
                  {formatTime(thread.last_message_at)}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Bottom Permission Notification Banner (Matching Screenshot 436) */}
      {showNotificationBanner && (
        <div className="h-10 bg-[#172335] text-white px-5 flex items-center justify-between text-xs shrink-0">
          <div className="flex items-center gap-2">
            <span>⚡ FlowInbox needs your permission to enable notifications.</span>
            <button 
              onClick={() => alert('Notifications Enabled!')} 
              className="font-bold underline hover:text-[#3186D8] transition-colors"
            >
              Enable notifications
            </button>
          </div>

          <button 
            onClick={() => setShowNotificationBanner(false)}
            className="p-1 hover:bg-white/10 rounded transition-colors"
          >
            <X className="w-3.5 h-3.5 text-white/70" />
          </button>
        </div>
      )}
    </div>
  );
}
