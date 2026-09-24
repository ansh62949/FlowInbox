import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  Users, 
  Palette, 
  FileSignature, 
  Filter, 
  Bell, 
  Code2, 
  Layers, 
  Building2, 
  Sliders, 
  PenTool, 
  Sparkles, 
  Play, 
  Upload, 
  Check, 
  ArrowLeft,
  X,
  Plus,
  RotateCw,
  HelpCircle,
  Briefcase,
  User,
  Rocket,
  Search,
  CheckCircle2,
  ShieldCheck,
  Zap,
  Inbox as InboxIcon,
  Bot
} from 'lucide-react';
import authApi from '../api/auth';
import followupsApi from '../api/followups';
import integrationsApi from '../api/integrations';
import apiTokensApi from '../api/apiTokens';
import { API_BASE } from '../api/client';

import TeamPage from './TeamPage';
import { useAuth } from '../context/AuthContext';


export default function SettingsPage() {
  const { user, theme, setTheme } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const currentTab = location.pathname.split('/settings/')[1] || 'signatures';
  const [searchQuery, setSearchQuery] = useState('');

  // Signatures State
  const [enableGmailSignature, setEnableGmailSignature] = useState(false);
  const [enableFlowInboxSignature, setEnableFlowInboxSignature] = useState(true);

  // Writing Profile State
  const [bio, setBio] = useState('Product builder focusing on intelligent productivity tools.');
  const [schedulingLink, setSchedulingLink] = useState('https://cal.com/user/meeting');
  const [signOff, setSignOff] = useState(`Best regards,\n${user?.full_name || 'User'}`);
  const [writingPrompt, setWritingPrompt] = useState(
    `Write in a courteous, concise, professional tone.

- Greeting: use "Hi [First name]," for an individual; use "Dear [Team name] Team," for a group.
- Opening: state the purpose in the first 1-2 sentences.
- Keep replies and confirmations to 2-3 concise paragraphs.`
  );

  // Workspace Settings State
  const [workspaceName, setWorkspaceName] = useState(user?.full_name ? `${user.full_name}'s team` : 'My Workspace');
  const [workspaceSlug, setWorkspaceSlug] = useState('my-team');
  const [saveSuccess, setSaveSuccess] = useState('');

  // Preference Settings State
  const [autoAdvance, setAutoAdvance] = useState(true);
  const [soundNotifications, setSoundNotifications] = useState(false);
  const [defaultView, setDefaultView] = useState('inbox');

  // Integrations State
  const [integrations, setIntegrations] = useState([]);
  const [showAddIntegrationModal, setShowAddIntegrationModal] = useState(false);
  const [newIntegrationType, setNewIntegrationType] = useState('slack');
  const [newIntegrationKey, setNewIntegrationKey] = useState('');

  // API & MCP State
  const [apiKeys, setApiKeys] = useState([]);
  const [showAddApiKeyModal, setShowAddApiKeyModal] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [createdRawToken, setCreatedRawToken] = useState('');
  const [copiedMcp, setCopiedMcp] = useState(false);
  const [testingMcp, setTestingMcp] = useState(false);
  const [mcpTestResult, setMcpTestResult] = useState(null);

  useEffect(() => {
    loadWritingProfile();
    loadIntegrations();
    loadApiTokens();
  }, []);

  const loadIntegrations = async () => {
    try {
      const data = await integrationsApi.list();
      if (Array.isArray(data)) setIntegrations(data);
    } catch (e) {
      console.error('Failed to load integrations:', e);
    }
  };

  const loadApiTokens = async () => {
    try {
      const data = await apiTokensApi.list();
      if (Array.isArray(data)) setApiKeys(data);
    } catch (e) {
      console.error('Failed to load API tokens:', e);
    }
  };

  const getMcpEndpointUrl = () => {
    const base = (API_BASE || '/api/v1').replace(/\/api\/v1\/?$/, '');
    return base.startsWith('http') ? `${base}/mcp` : `${window.location.protocol}//${window.location.host}/mcp`;
  };

  const handleTestMcp = async () => {
    setTestingMcp(true);
    setMcpTestResult(null);
    try {
      const mcpUrl = getMcpEndpointUrl();
      const res = await fetch(mcpUrl);
      const data = await res.json();
      if (data && data.status === 'online') {
        setMcpTestResult({ success: true, message: `MCP Server Online — ${data.name} (${data.tools_count} tools registered)` });
      } else {
        setMcpTestResult({ success: false, message: 'MCP server returned invalid response status.' });
      }
    } catch (err) {
      setMcpTestResult({ success: false, message: `MCP Connection test failed: ${err.message}` });
    } finally {
      setTestingMcp(false);
    }
  };

  const handleToggleIntegration = (id) => {
    setSaveSuccess('Integration status managed via OAuth.');
    setTimeout(() => setSaveSuccess(''), 3000);
  };

  const handleAddIntegration = (e) => {
    e.preventDefault();
    setShowAddIntegrationModal(false);
    setNewIntegrationKey('');
    setSaveSuccess('Integration endpoint configured!');
    setTimeout(() => setSaveSuccess(''), 3000);
  };

  const handleCreateApiKey = async (e) => {
    e.preventDefault();
    if (!newKeyName.trim()) return;
    try {
      const res = await apiTokensApi.create(newKeyName);
      if (res && res.token) {
        setCreatedRawToken(res.token);
        setShowAddApiKeyModal(false);
        setNewKeyName('');
        await loadApiTokens();
        setSaveSuccess(`Generated new API Token: ${res.name}`);
        setTimeout(() => setSaveSuccess(''), 3000);
      }
    } catch (err) {
      setSaveSuccess(`Failed to create API Token: ${err.message}`);
    }
  };

  const handleRevokeApiKey = async (tokenId) => {
    try {
      await apiTokensApi.revoke(tokenId);
      await loadApiTokens();
      setSaveSuccess('API Token revoked successfully.');
      setTimeout(() => setSaveSuccess(''), 3000);
    } catch (err) {
      setSaveSuccess(`Failed to revoke token: ${err.message}`);
    }
  };

  const handleCopyMcp = () => {
    navigator.clipboard.writeText(getMcpEndpointUrl());
    setCopiedMcp(true);
    setTimeout(() => setCopiedMcp(false), 2500);
  };


  const loadWritingProfile = async () => {
    try {
      const data = await authApi.getWritingProfile();
      if (data) {
        setBio(data.bio || bio);
        setSchedulingLink(data.scheduling_link || schedulingLink);
        setSignOff(data.sign_off || signOff);
        setWritingPrompt(data.writing_prompt || writingPrompt);
      }
    } catch (e) {}
  };

  const handleSaveWritingProfile = async () => {
    try {
      await authApi.updateWritingProfile({ bio, scheduling_link: schedulingLink, sign_off: signOff, writing_prompt: writingPrompt });
      setSaveSuccess('Writing profile updated successfully!');
      setTimeout(() => setSaveSuccess(''), 3000);
    } catch (err) {
      setSaveSuccess('Failed to save profile: ' + err.message);
    }
  };

  const navItems = [
    { id: 'team', label: 'My Team', icon: Users },
    { id: 'theme', label: 'Theme', icon: Palette },
    { id: 'signatures', label: 'Signatures', icon: FileSignature },
    { id: 'filters', label: 'Filters', icon: Filter },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'api-mcp', label: 'API and MCP', icon: Code2 },
    { id: 'integrations', label: 'Integrations', icon: Layers },
    { id: 'billing', label: 'Billing', icon: Building2 },
    { id: 'workspace', label: 'Workspace', icon: Building2 },
    { id: 'preferences', label: 'Preferences', icon: Sliders },
    { id: 'writing-style', label: 'Writing Style & Tone', icon: PenTool },
  ];

  const subNavItems = [
    { id: 'inbox-tabs', label: 'Inbox Tabs', icon: InboxIcon },
    { id: 'agents', label: 'Configure Agents', icon: Bot },
  ];

  return (
    <div className="flex h-full bg-[#EBF2FA] select-none p-3 gap-3 overflow-hidden relative">
      {/* Main Settings Card Overlay Container */}
      <div className="flex-1 bg-[#F0F5FA] rounded-[24px] border border-[#DCE5EF] shadow-2xl flex flex-col min-w-0 overflow-hidden animate-scale-in">
        {/* Settings Card Header Bar */}
        <div className="px-6 py-3 border-b border-[#DCE5EF] bg-[#F0F5FA] flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold text-[#172335]">Settings</span>
          </div>

          {/* Center Search Input */}
          <div className="relative flex items-center w-72">
            <Search className="w-3.5 h-3.5 text-[#8fa0b1] absolute left-3" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full h-8 pl-8 pr-7 bg-white border border-[#DCE5EF] rounded-xl text-xs text-[#172335] focus:outline-none focus:border-[#2d7ed0]"
              placeholder="Search settings..."
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-2.5 text-[#8fa0b1] hover:text-[#172335]"
              >
                <X className="w-3 h-3" />
              </button>
            )}
          </div>

          {/* Right Header Status Badges */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-[11px] text-[#5e7186] bg-white/60 px-2.5 py-1 rounded-lg border border-[#DCE5EF]">
              <span className="w-2 h-2 rounded-full bg-[#48A97B] animate-pulse" />
              <span>Syncing your messages...</span>
            </div>

            <div className="w-7 h-7 rounded-full bg-[#2d7ed0] text-white font-bold text-xs flex items-center justify-center border border-white shadow-2xs">
              {user?.full_name ? user.full_name.charAt(0) : 'U'}
            </div>

            <button
              onClick={() => navigate('/inbox')}
              className="p-1 text-[#5e7186] hover:text-[#172335] rounded-md transition-colors ml-1"
              title="Close Settings"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Settings Body: Left Navigation Column + Right Content Area */}
        <div className="flex-1 flex min-h-0 overflow-hidden">
          {/* Left Menu Column */}
          <div className="w-56 p-4 border-r border-[#DCE5EF] flex flex-col justify-between shrink-0 overflow-y-auto bg-[#F0F5FA]">
            <div className="flex flex-col gap-1">
              <span className="text-[11px] font-bold text-[#8fa0b1] uppercase tracking-wider px-2 mb-1">Settings</span>
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = currentTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => navigate(`/settings/${item.id}`)}
                    className={`w-full px-3 py-2 rounded-xl flex items-center gap-2.5 text-xs font-semibold transition-all ${
                      isActive
                        ? 'bg-white text-[#172335] font-bold shadow-2xs border border-[#DCE5EF]'
                        : 'text-[#536176] hover:bg-[#E2EEF8] hover:text-[#172335]'
                    }`}
                  >
                    <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-[#2d7ed0]' : 'text-[#8fa0b1]'}`} />
                    <span className="truncate">{item.label}</span>
                  </button>
                );
              })}

              <div className="w-full h-[1px] bg-[#DCE5EF] my-2" />

              {subNavItems.map((item) => {
                const Icon = item.icon;
                const isActive = currentTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => navigate(`/settings/${item.id}`)}
                    className={`w-full px-3 py-2 rounded-xl flex items-center gap-2.5 text-xs font-semibold transition-all ${
                      isActive
                        ? 'bg-white text-[#172335] font-bold shadow-2xs border border-[#DCE5EF]'
                        : 'text-[#536176] hover:bg-[#E2EEF8] hover:text-[#172335]'
                    }`}
                  >
                    <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-[#2d7ed0]' : 'text-[#8fa0b1]'}`} />
                    <span className="truncate">{item.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Right Main Content Area */}
          <div className="flex-1 p-8 overflow-y-auto bg-white/40">
            {saveSuccess && (
              <div className="mb-4 p-3 bg-[#ECFDF5] border border-[#A7F3D0] rounded-xl text-xs text-[#065F46] font-semibold flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-[#059669]" />
                <span>{saveSuccess}</span>
              </div>
            )}

            {/* 1. MY TEAM TAB (Reusing TeamPage component directly) */}
            {currentTab === 'team' && (
              <div className="animate-fade-in">
                <TeamPage />
              </div>
            )}

            {/* 2. SIGNATURES TAB */}
            {currentTab === 'signatures' && (
              <div className="flex flex-col gap-6 max-w-2xl animate-fade-in">
                <div>
                  <h1 className="text-lg font-bold text-[#172335] mb-1">Signatures</h1>
                </div>

                <div className="flex flex-col gap-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-xs font-bold text-[#172335]">Gmail</h3>
                      <p className="text-[11px] text-[#5e7186] mt-0.5">
                        Include your Gmail signature on all outgoing messages.
                      </p>
                    </div>

                    <button
                      onClick={() => setEnableGmailSignature(!enableGmailSignature)}
                      className={`w-10 h-5 rounded-full transition-colors relative p-0.5 ${
                        enableGmailSignature ? 'bg-[#2d7ed0]' : 'bg-[#DCE5EF]'
                      }`}
                    >
                      <span className={`w-4 h-4 rounded-full bg-white block transition-transform ${
                        enableGmailSignature ? 'translate-x-5' : 'translate-x-0'
                      }`} />
                    </button>
                  </div>

                  <div className="p-4 bg-white border border-[#E6DFD5] rounded-2xl text-xs text-[#8fa0b1] shadow-2xs">
                    No default signature set, managed in Gmail.
                  </div>
                </div>

                <div className="flex flex-col gap-3 pt-2">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-xs font-bold text-[#172335]">FlowInbox</h3>
                      <p className="text-[11px] text-[#5e7186] mt-0.5">
                        Add a clean FlowInbox signature line to outgoing messages.
                      </p>
                    </div>

                    <button
                      onClick={() => setEnableFlowInboxSignature(!enableFlowInboxSignature)}
                      className={`w-10 h-5 rounded-full transition-colors relative p-0.5 ${
                        enableFlowInboxSignature ? 'bg-[#2d7ed0]' : 'bg-[#DCE5EF]'
                      }`}
                    >
                      <span className={`w-4 h-4 rounded-full bg-white block transition-transform ${
                        enableFlowInboxSignature ? 'translate-x-5' : 'translate-x-0'
                      }`} />
                    </button>
                  </div>

                  <div className="flex items-center gap-2 text-xs text-[#5e7186]">
                    <span>Include:</span>
                    <span className="px-3 py-1 bg-white border border-[#E6DFD5] rounded-xl font-medium text-[#172335] shadow-2xs">
                      Sent using <span className="text-[#2d7ed0] font-bold">FlowInbox</span>
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* 3. INTEGRATIONS TAB */}
            {currentTab === 'integrations' && (
              <div className="flex flex-col gap-5 max-w-2xl animate-fade-in">
                <div className="flex items-center justify-between">
                  <div>
                    <h1 className="text-lg font-bold text-[#172335]">Integrations</h1>
                    <p className="text-xs text-[#5e7186] mt-0.5">Connect external workspace tools & apps to FlowInbox.</p>
                  </div>
                  <button
                    onClick={() => setShowAddIntegrationModal(true)}
                    className="px-3.5 h-8 bg-[#3186D8] hover:bg-[#2366A8] text-white text-xs font-semibold rounded-xl shadow-2xs transition-colors flex items-center gap-1.5"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Connect New App</span>
                  </button>
                </div>

                <div className="divide-y divide-[#E6DFD5] border border-[#E6DFD5] bg-white rounded-3xl p-4 shadow-2xs">
                  {integrations.map((item) => (
                    <div key={item.id} className="flex items-center gap-4 py-3.5 px-2">
                      <span className="w-10 h-10 rounded-2xl border border-[#E6DFD5] bg-[#FAF6F0] flex items-center justify-center font-extrabold text-xs text-[#2d7ed0] shadow-2xs shrink-0">
                        {item.icon}
                      </span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <h4 className="text-xs font-bold text-[#172335]">{item.name}</h4>
                          <span className="px-2 py-0.2 bg-[#f0f4f8] text-[#5e7186] text-[10px] font-bold rounded">
                            {item.category}
                          </span>
                        </div>
                        <p className="text-[11px] text-[#5e7186] mt-0.5">{item.desc}</p>
                      </div>

                      <button
                        onClick={() => handleToggleIntegration(item.id)}
                        className={`px-3 py-1 text-xs font-semibold rounded-xl border transition-all ${
                          item.status === 'Connected'
                            ? 'bg-[#ECFDF5] text-[#059669] border-[#A7F3D0] hover:bg-[#d1fae5]'
                            : 'bg-[#FAF6F0] text-[#2d7ed0] border-[#DCE5EF] hover:bg-[#eaf3fb]'
                        }`}
                      >
                        {item.status === 'Connected' ? '✓ Connected' : '+ Connect'}
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 4. WORKSPACE TAB */}
            {currentTab === 'workspace' && (
              <div className="flex flex-col gap-5 max-w-2xl animate-fade-in">
                <div>
                  <h1 className="text-lg font-bold text-[#172335]">Workspace Settings</h1>
                  <p className="text-xs text-[#5e7186] mt-0.5">Manage your workspace identity and team settings.</p>
                </div>

                <div className="p-5 bg-white border border-[#DCE5EF] rounded-2xl flex flex-col gap-4 shadow-2xs">
                  <div>
                    <label className="block text-xs font-bold text-[#172335] mb-1">Workspace Name</label>
                    <input
                      type="text"
                      value={workspaceName}
                      onChange={(e) => setWorkspaceName(e.target.value)}
                      className="w-full h-9 px-3 bg-[#FAF6F0] border border-[#DCE5EF] rounded-xl text-xs text-[#172335] focus:outline-none focus:border-[#2d7ed0]"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-[#172335] mb-1">Workspace Slug</label>
                    <input
                      type="text"
                      value={workspaceSlug}
                      onChange={(e) => setWorkspaceSlug(e.target.value)}
                      className="w-full h-9 px-3 bg-[#FAF6F0] border border-[#DCE5EF] rounded-xl text-xs text-[#172335] focus:outline-none focus:border-[#2d7ed0]"
                    />
                  </div>

                  <div className="pt-2">
                    <button
                      onClick={() => {
                        setSaveSuccess('Workspace settings saved!');
                        setTimeout(() => setSaveSuccess(''), 3000);
                      }}
                      className="px-4 h-8 bg-[#3186D8] hover:bg-[#2366A8] text-white text-xs font-semibold rounded-xl shadow-2xs transition-colors"
                    >
                      Save Workspace Changes
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* 5. PREFERENCES TAB */}
            {currentTab === 'preferences' && (
              <div className="flex flex-col gap-5 max-w-2xl animate-fade-in">
                <div>
                  <h1 className="text-lg font-bold text-[#172335]">Preferences</h1>
                  <p className="text-xs text-[#5e7186] mt-0.5">Customize your inbox interaction preferences.</p>
                </div>

                <div className="p-5 bg-white border border-[#DCE5EF] rounded-2xl flex flex-col gap-4 shadow-2xs">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-xs font-bold text-[#172335]">Auto-advance after triage</h4>
                      <p className="text-[11px] text-[#5e7186]">Automatically open next thread after archiving or snoozing.</p>
                    </div>
                    <button
                      onClick={() => setAutoAdvance(!autoAdvance)}
                      className={`w-10 h-5 rounded-full transition-colors relative p-0.5 ${autoAdvance ? 'bg-[#2d7ed0]' : 'bg-[#DCE5EF]'}`}
                    >
                      <span className={`w-4 h-4 rounded-full bg-white block transition-transform ${autoAdvance ? 'translate-x-5' : 'translate-x-0'}`} />
                    </button>
                  </div>

                  <div className="w-full h-[1px] bg-[#E9EFF5]" />

                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-xs font-bold text-[#172335]">Sound Notifications</h4>
                      <p className="text-[11px] text-[#5e7186]">Play subtle chime when high priority emails arrive.</p>
                    </div>
                    <button
                      onClick={() => setSoundNotifications(!soundNotifications)}
                      className={`w-10 h-5 rounded-full transition-colors relative p-0.5 ${soundNotifications ? 'bg-[#2d7ed0]' : 'bg-[#DCE5EF]'}`}
                    >
                      <span className={`w-4 h-4 rounded-full bg-white block transition-transform ${soundNotifications ? 'translate-x-5' : 'translate-x-0'}`} />
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* 6. BILLING TAB */}
            {currentTab === 'billing' && (
              <div className="flex flex-col gap-5 max-w-2xl animate-fade-in">
                <div>
                  <h1 className="text-lg font-bold text-[#172335]">Billing & Subscription</h1>
                  <p className="text-xs text-[#5e7186] mt-0.5">Manage your FlowInbox plan and usage limits.</p>
                </div>

                <div className="p-5 bg-white border border-[#DCE5EF] rounded-2xl flex flex-col gap-4 shadow-2xs">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="px-2.5 py-0.5 bg-[#E7F1FC] text-[#3186D8] font-bold text-[10px] rounded-full uppercase">Current Plan</span>
                      <h3 className="text-base font-bold text-[#172335] mt-1">FlowInbox Community Edition</h3>
                      <p className="text-xs text-[#5e7186] mt-0.5">Unlimited email thread synchronization & AI agent triage.</p>
                    </div>
                    <span className="text-lg font-black text-[#172335]">$0 <span className="text-xs font-normal text-[#8fa0b1]">/ month</span></span>
                  </div>

                  <div className="w-full h-[1px] bg-[#E9EFF5]" />

                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="p-3 bg-[#FAF6F0] rounded-xl border border-[#E6DFD5]">
                      <span className="text-[10px] font-bold text-[#8fa0b1] uppercase">AI Action Quota</span>
                      <p className="font-bold text-[#172335] mt-0.5">Unlimited local executions</p>
                    </div>
                    <div className="p-3 bg-[#FAF6F0] rounded-xl border border-[#E6DFD5]">
                      <span className="text-[10px] font-bold text-[#8fa0b1] uppercase">Connected Accounts</span>
                      <p className="font-bold text-[#172335] mt-0.5">1 Active Gmail Account</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* 7. THEME TAB */}
            {currentTab === 'theme' && (
              <div className="flex flex-col gap-5 max-w-2xl animate-fade-in">
                <div>
                  <h1 className="text-lg font-bold text-[#172335]">Theme & Color Palette</h1>
                  <p className="text-xs text-[#5e7186] mt-0.5">Select your workspace visual theme preference.</p>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  {[
                    {
                      id: 'cream',
                      name: 'FlowInbox Cream',
                      desc: 'Warm Cream & Soft Blue (Default)',
                      previewBg: 'bg-[#FAF6F0]',
                      previewBorder: 'border-[#d7e3ee]',
                      accentBg: 'bg-[#2d7ed0]',
                      textColor: 'text-[#172335]'
                    },
                    {
                      id: 'dark',
                      name: 'Modern Dark',
                      desc: 'Sleek Dark Gray & Sky Blue',
                      previewBg: 'bg-[#0F172A]',
                      previewBorder: 'border-[#334155]',
                      accentBg: 'bg-[#38BDF8]',
                      textColor: 'text-white'
                    },
                    {
                      id: 'slate',
                      name: 'Indigo Slate',
                      desc: 'Cool Slate & Indigo Accent',
                      previewBg: 'bg-[#111827]',
                      previewBorder: 'border-[#374151]',
                      accentBg: 'bg-[#6366F1]',
                      textColor: 'text-white'
                    }
                  ].map((t) => {
                    const isSelected = (theme || 'cream') === t.id;
                    return (
                      <div
                        key={t.id}
                        onClick={() => {
                          setTheme(t.id);
                          setSaveSuccess(`Theme updated to ${t.name}!`);
                          setTimeout(() => setSaveSuccess(''), 3000);
                        }}
                        className={`p-4 rounded-2xl border-2 cursor-pointer transition-all flex flex-col justify-between ${
                          isSelected
                            ? 'border-[#3186D8] bg-white shadow-md ring-2 ring-[#3186D8]/20'
                            : 'border-[#DCE5EF] bg-[#F7FAFD] hover:bg-white hover:border-[#b9d2e8]'
                        }`}
                      >
                        <div>
                          <div className={`w-full h-20 rounded-xl ${t.previewBg} border ${t.previewBorder} mb-3 p-3 flex flex-col justify-between shadow-2xs`}>
                            <div className="flex items-center justify-between">
                              <span className={`text-[10px] font-bold ${t.textColor}`}>{t.name}</span>
                              <span className={`w-3 h-3 rounded-full ${t.accentBg}`} />
                            </div>
                            <div className="w-full h-2 rounded bg-current opacity-20" />
                          </div>
                          <h4 className="text-xs font-bold text-[#172335] flex items-center justify-between">
                            <span>{t.name}</span>
                            {isSelected && <CheckCircle2 className="w-4 h-4 text-[#3186D8]" />}
                          </h4>
                          <p className="text-[11px] text-[#5e7186] mt-0.5">{t.desc}</p>
                        </div>
                        {isSelected && (
                          <span className="mt-3 px-2 py-0.5 bg-[#E7F1FC] text-[#3186D8] text-[10px] font-bold rounded-md self-start">
                            Active Theme
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* 8. FILTERS TAB */}
            {currentTab === 'filters' && (
              <div className="flex flex-col gap-5 max-w-2xl animate-fade-in">
                <div>
                  <h1 className="text-lg font-bold text-[#172335]">Inbox Filters & Rules</h1>
                  <p className="text-xs text-[#5e7186] mt-0.5">Automated triage rules for organizing incoming messages.</p>
                </div>

                <div className="p-4 bg-white border border-[#DCE5EF] rounded-2xl flex flex-col gap-3 shadow-2xs">
                  {[
                    { title: 'Needs Reply Detection', desc: 'Identify emails requiring action and flag them in Needs Reply tab.' },
                    { title: 'Follow-Up Tracker', desc: 'Track sent emails that haven’t received a response after 48 hours.' }
                  ].map((rule, i) => (
                    <div key={i} className="flex items-center justify-between p-3 bg-[#FAF6F0] rounded-xl border border-[#E6DFD5]">
                      <div>
                        <h4 className="text-xs font-bold text-[#172335]">{rule.title}</h4>
                        <p className="text-[11px] text-[#5e7186]">{rule.desc}</p>
                      </div>
                      <span className="px-2 py-0.5 bg-[#ECFDF5] text-[#059669] font-bold text-[10px] rounded">Active</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 9. NOTIFICATIONS TAB */}
            {currentTab === 'notifications' && (
              <div className="flex flex-col gap-5 max-w-2xl animate-fade-in">
                <div>
                  <h1 className="text-lg font-bold text-[#172335]">Notification Preferences</h1>
                  <p className="text-xs text-[#5e7186] mt-0.5">Control alert settings for workspace updates.</p>
                </div>

                <div className="p-5 bg-white border border-[#DCE5EF] rounded-2xl flex flex-col gap-4 shadow-2xs">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-xs font-bold text-[#172335]">Agent Action Approvals</h4>
                      <p className="text-[11px] text-[#5e7186]">Alert when an agent requests approval before sending emails.</p>
                    </div>
                    <button onClick={() => setNotifyApprovals(!notifyApprovals)} className={`w-10 h-5 rounded-full transition-colors relative p-0.5 ${notifyApprovals ? 'bg-[#2d7ed0]' : 'bg-[#DCE5EF]'}`}>
                      <span className={`w-4 h-4 rounded-full bg-white block transition-transform ${notifyApprovals ? 'translate-x-5' : 'translate-x-0'}`} />
                    </button>
                  </div>

                  <div className="w-full h-[1px] bg-[#E9EFF5]" />

                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-xs font-bold text-[#172335]">Needs Reply Reminders</h4>
                      <p className="text-[11px] text-[#5e7186]">Highlight urgent messages needing your response.</p>
                    </div>
                    <button onClick={() => setNotifyNeedsReply(!notifyNeedsReply)} className={`w-10 h-5 rounded-full transition-colors relative p-0.5 ${notifyNeedsReply ? 'bg-[#2d7ed0]' : 'bg-[#DCE5EF]'}`}>
                      <span className={`w-4 h-4 rounded-full bg-white block transition-transform ${notifyNeedsReply ? 'translate-x-5' : 'translate-x-0'}`} />
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* 10. API & MCP TAB */}
            {currentTab === 'api-mcp' && (
              <div className="flex flex-col gap-5 max-w-2xl animate-fade-in">
                <div className="flex items-center justify-between">
                  <div>
                    <h1 className="text-lg font-bold text-[#172335]">API & Model Context Protocol (MCP)</h1>
                    <p className="text-xs text-[#5e7186] mt-0.5">Manage live API keys and connect external MCP tools.</p>
                  </div>
                  <button
                    onClick={() => setShowAddApiKeyModal(true)}
                    className="px-3.5 h-8 bg-[#3186D8] hover:bg-[#2366A8] text-white text-xs font-semibold rounded-xl shadow-2xs transition-colors flex items-center gap-1.5"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Generate API Key</span>
                  </button>
                </div>

                <div className="p-5 bg-white border border-[#DCE5EF] rounded-2xl flex flex-col gap-4 shadow-2xs">
                  <div>
                    <label className="block text-[11px] font-bold text-[#8fa0b1] uppercase mb-1">MCP HTTP Endpoint</label>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 p-2.5 bg-[#FAF6F0] border border-[#E6DFD5] rounded-xl font-mono text-xs text-[#172033] font-bold truncate">
                        {getMcpEndpointUrl()}
                      </div>
                      <button
                        onClick={handleCopyMcp}
                        className="px-3.5 h-9 bg-[#FAF6F0] hover:bg-[#eaf3fb] border border-[#DCE5EF] text-[#2d7ed0] text-xs font-bold rounded-xl shadow-2xs transition-colors flex items-center gap-1.5 shrink-0"
                      >
                        {copiedMcp ? <Check className="w-3.5 h-3.5 text-[#059669]" /> : <Code2 className="w-3.5 h-3.5" />}
                        <span>{copiedMcp ? 'Copied!' : 'Copy Endpoint'}</span>
                      </button>
                      <button
                        onClick={handleTestMcp}
                        disabled={testingMcp}
                        className="px-3.5 h-9 bg-[#3186D8] hover:bg-[#2366A8] disabled:opacity-50 text-white text-xs font-bold rounded-xl shadow-2xs transition-colors flex items-center gap-1.5 shrink-0"
                      >
                        <RotateCw className={`w-3.5 h-3.5 ${testingMcp ? 'animate-spin' : ''}`} />
                        <span>{testingMcp ? 'Testing...' : 'Test MCP'}</span>
                      </button>
                    </div>

                    {mcpTestResult && (
                      <div className={`mt-2 p-2.5 text-xs rounded-xl flex items-center gap-2 font-medium ${
                        mcpTestResult.success ? 'bg-[#ECFDF5] text-[#047857] border border-[#A7F3D0]' : 'bg-[#FEF2F2] text-[#B91C1C] border border-[#FFECB3]'
                      }`}>
                        <CheckCircle2 className="w-4 h-4 shrink-0" />
                        <span>{mcpTestResult.message}</span>
                      </div>
                    )}
                  </div>

                  <div className="w-full h-[1px] bg-[#E9EFF5]" />

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="block text-[11px] font-bold text-[#8fa0b1] uppercase">Active API Access Tokens ({apiKeys.length})</label>
                    </div>

                    <div className="divide-y divide-[#f0f5fa] border border-[#DCE5EF] bg-[#FAF6F0]/60 rounded-xl overflow-hidden">
                      {apiKeys.length === 0 ? (
                        <div className="p-4 text-xs text-[#5e7186] text-center">No active API tokens found.</div>
                      ) : (
                        apiKeys.map((key) => (
                          <div key={key.id} className="p-3 flex items-center justify-between">
                            <div>
                              <h4 className="text-xs font-bold text-[#172335]">{key.name}</h4>
                              <p className="text-[10px] font-mono text-[#5e7186] mt-0.5">
                                Token ID: {key.id.substring(0, 8)}... • Created {new Date(key.created_at).toLocaleDateString()}
                              </p>
                            </div>
                            <button
                              onClick={() => handleRevokeApiKey(key.id)}
                              className="text-[11px] font-semibold text-[#D95D5D] hover:underline"
                            >
                              Revoke
                            </button>
                          </div>
                        ))
                      )}
                    </div>
                  </div>

                  <div className="w-full h-[1px] bg-[#E9EFF5]" />

                  <div>
                    <label className="block text-[11px] font-bold text-[#8fa0b1] uppercase mb-1.5">Registered Agent Tools</label>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      {['search_emails', 'get_thread', 'get_events', 'list_pending_approvals', 'create_draft', 'propose_send_email', 'propose_create_event'].map((tool) => (
                        <div key={tool} className="p-2.5 bg-[#FAF6F0] border border-[#E6DFD5] rounded-xl font-mono text-[#2d7ed0] flex items-center justify-between">
                          <span>{tool}</span>
                          <span className="text-[9px] font-extrabold uppercase px-1.5 py-0.5 rounded bg-[#eaf3fb] text-[#2d7ed0]">MCP 1.0</span>
                        </div>
                      ))}
                    </div>
                  </div>

                </div>
              </div>
            )}

            {/* 11. WRITING STYLE TAB */}
            {currentTab === 'writing-style' && (
              <div className="flex flex-col gap-5 max-w-2xl animate-fade-in">
                <div>
                  <h1 className="text-lg font-bold text-[#172335]">Writing Style & Tone</h1>
                  <p className="text-xs text-[#5e7186] mt-0.5">Define your writing style and how it adapts by audience.</p>
                </div>

                <div className="flex flex-col gap-3">
                  <div>
                    <label className="text-xs font-bold text-[#172335]">Sign-off Pattern</label>
                    <input
                      type="text"
                      value={signOff}
                      onChange={(e) => setSignOff(e.target.value)}
                      className="w-full h-9 px-3 bg-white border border-[#E6DFD5] rounded-xl text-xs text-[#172335] focus:outline-none focus:border-[#2d7ed0] mt-1"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-bold text-[#172335]">Writing Style Prompt</label>
                    <textarea
                      rows={6}
                      value={writingPrompt}
                      onChange={(e) => setWritingPrompt(e.target.value)}
                      className="w-full p-4 bg-white border border-[#E6DFD5] rounded-2xl text-xs font-mono text-[#172335] focus:outline-none focus:border-[#2d7ed0] mt-1"
                    />
                  </div>

                  <div>
                    <button
                      onClick={handleSaveWritingProfile}
                      className="px-4 h-8 bg-[#3186D8] hover:bg-[#2366A8] text-white text-xs font-semibold rounded-xl shadow-2xs transition-colors"
                    >
                      Save Writing Profile
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* MODAL 1: Connect New Integration */}
      {showAddIntegrationModal && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs z-50 flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white rounded-3xl border border-[#DCE5EF] p-6 w-full max-w-md shadow-2xl flex flex-col gap-4 animate-scale-in">
            <div className="flex items-center justify-between border-b border-[#f0f4f8] pb-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-[#eaf3fb] text-[#2d7ed0] font-extrabold flex items-center justify-center text-xs">
                  <Layers className="w-4 h-4" />
                </div>
                <h3 className="text-sm font-bold text-[#172335]">Connect New App Integration</h3>
              </div>
              <button onClick={() => setShowAddIntegrationModal(false)} className="p-1 text-[#8fa0b1] hover:text-[#172335]">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleAddIntegration} className="flex flex-col gap-3">
              <div>
                <label className="block text-xs font-bold text-[#172335] mb-1">Integration Provider</label>
                <select
                  value={newIntegrationType}
                  onChange={(e) => setNewIntegrationType(e.target.value)}
                  className="w-full h-9 px-3 bg-[#FAF6F0] border border-[#DCE5EF] rounded-xl text-xs text-[#172335] focus:outline-none"
                >
                  <option value="slack">Slack Workspace</option>
                  <option value="notion">Notion Workspace</option>
                  <option value="github">GitHub Enterprise</option>
                  <option value="gworkspace">Google Workspace</option>
                  <option value="webhook">Custom Webhook Endpoint</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-[#172335] mb-1">API Key / Token / Webhook URL</label>
                <input
                  type="text"
                  value={newIntegrationKey}
                  onChange={(e) => setNewIntegrationKey(e.target.value)}
                  placeholder="Paste your API key, secret token, or webhook endpoint..."
                  className="w-full h-9 px-3 bg-[#FAF6F0] border border-[#DCE5EF] rounded-xl text-xs text-[#172335] focus:outline-none"
                  required
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddIntegrationModal(false)}
                  className="px-4 h-8 bg-white border border-[#DCE5EF] text-[#5e7186] text-xs font-semibold rounded-xl hover:bg-[#FAF6F0]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 h-8 bg-[#3186D8] hover:bg-[#2366A8] text-white text-xs font-semibold rounded-xl shadow-2xs"
                >
                  Connect Integration
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: Generate API Key */}
      {showAddApiKeyModal && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs z-50 flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white rounded-3xl border border-[#DCE5EF] p-6 w-full max-w-md shadow-2xl flex flex-col gap-4 animate-scale-in">
            <div className="flex items-center justify-between border-b border-[#f0f4f8] pb-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-[#eaf3fb] text-[#2d7ed0] font-extrabold flex items-center justify-center text-xs">
                  <Code2 className="w-4 h-4" />
                </div>
                <h3 className="text-sm font-bold text-[#172335]">Generate Live API Access Key</h3>
              </div>
              <button onClick={() => setShowAddApiKeyModal(false)} className="p-1 text-[#8fa0b1] hover:text-[#172335]">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateApiKey} className="flex flex-col gap-3">
              <div>
                <label className="block text-xs font-bold text-[#172335] mb-1">Key Description Label</label>
                <input
                  type="text"
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  placeholder="e.g. Production MCP Client, CLI Agent Token..."
                  className="w-full h-9 px-3 bg-[#FAF6F0] border border-[#DCE5EF] rounded-xl text-xs text-[#172335] focus:outline-none"
                  required
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddApiKeyModal(false)}
                  className="px-4 h-8 bg-white border border-[#DCE5EF] text-[#5e7186] text-xs font-semibold rounded-xl hover:bg-[#FAF6F0]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 h-8 bg-[#3186D8] hover:bg-[#2366A8] text-white text-xs font-semibold rounded-xl shadow-2xs"
                >
                  Generate Key
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 3: Display Generated Token (ONCE) */}
      {createdRawToken && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-xs z-50 flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white rounded-3xl border border-[#DCE5EF] p-6 w-full max-w-lg shadow-2xl flex flex-col gap-4 animate-scale-in">
            <div className="flex items-center justify-between border-b border-[#f0f4f8] pb-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-[#ECFDF5] text-[#059669] font-extrabold flex items-center justify-center text-xs">
                  <ShieldCheck className="w-4 h-4" />
                </div>
                <h3 className="text-sm font-bold text-[#172335]">Save Your Secret API Token</h3>
              </div>
              <button onClick={() => setCreatedRawToken('')} className="p-1 text-[#8fa0b1] hover:text-[#172335]">
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-[#5e7186]">
              Please copy and store this API token securely. <strong>It will not be shown again!</strong>
            </p>

            <div className="p-3 bg-[#FAF6F0] border border-[#E6DFD5] rounded-xl font-mono text-xs text-[#172335] font-bold break-all flex items-center justify-between gap-2">
              <span>{createdRawToken}</span>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(createdRawToken);
                  setSaveSuccess('API Token copied to clipboard!');
                  setTimeout(() => setSaveSuccess(''), 3000);
                }}
                className="px-3 py-1 bg-[#2d7ed0] text-white text-xs font-bold rounded-lg shrink-0 hover:bg-[#2366a8]"
              >
                Copy
              </button>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setCreatedRawToken('')}
                className="px-4 h-8 bg-[#3186D8] hover:bg-[#2366A8] text-white text-xs font-semibold rounded-xl shadow-2xs"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

