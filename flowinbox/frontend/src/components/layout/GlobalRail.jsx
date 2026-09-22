import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  Sparkles, 
  Mail, 
  Bot,
  Hash, 
  Settings, 
  HelpCircle,
  PanelLeft
} from 'lucide-react';

export default function GlobalRail({ 
  sidebarMode, 
  setSidebarMode, 
  isSidebarCollapsed, 
  onToggleSidebar, 
  onToggleAi, 
  isAiOpen 
}) {
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = (path) => {
    if (path === '/inbox') return location.pathname.startsWith('/inbox') || location.pathname.startsWith('/thread');
    if (path === '/agents') return location.pathname.startsWith('/agents');
    if (path === '/channels') return location.pathname.startsWith('/channels');
    if (path === '/settings') return location.pathname.startsWith('/settings');
    return false;
  };

  const handleModeClick = (mode) => {
    setSidebarMode(mode);
    if (isSidebarCollapsed) {
      onToggleSidebar();
    }
    if (location.pathname !== '/inbox') {
      navigate('/inbox');
    }
  };

  return (
    <aside className="w-12 bg-[#f5f9fd] border-r border-[#d7e3ee] flex flex-col items-center justify-between py-3 shrink-0 select-none z-20">
      {/* Top: Logo + Core Nav */}
      <div className="flex flex-col items-center gap-3 w-full">
        {/* Logo Mark */}
        <button 
          onClick={() => handleModeClick('ai')}
          title="FlowInbox Home"
          className="w-8 h-8 rounded-xl bg-[#172335] text-white flex items-center justify-center font-extrabold text-sm shadow-2xs hover:bg-[#2d7ed0] transition-colors"
        >
          A
        </button>

        {/* Sidebar Expand/Collapse Toggle Icon */}
        <button
          onClick={onToggleSidebar}
          title={isSidebarCollapsed ? "Expand Workspace Sidebar" : "Collapse Workspace Sidebar"}
          className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors ${
            isSidebarCollapsed ? 'bg-[#3186D8] text-white shadow-2xs' : 'text-[#5e7186] hover:bg-[#e4eff9] hover:text-[#172335]'
          }`}
        >
          <PanelLeft className="w-4 h-4" />
        </button>

        <div className="w-6 h-[1px] bg-[#d7e3ee] my-0.5" />

        {/* AI Assistant Mode Icon */}
        <button
          onClick={() => handleModeClick('ai')}
          title="FlowInbox AI Assistant Panel"
          className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors relative ${
            sidebarMode === 'ai' && !isSidebarCollapsed
              ? 'bg-[#dcebf8] text-[#1d5f9f] shadow-2xs font-bold' 
              : 'text-[#5e7186] hover:bg-[#e4eff9] hover:text-[#172335]'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-[#3186D8] ring-1 ring-white" />
        </button>

        {/* 1. Mail Folders Mode Icon */}
        <button
          onClick={() => handleModeClick('mail')}
          title="Mail Folders Panel"
          className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors ${
            sidebarMode === 'mail' && !isSidebarCollapsed
              ? 'bg-white text-[#2d7ed0] font-bold shadow-2xs border border-[#d7e3ee]'
              : 'text-[#5e7186] hover:bg-[#e4eff9] hover:text-[#172335]'
          }`}
        >
          <Mail className="w-4 h-4" />
        </button>

        {/* 2. Agents */}
        <button
          onClick={() => navigate('/agents')}
          title="Agents"
          className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors ${
            isActive('/agents')
              ? 'bg-white text-[#2d7ed0] font-bold shadow-2xs border border-[#d7e3ee]'
              : 'text-[#5e7186] hover:bg-[#e4eff9] hover:text-[#172335]'
          }`}
        >
          <Bot className="w-4 h-4" />
        </button>

        {/* 3. Channels */}
        <button
          onClick={() => navigate('/channels')}
          title="Channels"
          className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors ${
            isActive('/channels')
              ? 'bg-white text-[#3186D8] font-bold shadow-2xs border border-[#DCE5EF]'
              : 'text-[#536176] hover:bg-[#EDF4FB] hover:text-[#172033]'
          }`}
        >
          <Hash className="w-4 h-4" />
        </button>

      </div>

      {/* Bottom Nav */}
      <div className="flex flex-col items-center gap-3 w-full">
        <button
          onClick={() => navigate('/settings')}
          title="Settings"
          className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors ${
            isActive('/settings')
              ? 'bg-white text-[#3186D8] font-bold shadow-2xs border border-[#DCE5EF]'
              : 'text-[#536176] hover:bg-[#EDF4FB] hover:text-[#172033]'
          }`}
        >
          <Settings className="w-4 h-4" />
        </button>

        <button
          onClick={() => alert('FlowInbox Documentation & Support')}
          title="Help"
          className="w-8 h-8 rounded-lg flex items-center justify-center text-[#536176] hover:bg-[#EDF4FB] hover:text-[#172033] transition-colors"
        >
          <HelpCircle className="w-4 h-4" />
        </button>

        <div className="w-7 h-7 rounded-full bg-[#3186D8] text-white font-bold text-xs flex items-center justify-center cursor-pointer border border-white shadow-2xs">
          AP
        </div>
      </div>
    </aside>
  );
}
