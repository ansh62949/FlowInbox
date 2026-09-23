import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  ChevronDown, 
  Sparkles, 
  Plus, 
  Mic, 
  ArrowUp,
  Square,
  RotateCcw,
  User,
  Bot,
  Mail,
  Zap,
  Star,
  Clock,
  Send,
  FileText,
  Calendar,
  Inbox as InboxIcon,
  AlertOctagon,
  Trash2,
  ExternalLink,
  PanelLeftClose,
  PanelLeft
} from 'lucide-react';
import agentsApi from '../../api/agents';
import { useAuth } from '../../context/AuthContext';
import FormattedMarkdown from '../ai/FormattedMarkdown';

export default function WorkspaceSidebar({ 
  sidebarMode = 'ai', 
  setSidebarMode, 
  isCollapsed = false,
  onToggleCollapse,
  width = 320,
  setWidth
}) {
  const { user, llmLabel } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [query, setQuery] = useState('');
  const [selectedModel, setSelectedModel] = useState(llmLabel || 'Groq Llama 3 70B');
  const [loading, setLoading] = useState(false);
  const [turns, setTurns] = useState([]);
  const [abortController, setAbortController] = useState(null);

  const turnsEndRef = useRef(null);

  useEffect(() => {
    turnsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [turns, loading]);

  const handleResizeStart = (event) => {
    event.preventDefault();
    const startX = event.clientX;
    const startWidth = width;
    const move = (moveEvent) => setWidth(Math.min(480, Math.max(240, startWidth + moveEvent.clientX - startX)));
    const stop = () => {
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerup', stop);
    };
    window.addEventListener('pointermove', move);
    window.addEventListener('pointerup', stop);
  };

  const handlePromptClick = (promptText) => {
    setQuery(promptText);
    handleSearchSubmit(promptText);
  };

  const handleCancelRequest = () => {
    if (abortController) {
      abortController.abort();
      setAbortController(null);
      setLoading(false);
    }
  };

  const handleClearThread = () => {
    if (loading) handleCancelRequest();
    setTurns([]);
  };

  const handleSearchSubmit = async (textToSubmit) => {
    const q = (textToSubmit || query).trim();
    if (!q || loading) return;

    const controller = new AbortController();
    setAbortController(controller);

    const userTurn = {
      id: Date.now().toString(),
      role: 'user',
      content: q,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setTurns(prev => [...prev, userTurn]);
    setQuery('');
    setLoading(true);

    try {
      const res = await agentsApi.submitTask(user?.id || 'default', q, { signal: controller.signal });
      const replyContent = res.final_response || res.intent || 'Task completed.';

      const assistantTurn = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: replyContent,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setTurns(prev => [...prev, assistantTurn]);
    } catch (err) {
      if (err.name === 'AbortError' || err.message === 'canceled') {
        const cancelledTurn = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: '_Request cancelled by user._',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        setTurns(prev => [...prev, cancelledTurn]);
      } else {
        const errorTurn = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `Unable to complete request: ${err.message || 'Server error'}.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        setTurns(prev => [...prev, errorTurn]);
      }
    } finally {
      setLoading(false);
      setAbortController(null);
    }
  };

  if (isCollapsed) {
    return (
      <div className="w-0 overflow-hidden transition-all duration-300 ease-in-out" />
    );
  }

  const workspaceName = user?.full_name ? `${user.full_name.split(' ')[0]}'s team` : 'My Workspace';
  const userInitials = user?.full_name ? user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) : 'US';

  return (
    <aside 
      style={{ width }} 
      className="relative shrink-0 bg-[#eaf3fb] border-r border-[#d7e3ee] flex flex-col justify-between p-3 select-none overflow-y-auto transition-[width] duration-200 ease-out"
    >
      {/* Right Edge Draggable Resize Handle */}
      <button 
        onPointerDown={handleResizeStart} 
        aria-label="Resize workspace sidebar" 
        className="absolute inset-y-0 right-0 z-10 w-1.5 cursor-ew-resize bg-transparent hover:bg-[#2d7ed0]/40 transition-colors" 
      />

      {sidebarMode === 'ai' ? (
        /* MODE A: Embedded AI Assistant Section */
        <div className="flex flex-col gap-3 h-full">
          {/* Top Header: Workspace Dropdown + Configure Agents Controls + Collapse */}
          <div className="flex items-center justify-between px-1 pt-1 shrink-0">
            <button 
              onClick={() => navigate('/settings/workspace')}
              className="flex items-center gap-1.5 px-2 py-1.5 rounded-xl bg-white/80 hover:bg-white text-xs font-bold text-[#172335] shadow-2xs border border-[#d7e3ee] transition-all truncate"
            >
              <span className="w-4 h-4 rounded-full bg-[#2d7ed0] text-white font-extrabold text-[10px] flex items-center justify-center shrink-0">
                {workspaceName.charAt(0)}
              </span>
              <span className="truncate">{workspaceName}</span>
              <ChevronDown className="w-3.5 h-3.5 text-[#6f8498] shrink-0" />
            </button>

            <div className="flex items-center gap-1 shrink-0">
              {turns.length > 0 && (
                <button
                  onClick={handleClearThread}
                  className="p-1.5 text-[#6f8498] hover:text-[#172335] hover:bg-white rounded-lg transition-colors"
                  title="Clear Conversation Thread"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                </button>
              )}

              <button 
                onClick={() => navigate('/settings/agents')}
                className="flex items-center gap-1 px-2 py-1 bg-white/70 hover:bg-white text-[11px] font-semibold text-[#536176] rounded-lg border border-[#d7e3ee] transition-colors"
                title="Configure Agents"
              >
                <Sparkles className="w-3 h-3 text-[#3186D8]" />
                <span className="hidden sm:inline">Configure</span>
              </button>

              <button 
                onClick={onToggleCollapse}
                className="p-1.5 text-[#6f8498] hover:text-[#172335] hover:bg-white rounded-lg transition-colors"
                title="Collapse Sidebar"
              >
                <PanelLeftClose className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Assistant View Body */}
          <div className="flex-1 flex flex-col justify-between overflow-y-auto px-1">
            
            {/* Conversation Turns Thread */}
            {turns.length > 0 ? (
              <div className="flex-1 overflow-y-auto space-y-3 pr-1 my-2">
                {turns.map((turn) => {
                  const isUser = turn.role === 'user';
                  return (
                    <div 
                      key={turn.id} 
                      className={`flex gap-2 animate-fade-in ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
                    >
                      <div className={`w-6 h-6 rounded-lg text-white font-bold text-[10px] flex items-center justify-center shrink-0 ${
                        isUser ? 'bg-[#172335]' : 'bg-[#3186D8]'
                      }`}>
                        {isUser ? userInitials : <Sparkles className="w-3 h-3" />}
                      </div>

                      <div className={`flex flex-col gap-1 max-w-[88%] ${isUser ? 'items-end' : 'items-start'}`}>
                        <div className="text-[9px] font-semibold text-[#64788c] px-1">
                          {isUser ? 'You' : 'FlowInbox AI'} · {turn.timestamp}
                        </div>

                        <div className={`p-3 rounded-xl text-xs leading-relaxed border shadow-2xs text-left ${
                          isUser 
                            ? 'bg-[#3186D8] text-white border-[#2874BE]' 
                            : 'bg-white text-[#172335] border-[#cce5fb]'
                        }`}>
                          {isUser ? (
                            <div className="whitespace-pre-wrap font-medium">{turn.content}</div>
                          ) : (
                            <FormattedMarkdown content={turn.content} />
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}

                {/* Loading / Thinking Turn */}
                {loading && (
                  <div className="flex gap-2 flex-row animate-fade-in items-start">
                    <div className="w-6 h-6 rounded-lg bg-[#3186D8] text-white flex items-center justify-center shrink-0">
                      <Sparkles className="w-3 h-3 animate-spin" />
                    </div>
                    <div className="p-3 bg-white border border-[#cce5fb] rounded-xl text-xs text-[#536176] flex items-center gap-2 shadow-2xs">
                      <span className="w-2 h-2 rounded-full bg-[#3186D8] animate-ping" />
                      <span>Thinking & searching vector context...</span>
                      <button
                        onClick={handleCancelRequest}
                        className="ml-2 p-1 rounded-md bg-[#FEF2F2] hover:bg-[#FEE2E2] text-[#991B1B] text-[10px] font-bold border border-[#FCA5A5] flex items-center gap-1 transition-colors"
                        title="Cancel Request"
                      >
                        <Square className="w-2.5 h-2.5 fill-current" />
                        <span>Stop</span>
                      </button>
                    </div>
                  </div>
                )}
                <div ref={turnsEndRef} />
              </div>
            ) : (
              /* Welcome Screen when no conversation turns exist */
              <div className="flex flex-col items-center text-center mt-2 px-1">
                <div className="w-10 h-10 rounded-2xl bg-[#3186D8] text-white flex items-center justify-center mb-3 shadow-md">
                  <Sparkles className="w-5 h-5 fill-white/20" />
                </div>

                <h2 className="text-sm font-bold text-[#172335]">How can I help?</h2>
                <p className="text-[11px] text-[#64788c] mt-0.5 mb-4 max-w-[240px] leading-tight">
                  Search, summarize, and navigate your inbox with AI.
                </p>
              </div>
            )}

            {/* Sticky Input Box & App Connections */}
            <div className="shrink-0 mt-auto pt-2">
              <div className="w-full bg-white border border-[#d7e3ee] rounded-2xl p-2.5 shadow-2xs text-left mb-2">
                <textarea
                  rows={2}
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSearchSubmit();
                    }
                  }}
                  placeholder="Ask anything, @mention contacts..."
                  className="w-full text-xs text-[#172335] placeholder-[#8fa0b1] focus:outline-none resize-none bg-transparent"
                />

                <div className="flex items-center justify-between pt-1 border-t border-[#f0f5fa] mt-1">
                  <div className="flex items-center gap-1.5">
                    <button className="p-1 text-[#8fa0b1] hover:text-[#172335] rounded-md transition-colors" title="Attach file">
                      <Plus className="w-3.5 h-3.5" />
                    </button>
                    <select
                      value={selectedModel}
                      onChange={(e) => setSelectedModel(e.target.value)}
                      className="text-[10px] font-semibold bg-[#f4f8fc] border border-[#d7e3ee] rounded-md px-1.5 py-0.5 text-[#536176] focus:outline-none"
                    >
                      <option value={llmLabel || 'Groq Llama 3 70B'}>{llmLabel || 'Groq Llama 3 70B'}</option>
                    </select>
                  </div>

                  <div className="flex items-center gap-1">
                    {loading ? (
                      <button
                        onClick={handleCancelRequest}
                        className="w-6 h-6 rounded-lg bg-[#DC2626] hover:bg-[#B91C1C] text-white flex items-center justify-center transition-colors shadow-2xs"
                        title="Stop Generation"
                      >
                        <Square className="w-3 h-3 fill-current" />
                      </button>
                    ) : (
                      <button
                        onClick={() => handleSearchSubmit()}
                        disabled={!query.trim()}
                        className="w-6 h-6 rounded-lg bg-[#3186D8] hover:bg-[#2366A8] disabled:opacity-40 text-white flex items-center justify-center transition-colors shadow-2xs"
                      >
                        <ArrowUp className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {turns.length === 0 && (
                <>
                  <div className="w-full flex items-center justify-between text-[11px] text-[#71869a] px-1 mb-2">
                    <span>Connected Apps</span>
                    <div className="flex items-center gap-1.5">
                      <span className="w-3.5 h-3.5 rounded bg-[#ea4335] text-white text-[8px] font-bold flex items-center justify-center" title="Gmail">M</span>
                      <span className="w-3.5 h-3.5 rounded bg-[#4285f4] text-white text-[8px] font-bold flex items-center justify-center" title="Google Calendar">C</span>
                      <span className="w-3.5 h-3.5 rounded bg-[#34a853] text-white text-[8px] font-bold flex items-center justify-center" title="Google Workspace">G</span>
                    </div>
                  </div>

                  <div className="flex flex-col gap-1.5 w-full">
                    {[
                      "Summarize my unread messages",
                      "Find emails with attachments from this week",
                      "What needs my attention today?"
                    ].map((promptText, idx) => (
                      <button
                        key={idx}
                        onClick={() => handlePromptClick(promptText)}
                        className="w-full py-2 px-3 bg-white hover:bg-[#f7fbff] border border-[#d7e3ee] hover:border-[#b9d2e8] rounded-xl text-xs font-semibold text-[#172335] text-center shadow-2xs transition-all"
                      >
                        {promptText}
                      </button>
                    ))}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      ) : (
        /* MODE B: Email Folders Section (Matching Screenshot 437) */
        <div className="flex flex-col justify-between h-full">
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between px-2 pt-1 pb-2">
              <button 
                onClick={() => navigate('/settings/workspace')}
                className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-white/80 hover:bg-white text-xs font-bold text-[#172335] shadow-2xs border border-[#d7e3ee]"
              >
                <span className="w-4 h-4 rounded-full bg-[#2d7ed0] text-white font-extrabold text-[10px] flex items-center justify-center">
                  {workspaceName.charAt(0)}
                </span>
                <span>{workspaceName}</span>
                <ChevronDown className="w-3.5 h-3.5 text-[#6f8498]" />
              </button>

              <button 
                onClick={onToggleCollapse}
                className="p-1.5 text-[#6f8498] hover:text-[#172335] hover:bg-white rounded-lg transition-colors"
                title="Collapse Sidebar"
              >
                <PanelLeftClose className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Folders List */}
            <nav className="flex flex-col gap-0.5">
              {[
                { id: 'all', label: 'Inbox', icon: InboxIcon, path: '/inbox' },
                { id: 'needs-reply', label: 'Needs Reply', icon: Zap, path: '/inbox/needs-reply' },
                { id: 'follow-ups', label: 'Follow Ups', icon: Sparkles, path: '/inbox/follow-ups' },
                { id: 'starred', label: 'Starred', icon: Star, path: '/inbox/starred' },
                { id: 'snoozed', label: 'Snoozed', icon: Clock, path: '/inbox/snoozed' },
                { id: 'sent', label: 'Sent', icon: Send, path: '/inbox/sent' },
                { id: 'drafts', label: 'Drafts', icon: FileText, path: '/inbox/drafts' },
                { id: 'scheduled', label: 'Scheduled', icon: Calendar, path: '/inbox/scheduled' },
                { id: 'all-mail', label: 'All Mail', icon: Mail, path: '/inbox/all' },
                { id: 'spam', label: 'Spam', icon: AlertOctagon, path: '/inbox/spam' },
                { id: 'trash', label: 'Trash', icon: Trash2, path: '/inbox/trash' },
              ].map((item) => {
                const Icon = item.icon;
                const active = location.pathname === item.path || (item.id === 'all' && location.pathname === '/inbox');
                return (
                  <button
                    key={item.id}
                    onClick={() => navigate(item.path)}
                    className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold transition-all ${
                      active
                        ? 'bg-white text-[#2d7ed0] shadow-2xs border border-[#d7e3ee]'
                        : 'text-[#536176] hover:bg-white/60 hover:text-[#172033]'
                    }`}
                  >
                    <Icon className={`w-3.5 h-3.5 ${active ? 'text-[#2d7ed0]' : 'text-[#8fa0b1]'}`} />
                    <span>{item.label}</span>
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Bottom Card: Claim your free month! (Matching Screenshot 437) */}
          <div className="mt-4 p-4 bg-white border border-[#d7e3ee] rounded-3xl shadow-2xs flex flex-col gap-3">
            <h4 className="text-xs font-bold text-[#172335]">Claim your free month!</h4>
            <div className="flex flex-col gap-1.5 text-[11px] text-[#536176]">
              <div className="flex items-center justify-between">
                <span>Get Browser Extension</span>
                <ExternalLink className="w-3 h-3 text-[#8fa0b1]" />
              </div>
              <div className="flex items-center justify-between">
                <span>Download mobile app</span>
                <ExternalLink className="w-3 h-3 text-[#8fa0b1]" />
              </div>
              <div className="flex items-center justify-between">
                <span>Install Desktop App</span>
                <ExternalLink className="w-3 h-3 text-[#8fa0b1]" />
              </div>
            </div>

            <button
              onClick={() => alert('Claiming free month!')}
              className="w-full h-8 bg-gradient-to-r from-[#9b51e0] to-[#2d7ed0] text-white text-xs font-bold rounded-xl shadow-2xs hover:opacity-90 transition-opacity"
            >
              Get 1 month free
            </button>
          </div>
        </div>
      )}
    </aside>
  );
}
