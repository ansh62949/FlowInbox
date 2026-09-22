import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import GlobalRail from './GlobalRail';
import WorkspaceSidebar from './WorkspaceSidebar';
import TopBar from './TopBar';
import AIDrawer from '../ai/AIDrawer';
import CommandPalette from './CommandPalette';
import { X, Send } from 'lucide-react';

export default function AppShell({ children }) {
  const location = useLocation();
  const [sidebarMode, setSidebarMode] = useState('ai'); // 'ai' or 'mail'
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [sidebarWidth, setSidebarWidth] = useState(() => Number(localStorage.getItem('flowinbox.sidebarWidth')) || 320);
  const [isAiOpen, setIsAiOpen] = useState(false);
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const [isComposeOpen, setIsComposeOpen] = useState(false);

  const [composeTo, setComposeTo] = useState('');
  const [composeSubject, setComposeSubject] = useState('');
  const [composeBody, setComposeBody] = useState('');
  const [sending, setSending] = useState(false);

  useEffect(() => {
    localStorage.setItem('flowinbox.sidebarWidth', String(sidebarWidth));
  }, [sidebarWidth]);

  const handleSendCompose = async (e) => {
    e.preventDefault();
    if (!composeTo.trim() || !composeSubject.trim()) return;
    setSending(true);
    try {
      alert('Draft email created for ' + composeTo);
      setIsComposeOpen(false);
      setComposeTo('');
      setComposeSubject('');
      setComposeBody('');
    } catch (err) {
      alert('Error composing message: ' + err.message);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="flex h-screen w-screen bg-[#FAF6F0] overflow-hidden select-none">
      {/* 1. Global Rail (44px) */}
      <GlobalRail 
        sidebarMode={sidebarMode}
        setSidebarMode={setSidebarMode}
        isSidebarCollapsed={isSidebarCollapsed}
        onToggleSidebar={() => setIsSidebarCollapsed((prev) => !prev)}
        onToggleAi={() => setIsAiOpen((prev) => !prev)} 
        isAiOpen={isAiOpen} 
      />

      {/* 2. Workspace Sidebar (Collapsible & Resizable/Extendable) */}
      {!isSidebarCollapsed && (
        <WorkspaceSidebar 
          sidebarMode={sidebarMode}
          setSidebarMode={setSidebarMode}
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={() => setIsSidebarCollapsed((prev) => !prev)}
          width={sidebarWidth}
          setWidth={setSidebarWidth}
          onNewCompose={() => setIsComposeOpen(true)} 
        />
      )}

      {/* 3. Main Workspace Area */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden bg-[#FAF6F0]">
        <TopBar 
          onOpenCommandPalette={() => setIsCommandPaletteOpen(true)}
          onToggleAi={() => setIsAiOpen((prev) => !prev)}
        />

        <main className="flex-1 min-h-0 overflow-y-auto bg-[#FAF6F0]">
          {children}
        </main>
      </div>

      {/* 4. Slide-out AI Drawer */}
      <AIDrawer 
        isOpen={isAiOpen} 
        onClose={() => setIsAiOpen(false)} 
      />

      {/* 5. Command Palette (⌘K) */}
      <CommandPalette 
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
        onOpenAi={() => setIsAiOpen(true)}
      />

      {/* 6. Compose Modal */}
      {isComposeOpen && (
        <div className="fixed bottom-4 right-4 w-full max-w-lg bg-white rounded-2xl shadow-2xl border border-[#E6DFD5] z-50 animate-scale-in overflow-hidden">
          <div className="px-4 py-3 bg-[#FAF6F0] border-b border-[#E6DFD5] flex items-center justify-between">
            <h3 className="text-xs font-bold text-[#172033]">New Message</h3>
            <button 
              onClick={() => setIsComposeOpen(false)}
              className="p-1 text-[#536176] hover:text-[#172033] hover:bg-[#F0E8DC] rounded-md transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <form onSubmit={handleSendCompose} className="p-4 flex flex-col gap-3">
            <div>
              <label className="block text-[11px] font-semibold text-[#536176] mb-1">To</label>
              <input
                type="email"
                value={composeTo}
                onChange={(e) => setComposeTo(e.target.value)}
                placeholder="recipient@example.com"
                className="w-full h-8 px-3 bg-[#FAF6F0] border border-[#E6DFD5] rounded-xl text-xs focus:outline-none focus:border-[#3186D8]"
                required
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-[#536176] mb-1">Subject</label>
              <input
                type="text"
                value={composeSubject}
                onChange={(e) => setComposeSubject(e.target.value)}
                placeholder="Subject"
                className="w-full h-8 px-3 bg-[#FAF6F0] border border-[#E6DFD5] rounded-xl text-xs focus:outline-none focus:border-[#3186D8]"
                required
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-[#536176] mb-1">Message</label>
              <textarea
                rows={6}
                value={composeBody}
                onChange={(e) => setComposeBody(e.target.value)}
                placeholder="Write your email body..."
                className="w-full p-3 bg-[#FAF6F0] border border-[#E6DFD5] rounded-xl text-xs focus:outline-none focus:border-[#3186D8] resize-none"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setIsComposeOpen(false)}
                className="px-3 h-8 text-xs font-medium text-[#536176] hover:bg-[#FAF6F0] rounded-lg transition-colors"
              >
                Discard
              </button>
              <button
                type="submit"
                disabled={sending}
                className="px-4 h-8 bg-[#3186D8] hover:bg-[#2366A8] text-white text-xs font-semibold rounded-xl flex items-center gap-1.5 shadow-2xs transition-colors"
              >
                <Send className="w-3.5 h-3.5" />
                <span>{sending ? 'Sending...' : 'Send Email'}</span>
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
