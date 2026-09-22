import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Mail, Hash, Sparkles, ShieldCheck, Activity, Settings, ArrowRight } from 'lucide-react';
import inboxApi from '../../api/inbox';

export default function CommandPalette({ isOpen, onClose, onOpenAi }) {
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const inputRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
    } else {
      setQuery('');
      setSearchResults([]);
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
      }
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  useEffect(() => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const threads = await inboxApi.getThreads({ q: query });
        setSearchResults(threads || []);
      } catch (err) {
        setSearchResults([]);
      } finally {
        setLoading(false);
      }
    }, 200);

    return () => clearTimeout(timer);
  }, [query]);

  if (!isOpen) return null;

  const quickNav = [
    { label: 'Go to Inbox', icon: Mail, path: '/inbox' },
    { label: 'Go to Needs Reply', icon: Mail, path: '/inbox/needs-reply' },
    { label: 'Go to Channels', icon: Hash, path: '/channels' },
    { label: 'Ask FlowInbox AI', icon: Sparkles, action: () => { onClose(); onOpenAi(); } },
    { label: 'Open Approvals', icon: ShieldCheck, path: '/approvals' },
    { label: 'Open Agent Activity', icon: Activity, path: '/agent-activity' },
    { label: 'Open Settings', icon: Settings, path: '/settings' },
  ];

  const handleSelectNav = (item) => {
    onClose();
    if (item.action) item.action();
    else if (item.path) navigate(item.path);
  };

  return (
    <div className="fixed inset-0 bg-black/20 backdrop-blur-xs flex items-start justify-center pt-20 z-50 animate-fade-in" onClick={onClose}>
      <div 
        className="bg-white rounded-2xl shadow-xl border border-[#DCE5EF] w-full max-w-xl overflow-hidden animate-scale-in"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-3 border-b border-[#DCE5EF] flex items-center gap-3">
          <Search className="w-4 h-4 text-[#536176] shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command or search emails..."
            className="w-full text-xs text-[#172033] bg-transparent focus:outline-none placeholder-[#8995A7]"
          />
          <kbd className="text-[10px] font-semibold text-[#8995A7] bg-[#F4F8FC] border border-[#DCE5EF] px-1.5 py-0.5 rounded">
            ESC
          </kbd>
        </div>

        <div className="max-h-80 overflow-y-auto p-2">
          {query.trim() !== '' ? (
            <div>
              <div className="px-3 py-1.5 text-[10px] font-bold text-[#8995A7] uppercase tracking-wider">
                Matching Email Threads {loading && '(Searching...)'}
              </div>

              {searchResults.length === 0 && !loading ? (
                <div className="p-4 text-center text-xs text-[#536176]">
                  No email threads found matching "{query}"
                </div>
              ) : (
                searchResults.map((t) => (
                  <button
                    key={t.id}
                    onClick={() => { onClose(); navigate(`/thread/${t.id}`); }}
                    className="w-full px-3 py-2 text-left rounded-xl hover:bg-[#EDF4FB] flex items-center justify-between group transition-colors"
                  >
                    <div className="truncate">
                      <div className="text-xs font-semibold text-[#172033] truncate">{t.subject}</div>
                      <div className="text-[11px] text-[#536176] truncate">{t.sender} &bull; {t.snippet}</div>
                    </div>
                    <ArrowRight className="w-3.5 h-3.5 text-[#8995A7] group-hover:text-[#3186D8] shrink-0 ml-2" />
                  </button>
                ))
              )}
            </div>
          ) : (
            <div>
              <div className="px-3 py-1.5 text-[10px] font-bold text-[#8995A7] uppercase tracking-wider">
                Quick Navigation & Commands
              </div>
              {quickNav.map((item, idx) => {
                const Icon = item.icon;
                return (
                  <button
                    key={idx}
                    onClick={() => handleSelectNav(item)}
                    className="w-full px-3 py-2 rounded-xl hover:bg-[#EDF4FB] flex items-center justify-between text-xs text-[#172033] transition-colors"
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon className="w-4 h-4 text-[#536176]" />
                      <span>{item.label}</span>
                    </div>
                    <ArrowRight className="w-3.5 h-3.5 text-[#8995A7]" />
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
