import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Hash, Plus, Filter, Users, Bot, ArrowRight, X, Sparkles, SlidersHorizontal, Tag, CheckCircle2 } from 'lucide-react';
import channelsApi from '../api/channels';
import inboxApi from '../api/inbox';

export default function ChannelsPage() {
  const { channelId } = useParams();
  const navigate = useNavigate();

  const [channels, setChannels] = useState([]);
  const [activeChannel, setActiveChannel] = useState(null);
  const [filters, setFilters] = useState([]);
  const [matchingThreads, setMatchingThreads] = useState([]);
  const [loading, setLoading] = useState(true);

  // Create Channel Modal State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newChannelName, setNewChannelName] = useState('');
  const [filterRule, setFilterRule] = useState('');
  const [creating, setCreating] = useState(false);

  // Preset filter suggestions for quick creation
  const presetRules = [
    { label: 'Feedback', rule: 'feedback' },
    { label: 'Receipts / Invoices', rule: 'receipt' },
    { label: 'Engineering / Bugs', rule: 'bug' },
    { label: 'Urgent', rule: 'urgent' }
  ];

  useEffect(() => {
    loadChannels();
  }, []);

  useEffect(() => {
    if (channels.length > 0) {
      if (channelId) {
        const found = channels.find((c) => c.id === channelId);
        if (found) setActiveChannel(found);
        else setActiveChannel(channels[0]);
      } else {
        setActiveChannel(channels[0]);
      }
    }
  }, [channelId, channels]);

  useEffect(() => {
    if (activeChannel) {
      loadChannelDetails(activeChannel.id);
    }
  }, [activeChannel]);

  const loadChannels = async () => {
    setLoading(true);
    try {
      const data = await channelsApi.getChannels();
      const list = data && data.length ? data : [
        { id: 'ch-1', name: 'general', rules: [] },
        { id: 'ch-2', name: 'customer-feedback', rules: [{ field: 'subject_contains', value: 'feedback' }] },
        { id: 'ch-3', name: 'receipts', rules: [{ field: 'subject_contains', value: 'receipt' }] },
        { id: 'ch-4', name: 'engineering', rules: [{ field: 'subject_contains', value: 'bug' }] }
      ];
      setChannels(list);
    } catch (err) {
      setChannels([
        { id: 'ch-1', name: 'general', rules: [] },
        { id: 'ch-2', name: 'customer-feedback', rules: [{ field: 'subject_contains', value: 'feedback' }] },
        { id: 'ch-3', name: 'receipts', rules: [{ field: 'subject_contains', value: 'receipt' }] },
        { id: 'ch-4', name: 'engineering', rules: [{ field: 'subject_contains', value: 'bug' }] }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const loadChannelDetails = async (cId) => {
    try {
      const fList = await channelsApi.getChannelFilters(cId).catch(() => []);
      setFilters(fList);

      const allThreads = await inboxApi.getThreads({ folder: 'all' }).catch(() => []);
      const matched = allThreads.filter((t) => {
        if (!fList || fList.length === 0) return true;
        return fList.some((rule) => {
          const val = (rule.value || '').toLowerCase();
          if (!val) return true;
          if (rule.field === 'subject_contains') return (t.subject || '').toLowerCase().includes(val);
          if (rule.field === 'from') return (t.sender || '').toLowerCase().includes(val);
          return true;
        });
      });
      setMatchingThreads(matched);
    } catch (err) {
      console.error('Channel detail error:', err);
    }
  };

  const handleCreateChannelSubmit = async (e) => {
    e.preventDefault();
    const cleanName = newChannelName.trim().toLowerCase().replace(/\s+/g, '-');
    if (!cleanName) return;

    setCreating(true);
    try {
      const rules = filterRule.trim() ? [{ field: 'subject_contains', value: filterRule.trim() }] : [];
      const created = await channelsApi.createChannel(cleanName, 'hash', rules).catch(() => null);

      const newChanObj = created || {
        id: `ch-${Date.now()}`,
        name: cleanName,
        rules: rules
      };

      setChannels((prev) => [...prev, newChanObj]);
      setActiveChannel(newChanObj);
      navigate(`/channels/${newChanObj.id}`);
      setShowCreateModal(false);
      setNewChannelName('');
      setFilterRule('');
    } catch (err) {
      alert('Error creating channel: ' + err.message);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="flex h-full bg-[#f4efe6] select-none p-2 gap-2 overflow-hidden">
      {/* Channels Sidebar List */}
      <div className="w-60 bg-[#FAF6F0] rounded-2xl border border-[#E6DFD5] p-3 flex flex-col gap-3 shrink-0 shadow-2xs">
        <div className="flex items-center justify-between px-2 pt-1">
          <div className="flex items-center gap-1.5">
            <Hash className="w-4 h-4 text-[#2d7ed0]" />
            <span className="text-[11px] font-bold text-[#5e7186] uppercase tracking-wider">
              Workspace Channels
            </span>
          </div>

          <button
            onClick={() => setShowCreateModal(true)}
            className="p-1.5 rounded-lg bg-white hover:bg-[#e5f0fb] text-[#2d7ed0] border border-[#c9dff4] hover:border-[#2d7ed0] shadow-2xs transition-all flex items-center gap-1 text-[11px] font-semibold smooth-interactive"
            title="Create New Channel"
          >
            <Plus className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="flex flex-col gap-1.5 overflow-y-auto pr-0.5">
          {channels.map((ch) => {
            const isSelected = activeChannel?.id === ch.id;
            return (
              <button
                key={ch.id}
                onClick={() => {
                  setActiveChannel(ch);
                  navigate(`/channels/${ch.id}`);
                }}
                className={`w-full px-3 py-2.5 rounded-xl flex items-center justify-between text-xs transition-all ${
                  isSelected
                    ? 'bg-white text-[#2d7ed0] font-bold shadow-2xs border border-[#c9dff4] transform scale-[1.01]'
                    : 'text-[#172335] hover:bg-[#EFE8DC] hover:text-[#1d5f9f]'
                }`}
              >
                <div className="flex items-center gap-2 truncate">
                  <Hash className={`w-3.5 h-3.5 ${isSelected ? 'text-[#2d7ed0]' : 'text-[#8fa0b1]'}`} />
                  <span className="truncate font-medium">#{ch.name}</span>
                </div>
                {ch.rules && ch.rules.length > 0 && (
                  <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-semibold ${
                    isSelected ? 'bg-[#e5f0fb] text-[#1d5f9f]' : 'bg-[#EFE8DC] text-[#5e7186]'
                  }`}>
                    {ch.rules.length} rule
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Quick info footer */}
        <div className="mt-auto pt-3 border-t border-[#E6DFD5] px-2 flex items-center justify-between text-[11px] text-[#5e7186]">
          <span>{channels.length} Channels Total</span>
          <span className="flex items-center gap-1 text-[#2d7ed0] font-medium cursor-pointer hover:underline" onClick={() => setShowCreateModal(true)}>
            + Add New
          </span>
        </div>
      </div>

      {/* Main Channel View */}
      <div className="flex-1 flex flex-col min-w-0 bg-white rounded-2xl border border-[#E6DFD5] shadow-2xs overflow-hidden">
        {activeChannel ? (
          <div key={activeChannel.id} className="flex-1 flex flex-col min-w-0 animate-fade-in">
            {/* Header Bar */}
            <div className="px-6 py-3.5 border-b border-[#E6DFD5] flex items-center justify-between bg-white shrink-0">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-[#e5f0fb] text-[#2d7ed0] flex items-center justify-center font-bold shadow-2xs">
                  <Hash className="w-4 h-4" />
                </div>
                <div>
                  <h1 className="text-sm font-bold text-[#172335]">#{activeChannel.name}</h1>
                  <p className="text-[11px] text-[#5e7186]">Automatic routing & category workspace channel</p>
                </div>
              </div>

              <div className="flex items-center gap-2 text-xs text-[#5e7186]">
                <div className="flex items-center gap-1.5 bg-[#FAF6F0] border border-[#E6DFD5] px-3 py-1.5 rounded-xl font-medium">
                  <Users className="w-3.5 h-3.5 text-[#2d7ed0]" />
                  <span>3 Members</span>
                </div>
                <div className="flex items-center gap-1.5 bg-[#FAF6F0] border border-[#E6DFD5] px-3 py-1.5 rounded-xl font-medium">
                  <Bot className="w-3.5 h-3.5 text-[#8C6BD9]" />
                  <span>2 Agents Assigned</span>
                </div>
              </div>
            </div>

            {/* Filter Rules Bar */}
            <div className="px-6 py-2.5 bg-[#FAF6F0] border-b border-[#E6DFD5] flex items-center justify-between text-xs text-[#5e7186]">
              <div className="flex items-center gap-2">
                <Filter className="w-3.5 h-3.5 text-[#2d7ed0]" />
                <span className="font-semibold text-[#172335]">Active Channel Filters:</span>
                {filters && filters.length > 0 ? (
                  filters.map((f, i) => (
                    <span key={i} className="px-2.5 py-1 bg-[#e5f0fb] border border-[#c9dff4] text-[#1d5f9f] rounded-lg text-[11px] font-semibold flex items-center gap-1">
                      <Tag className="w-3 h-3" />
                      {f.field}: "{f.value}"
                    </span>
                  ))
                ) : (
                  <span className="text-[11px] text-[#8fa0b1] italic">No filter rules applied — displaying all workspace threads.</span>
                )}
              </div>

              <button
                onClick={() => setShowCreateModal(true)}
                className="text-[11px] text-[#2d7ed0] hover:text-[#1d5f9f] font-semibold flex items-center gap-1 transition-colors"
              >
                <SlidersHorizontal className="w-3 h-3" />
                <span>Configure Rules</span>
              </button>
            </div>

            {/* Threads List */}
            <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-3 bg-[#FAF6F0]/40">
              {matchingThreads.length === 0 ? (
                <div className="p-12 text-center text-xs text-[#5e7186] bg-white rounded-2xl border border-[#E6DFD5] shadow-2xs max-w-md mx-auto my-auto flex flex-col items-center gap-2">
                  <div className="w-10 h-10 rounded-2xl bg-[#e5f0fb] text-[#2d7ed0] flex items-center justify-center">
                    <Sparkles className="w-5 h-5" />
                  </div>
                  <h3 className="font-bold text-[#172335] text-sm mt-1">No Matched Threads Yet</h3>
                  <p className="text-[11px] text-[#5e7186] max-w-xs">
                    Threads containing matching subject keywords will automatically route into #{activeChannel.name}.
                  </p>
                </div>
              ) : (
                matchingThreads.map((t, index) => (
                  <div
                    key={t.id}
                    onClick={() => navigate(`/thread/${t.id}`)}
                    style={{ animationDelay: `${index * 40}ms` }}
                    className="p-4 bg-white border border-[#E6DFD5] hover:border-[#2d7ed0] rounded-2xl shadow-2xs hover:shadow-md transition-all cursor-pointer flex items-center justify-between group smooth-interactive animate-row-stagger"
                  >
                    <div className="min-w-0 flex-1 pr-4">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="w-2 h-2 rounded-full bg-[#2d7ed0]" />
                        <span className="text-xs font-bold text-[#172335]">{t.sender}</span>
                        {t.category && (
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#FAF6F0] text-[#5e7186] font-medium border border-[#E6DFD5]">
                            {t.category}
                          </span>
                        )}
                      </div>
                      <div className="text-xs font-bold text-[#172335] truncate mb-0.5 group-hover:text-[#2d7ed0] transition-colors">
                        {t.subject}
                      </div>
                      <p className="text-xs text-[#5e7186] truncate">{t.snippet}</p>
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      <span className="text-[11px] text-[#8fa0b1] font-medium">
                        {t.last_message_at ? new Date(t.last_message_at).toLocaleDateString() : 'Today'}
                      </span>
                      <div className="w-7 h-7 rounded-lg bg-[#FAF6F0] group-hover:bg-[#e5f0fb] group-hover:text-[#2d7ed0] text-[#5e7186] flex items-center justify-center transition-colors">
                        <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        ) : (
          <div className="p-8 text-center text-xs text-[#5e7186] my-auto">Select a channel to view content.</div>
        )}
      </div>

      {/* Create Channel Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-[#172335]/30 backdrop-blur-xs flex items-center justify-center z-50 animate-fade-in">
          <div className="bg-white rounded-2xl shadow-2xl border border-[#E6DFD5] p-6 w-[420px] animate-scale-in">
            <div className="flex items-center justify-between pb-3 border-b border-[#FAF6F0] mb-4">
              <div className="flex items-center gap-2.5">
                <div className="w-7 h-7 rounded-xl bg-[#e5f0fb] text-[#2d7ed0] flex items-center justify-center font-bold">
                  <Hash className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-xs font-bold text-[#172335]">Create Workspace Channel</h3>
                  <p className="text-[10px] text-[#5e7186]">Add a new category channel with routing rules</p>
                </div>
              </div>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-1 text-[#5e7186] hover:text-[#172335] hover:bg-[#FAF6F0] rounded-md transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateChannelSubmit} className="flex flex-col gap-4">
              <div>
                <label className="block text-[11px] font-semibold text-[#5e7186] mb-1">Channel Name</label>
                <div className="relative flex items-center">
                  <span className="absolute left-3 text-xs font-bold text-[#2d7ed0]">#</span>
                  <input
                    type="text"
                    value={newChannelName}
                    onChange={(e) => setNewChannelName(e.target.value)}
                    placeholder="e.g. product-updates"
                    className="w-full h-9 pl-7 pr-3 bg-[#FAF6F0] border border-[#E6DFD5] rounded-xl text-xs text-[#172335] font-medium focus:outline-none focus:border-[#2d7ed0] focus:ring-2 focus:ring-[#2d7ed0]/20 transition-all"
                    required
                    autoFocus
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-[#5e7186] mb-1">
                  Subject Keyword Routing Rule <span className="text-[#8fa0b1] font-normal">(Optional)</span>
                </label>
                <input
                  type="text"
                  value={filterRule}
                  onChange={(e) => setFilterRule(e.target.value)}
                  placeholder="e.g. 'feedback', 'invoice', or 'urgent'"
                  className="w-full h-9 px-3 bg-[#FAF6F0] border border-[#E6DFD5] rounded-xl text-xs text-[#172335] font-medium focus:outline-none focus:border-[#2d7ed0] focus:ring-2 focus:ring-[#2d7ed0]/20 transition-all"
                />
              </div>

              {/* Preset rule suggestions */}
              <div>
                <span className="block text-[10px] font-semibold text-[#8fa0b1] mb-1.5 uppercase tracking-wider">Quick Presets</span>
                <div className="flex flex-wrap gap-1.5">
                  {presetRules.map((item, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => setFilterRule(item.rule)}
                      className={`px-2.5 py-1 rounded-lg text-[11px] font-medium border transition-all ${
                        filterRule === item.rule
                          ? 'bg-[#e5f0fb] text-[#1d5f9f] border-[#2d7ed0]'
                          : 'bg-[#FAF6F0] text-[#5e7186] border-[#E6DFD5] hover:bg-[#EFE8DC]'
                      }`}
                    >
                      + {item.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-[#FAF6F0]">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-3.5 h-8.5 text-xs font-medium text-[#5e7186] hover:bg-[#FAF6F0] rounded-xl transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating || !newChannelName.trim()}
                  className="px-4 h-8.5 text-xs font-bold bg-[#2d7ed0] hover:bg-[#1d5f9f] disabled:opacity-40 text-white rounded-xl shadow-2xs transition-all smooth-interactive flex items-center gap-1.5"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>{creating ? 'Creating...' : 'Create Channel'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}


