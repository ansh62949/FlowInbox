import React, { useState, useEffect, useRef } from 'react';
import { 
  Bot, Send, Sparkles, User, CheckCircle2, ChevronRight, Trash2, 
  Plus, CornerDownLeft, ShieldCheck, Mail, FileText, Zap, RefreshCw, 
  ArrowRight, MessageSquare, ChevronDown, ChevronUp, Layers
} from 'lucide-react';
import agentsApi from '../api/agents';
import { useAuth } from '../context/AuthContext';
import FormattedMarkdown from '../components/ai/FormattedMarkdown';

const DEFAULT_AGENTS = [
  {
    id: 'orchestrator',
    name: 'FlowInbox Orchestrator',
    status: 'active',
    role: 'Primary AI Assistant',
    description: 'Autonomous LangGraph agent that searches inbox, categorizes emails, and drafts replies.',
    model: 'Groq Llama 3 70B',
    permissions: 'Inbox Read/Write, Drafts, Search',
    suggestedPrompts: [
      { title: 'Summarize Unread Emails', query: 'Scan my inbox and give me a brief 3-bullet summary of unread emails.' },
      { title: 'Check Pending Approvals', query: 'List all action items and draft replies currently waiting for my approval.' },
      { title: 'Draft Follow-Up Reply', query: 'Draft a polite, warm professional follow-up for my recent project discussions.' },
      { title: 'Find Invoices & Receipts', query: 'Search for all receipt and payment confirmation emails from this month.' }
    ]
  },
  {
    id: 'triage_bot',
    name: 'Triage & Categorization Bot',
    status: 'active',
    role: 'Channel Triage',
    description: 'Automatically sorts incoming messages into dedicated team channels and flags urgent tasks.',
    model: 'Groq Llama 3 70B',
    permissions: 'Channel Routing, Category Labeling',
    suggestedPrompts: [
      { title: 'Analyze Inbox Categories', query: 'What categories of emails came in today?' },
      { title: 'Flag Priority Threads', query: 'Show me all high-priority threads needing immediate reply.' }
    ]
  },
  {
    id: 'voice_agent',
    name: 'Writing Tone & Style Agent',
    status: 'active',
    role: 'Style Mimicry',
    description: 'Learns your unique greeting, sign-off, and formality patterns to write emails that sound like you.',
    model: 'Gemini 1.5 Flash',
    permissions: 'Tone Analysis, Response Generation',
    suggestedPrompts: [
      { title: 'Analyze Writing Style', query: 'Analyze my sent emails and describe my current writing style and tone.' },
      { title: 'Draft in My Style', query: 'Draft an email thanking a collaborator for their hard work using my signature style.' }
    ]
  }
];

