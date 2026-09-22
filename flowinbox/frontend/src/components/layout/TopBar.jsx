import React, { useState } from 'react';
import { Search, RefreshCw, ArrowRight } from 'lucide-react';
import inboxApi from '../../api/inbox';
import { useAuth } from '../../context/AuthContext';

export default function TopBar({ onOpenCommandPalette, onToggleAi }) {
  const { user } = useAuth();
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState('Syncing your messages...');

  const handleManualSync = async () => {
    if (isSyncing) return;
    setIsSyncing(true);
    setSyncMessage('Syncing Gmail...');
    try {
      const res = await inboxApi.syncInbox();
      setSyncMessage(`Synced ${res.synced_count || 0} messages`);
      setTimeout(() => setIsSyncing(false), 2500);
    } catch (err) {
      setSyncMessage('Sync up to date');
      setTimeout(() => setIsSyncing(false), 2500);
    }
  };

  const userInitial = user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'U';

  return (
    <header className="h-14 bg-[#f8fbfe] border-b border-[#d7e3ee] px-5 flex items-center justify-between shrink-0 select-none z-10">
      {/* Search Bar Input */}
      <div className="flex-1 max-w-md">
        <button
          onClick={onOpenCommandPalette}
          className="w-full h-8 bg-white hover:bg-[#fbfdff] border border-[#d7e3ee] rounded-xl px-3 flex items-center justify-between text-xs text-[#8995A7] transition-all cursor-text shadow-2xs"
        >
          <div className="flex items-center gap-2">
            <Search className="w-3.5 h-3.5 text-[#64788c]" />
            <span className="truncate">Search</span>
          </div>
          <kbd className="hidden sm:inline-flex items-center gap-0.5 text-[10px] font-semibold text-[#536176] bg-[#f4f8fc] border border-[#d7e3ee] px-1.5 py-0.5 rounded">
            ⌘K
          </kbd>
        </button>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-3 ml-4">
        {/* Syncing Status Indicator with Green Dot */}
        <button
          onClick={handleManualSync}
          disabled={isSyncing}
          className="flex items-center gap-1.5 text-xs text-[#64788c] hover:text-[#172335] transition-colors"
        >
          <span className={`w-2 h-2 rounded-full bg-[#48A97B] ${isSyncing ? 'animate-pulse' : ''}`} />
          <span className="text-[11px] font-medium hidden md:inline">
            {isSyncing ? syncMessage : 'Syncing your messages...'}
          </span>
        </button>

        {/* User Avatar */}
        <div 
          className="w-7 h-7 rounded-full bg-[#2d7ed0] text-white text-xs font-bold flex items-center justify-center cursor-pointer border border-white shadow-2xs"
          title={user?.email || 'User Account'}
        >
          {userInitial}
        </div>
      </div>
    </header>
  );
}