export default function AgentsPage() {
  const { user } = useAuth();
  const [agents, setAgents] = useState(DEFAULT_AGENTS);
  const [selectedAgent, setSelectedAgent] = useState(DEFAULT_AGENTS[0]);
  const [messages, setMessages] = useState(() => {
    const saved = localStorage.getItem('flowinbox_agent_chat');
    return saved ? JSON.parse(saved) : [];
  });
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState('Groq Llama 3 70B');
  const [expandedSteps, setExpandedSteps] = useState({});

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    localStorage.setItem('flowinbox_agent_chat', JSON.stringify(messages));
    scrollToBottom();
  }, [messages, loading]);

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      const data = await agentsApi.listAgents();
      if (data && data.length > 0) {
        // Merge with defaults
        const merged = DEFAULT_AGENTS.map(def => {
          const matched = data.find(a => a.id === def.id || a.name?.toLowerCase().includes(def.name.toLowerCase()));
          return matched ? { ...def, ...matched } : def;
        });
        setAgents(merged);
        if (!selectedAgent) setSelectedAgent(merged[0]);
      }
    } catch (err) {
      console.warn('[AgentsPage] Using default agents:', err);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSend = async (queryText) => {
    const query = (queryText || input).trim();
    if (!query || loading) return;

    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
    setLoading(true);

    try {
      const res = await agentsApi.submitTask(user?.id || 'default', query);

      let replyContent = res.final_response;
      if (!replyContent) {
        if (res.approval_status === 'pending') {
          replyContent = `### Action Pending Approval\n\nI have generated an action request (**${res.intent || 'Consequential Email Action'}**) that requires your explicit review.\n\nPlease check the **Approvals** page to inspect and approve this action before execution.`;
        } else {
          replyContent = `Unable to generate a detailed response for intent '${res.intent || 'general_query'}'. Please try rephrasing your prompt.`;
        }
      }

      const botMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        agentName: selectedAgent.name,
        content: replyContent,
        intent: res.intent,
        plan: res.plan && res.plan.length > 0 ? res.plan : null,
        approvalStatus: res.approval_status,
        pendingActions: res.pending_actions || [],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (err) {
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        agentName: selectedAgent.name,
        content: `### Error Executing Task\n\nUnable to complete request: ${err.message || 'Server error'}.\n\nPlease ensure the backend container is running and try again.`,
        isError: true,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleTextareaInput = (e) => {
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`;
  };

  const handleClearChat = () => {
    setMessages([]);
    localStorage.removeItem('flowinbox_agent_chat');
  };

  const toggleSteps = (msgId) => {
    setExpandedSteps(prev => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  return (
    <div className="flex h-[calc(100vh-56px)] w-full overflow-hidden bg-[#FAF6F0] select-none">
      
      {/* LEFT SIDEBAR: Agent Switcher & Status */}
      <div className="w-80 border-r border-[#E6DFD5] bg-[#F7FAFD] flex flex-col justify-between shrink-0 hidden md:flex">
        <div className="p-4 flex flex-col gap-4 overflow-y-auto">
          
          <div className="flex items-center justify-between pb-3 border-b border-[#E6DFD5]">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-xl bg-[#3186D8] text-white flex items-center justify-center shadow-2xs">
                <Bot className="w-4 h-4" />
              </div>
              <div>
                <h2 className="text-xs font-extrabold text-[#172033]">Agent Studio</h2>
                <p className="text-[10px] text-[#536176]">Select workspace AI agent</p>
              </div>
            </div>

            <button
              onClick={handleClearChat}
              title="Clear chat history"
              className="p-1.5 rounded-lg text-[#536176] hover:bg-[#E6DFD5]/50 hover:text-[#172033] transition-colors"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>

          {/* Agent Selection Cards */}
          <div className="flex flex-col gap-2.5">
            {agents.map((ag) => {
              const isSelected = selectedAgent?.id === ag.id;
              return (
                <div
                  key={ag.id}
                  onClick={() => setSelectedAgent(ag)}
                  className={`p-3.5 rounded-2xl border transition-all cursor-pointer flex flex-col gap-2 ${
                    isSelected
                      ? 'bg-white border-[#3186D8] shadow-sm ring-1 ring-[#3186D8]/20'
                      : 'bg-[#F2E8DA]/40 border-[#E6DFD5] hover:bg-white/80 hover:border-[#3186D8]/40'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className={`w-6 h-6 rounded-lg flex items-center justify-center text-xs font-bold ${
                        isSelected ? 'bg-[#3186D8] text-white' : 'bg-[#E6DFD5] text-[#172033]'
                      }`}>
                        <Bot className="w-3.5 h-3.5" />
                      </div>
                      <span className="text-xs font-bold text-[#172033]">{ag.name}</span>
                    </div>

                    <span className="px-2 py-0.5 rounded-full bg-[#ECFDF5] text-[#48A97B] text-[9px] font-bold border border-[#A7F3D0]">
                      ● Active
                    </span>
                  </div>

                  <p className="text-[11px] text-[#536176] line-clamp-2 leading-relaxed">{ag.description}</p>

                  <div className="flex items-center gap-2 text-[10px] text-[#8995A7] pt-1 border-t border-[#E6DFD5]/50">
                    <ShieldCheck className="w-3 h-3 text-[#3186D8]" />
                    <span className="truncate">{ag.permissions}</span>
                  </div>
                </div>
              );
            })}
          </div>

        </div>

        {/* Footer Settings Card */}
        <div className="p-4 border-t border-[#E6DFD5] bg-white/60">
          <div className="p-3 bg-[#FAF6F0] border border-[#E6DFD5] rounded-xl flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-[#3186D8]" />
              <div>
                <div className="font-bold text-[#172033]">LLM Model</div>
                <div className="text-[10px] text-[#536176]">{selectedModel}</div>
              </div>
            </div>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="text-[10px] bg-white border border-[#E6DFD5] rounded-lg px-2 py-1 text-[#172033] font-semibold focus:outline-none"
            >
              <option value="Groq Llama 3 70B">Groq Llama 3</option>
              <option value="Gemini 1.5 Pro">Gemini 1.5 Pro</option>
            </select>
          </div>
        </div>
      </div>

      {/* RIGHT MAIN CHAT WINDOW (ChatGPT Layout) */}
      <div className="flex-1 flex flex-col h-full min-w-0 bg-[#FAF6F0]">
        
        {/* Chat Top Header */}
        <div className="h-14 px-6 border-b border-[#E6DFD5] bg-white/80 backdrop-blur-md flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-r from-[#3186D8] to-[#8C6BD9] text-white flex items-center justify-center shadow-2xs">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-sm font-bold text-[#172033]">{selectedAgent?.name || 'FlowInbox AI Agent'}</h1>
                <span className="px-2 py-0.5 bg-[#E7F1FC] text-[#3186D8] font-bold text-[10px] rounded-md border border-[#3186D8]/20">
                  {selectedModel}
                </span>
              </div>
              <p className="text-[11px] text-[#536176]">Conversational AI Assistant · Inbox & Vector Memory Connected</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleClearChat}
              className="px-3 py-1.5 rounded-xl border border-[#E6DFD5] bg-white text-xs font-semibold text-[#536176] hover:bg-[#FAF6F0] hover:text-[#172033] transition-colors flex items-center gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Reset Chat</span>
            </button>
          </div>
        </div>

        {/* Message History List */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
          {messages.length === 0 ? (
            /* EMPTY CHAT WELCOME SCREEN (ChatGPT style) */
            <div className="h-full max-w-2xl mx-auto flex flex-col items-center justify-center text-center gap-6 py-12 animate-fade-in">
              <div className="w-16 h-16 rounded-3xl bg-gradient-to-tr from-[#3186D8] via-[#8C6BD9] to-[#3186D8] text-white flex items-center justify-center shadow-lg animate-pulse">
                <Sparkles className="w-8 h-8" />
              </div>

              <div>
                <h2 className="text-2xl font-extrabold text-[#172033] tracking-tight mb-2">
                  What can FlowInbox AI do for you today?
                </h2>
                <p className="text-xs text-[#536176] max-w-md leading-relaxed">
                  Ask me to search your emails, summarize conversations, check pending approvals, or draft replies in your personalized tone.
                </p>
              </div>

              {/* Prompt Suggestions 2x2 Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full text-left mt-2">
                {selectedAgent?.suggestedPrompts?.map((item, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(item.query)}
                    className="p-4 bg-white border border-[#E6DFD5] hover:border-[#3186D8] rounded-2xl shadow-2xs hover:shadow-md transition-all group flex flex-col justify-between gap-3 text-left"
                  >
                    <div>
                      <div className="flex items-center justify-between text-xs font-bold text-[#172033] mb-1 group-hover:text-[#3186D8]">
                        <span>{item.title}</span>
                        <ArrowRight className="w-3.5 h-3.5 text-[#8995A7] group-hover:text-[#3186D8] transition-colors" />
                      </div>
                      <p className="text-[11px] text-[#536176] leading-relaxed line-clamp-2">
                        "{item.query}"
                      </p>
                    </div>
                    <span className="text-[10px] font-semibold text-[#3186D8] uppercase tracking-wider">
                      Run Prompt →
                    </span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            /* CONVERSATION MESSAGES LIST */
            <div className="max-w-3xl mx-auto space-y-6">
              {messages.map((msg) => {
                const isUser = msg.role === 'user';
                const showSteps = expandedSteps[msg.id];

                return (
                  <div
                    key={msg.id}
                    className={`flex gap-3.5 ${isUser ? 'flex-row-reverse' : 'flex-row'} animate-fade-in`}
                  >
                    {/* Avatar */}
                    <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 text-white font-bold text-xs shadow-2xs ${
                      isUser ? 'bg-[#172033]' : 'bg-gradient-to-r from-[#3186D8] to-[#8C6BD9]'
                    }`}>
                      {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                    </div>

                    {/* Bubble Content Container */}
                    <div className={`flex flex-col gap-1.5 max-w-[85%] ${isUser ? 'items-end' : 'items-start'}`}>
                      
                      {/* Name & Time Header */}
                      <div className="flex items-center gap-2 text-[10px] text-[#8995A7] px-1 font-semibold">
                        <span>{isUser ? (user?.full_name || 'You') : (msg.agentName || 'FlowInbox AI')}</span>
                        <span>·</span>
                        <span>{msg.timestamp}</span>
                      </div>

                      {/* Main Message Bubble */}
                      <div className={`p-4 rounded-2xl text-xs leading-relaxed border shadow-2xs ${
                        isUser
                          ? 'bg-[#3186D8] text-white border-[#2874BE] rounded-tr-xs'
                          : msg.isError
                          ? 'bg-[#FEF2F2] text-[#991B1B] border-[#FCA5A5] rounded-tl-xs'
                          : 'bg-white text-[#172033] border-[#E6DFD5] rounded-tl-xs'
                      }`}>
                        
                        {/* Collapsible Execution Steps (if assistant message has plan) */}
                        {!isUser && msg.plan && msg.plan.length > 0 && (
                          <div className="mb-3 pb-3 border-b border-[#E6DFD5]">
                            <button
                              onClick={() => toggleSteps(msg.id)}
                              className="flex items-center gap-1.5 text-[11px] font-bold text-[#3186D8] hover:underline"
                            >
                              <Layers className="w-3.5 h-3.5" />
                              <span>Reasoning & Execution Steps ({msg.plan.length})</span>
                              {showSteps ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                            </button>

                            {showSteps && (
                              <div className="mt-2 space-y-1.5 p-2.5 bg-[#FAF6F0] rounded-xl border border-[#E6DFD5] text-[11px] text-[#536176]">
                                {msg.plan.map((stepItem, sIdx) => (
                                  <div key={sIdx} className="flex items-center gap-2">
                                    <span className="w-4 h-4 rounded-full bg-[#E7F1FC] text-[#3186D8] font-bold text-[9px] flex items-center justify-center shrink-0">
                                      {sIdx + 1}
                                    </span>
                                    <span>{stepItem}</span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        )}

                        {/* Render Markdown or Plain Text */}
                        {isUser ? (
                          <div className="whitespace-pre-wrap font-medium">{msg.content}</div>
                        ) : (
                          <FormattedMarkdown content={msg.content} />
                        )}

                        {/* Pending Action Preview Box */}
                        {!isUser && msg.approvalStatus === 'pending' && (
                          <div className="mt-3 p-3 bg-[#FFFBEB] border border-[#FCD34D] rounded-xl flex items-center justify-between text-xs text-[#92400E]">
                            <div className="flex items-center gap-2">
                              <Zap className="w-4 h-4 text-[#D97706]" />
                              <div>
                                <div className="font-bold">Action Created & Pending Review</div>
                                <div className="text-[10px] text-[#B45309]">Check Approvals to confirm execution</div>
                              </div>
                            </div>
                            <a
                              href="/approvals"
                              className="px-3 py-1 bg-[#D97706] hover:bg-[#B45309] text-white text-[11px] font-bold rounded-lg transition-colors"
                            >
                              Review Action →
                            </a>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}

              {/* Loading Indicator */}
              {loading && (
                <div className="flex gap-3.5 items-start animate-fade-in">
                  <div className="w-8 h-8 rounded-xl bg-gradient-to-r from-[#3186D8] to-[#8C6BD9] text-white flex items-center justify-center shrink-0 shadow-2xs">
                    <Sparkles className="w-4 h-4 animate-spin" />
                  </div>
                  <div className="p-4 bg-white border border-[#E6DFD5] rounded-2xl rounded-tl-xs shadow-2xs flex items-center gap-3">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 rounded-full bg-[#3186D8] animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-2 h-2 rounded-full bg-[#3186D8] animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-2 h-2 rounded-full bg-[#3186D8] animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                    <span className="text-xs font-semibold text-[#536176]">FlowInbox AI is searching vector index & reasoning...</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* BOTTOM FLOATING INPUT DOCK (ChatGPT Style) */}
        <div className="p-4 md:p-6 bg-gradient-to-t from-[#FAF6F0] via-[#FAF6F0] to-transparent shrink-0">
          <div className="max-w-3xl mx-auto">
            
            {/* Input Container Box */}
            <div className="relative bg-white border border-[#E6DFD5] focus-within:border-[#3186D8] focus-within:ring-2 focus-within:ring-[#3186D8]/20 rounded-2xl shadow-lg transition-all p-3 flex flex-col gap-2">
              
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onInput={handleTextareaInput}
                onKeyDown={handleKeyDown}
                placeholder={`Ask ${selectedAgent?.name || 'FlowInbox AI'} to search emails, draft replies, or manage workspace...`}
                rows={1}
                className="w-full bg-transparent text-xs text-[#172033] placeholder-[#8995A7] focus:outline-none resize-none min-h-[40px] max-h-40 leading-relaxed font-medium"
              />

              <div className="flex items-center justify-between pt-2 border-t border-[#FAF6F0]">
                <div className="flex items-center gap-1.5 text-[10px] text-[#8995A7] font-semibold">
                  <span className="px-2 py-0.5 bg-[#FAF6F0] rounded-md border border-[#E6DFD5]">
                    Enter ↵ to send
                  </span>
                  <span>Shift + Enter for new line</span>
                </div>

                <button
                  onClick={() => handleSend()}
                  disabled={!input.trim() || loading}
                  className="h-8 px-4 bg-[#3186D8] hover:bg-[#2366A8] disabled:opacity-30 disabled:hover:bg-[#3186D8] text-white text-xs font-bold rounded-xl flex items-center justify-center gap-1.5 shadow-2xs transition-all"
                >
                  <span>Send</span>
                  <Send className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            <div className="text-[10px] text-center text-[#8995A7] mt-2">
              FlowInbox AI uses RAG vector context & Groq LLM. Review consequential email actions in Approvals.
            </div>

          </div>
        </div>

      </div>

    </div>
  );
}
