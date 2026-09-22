import React, { useEffect, useState } from 'react';
import { Sparkles, X, Send, Bot, User, CheckCircle2, Loader2, CornerDownLeft } from 'lucide-react';
import agentsApi from '../../api/agents';

import { useAuth } from '../../context/AuthContext';
import FormattedMarkdown from './FormattedMarkdown';

export default function AIDrawer({ isOpen, onClose }) {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState('Groq Llama 3 70B');
  const [width, setWidth] = useState(() => Number(localStorage.getItem('flowinbox.aiDrawerWidth')) || 380);

  useEffect(() => {
    localStorage.setItem('flowinbox.aiDrawerWidth', String(width));
  }, [width]);

  const handleResizeStart = (event) => {
    event.preventDefault();
    const startX = event.clientX;
    const startWidth = width;
    const move = (moveEvent) => setWidth(Math.min(600, Math.max(320, startWidth + startX - moveEvent.clientX)));
    const stop = () => {
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerup', stop);
    };
    window.addEventListener('pointermove', move);
    window.addEventListener('pointerup', stop);
  };

  if (!isOpen) return null;

  const handleSend = async (textToSend) => {
    const query = textToSend || input;
    if (!query.trim() || loading) return;

    const userMsg = { role: 'user', content: query };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await agentsApi.submitTask(user?.id || 'default', query);
      
      let replyText = res.final_response;
      if (!replyText) {
        if (res.approval_status === 'pending') {
          replyText = `Agent action created and pending approval: ${res.intent || 'Consequential action'}. Please check Approvals.`;
        } else {
          replyText = `Task processed successfully. Intent: ${res.intent || 'Inquiry'}.`;
        }
      }

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: replyText,
          intent: res.intent,
          plan: res.plan,
        }
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Unable to process request: ' + err.message, isError: true }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const promptSuggestions = [
    "Summarize my unread messages",
    "What needs my attention today?",
    "Find emails with attachments from this week"
  ];

  return (
    <aside style={{ width }} className="fixed inset-y-0 right-0 bg-[#eaf3fb] border-l border-[#d7e3ee] shadow-2xl z-40 flex flex-col animate-drawer-slide">
      <button onPointerDown={handleResizeStart} aria-label="Resize AI assistant" className="absolute inset-y-0 left-0 z-10 w-1.5 cursor-ew-resize bg-transparent hover:bg-[#2d7ed0]/40 transition-colors" />
      {/* Header */}
      <div className="p-3.5 border-b border-[#DCE5EF] flex items-center justify-between bg-[#F7FAFD]">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-lg bg-[#3186D8] text-white flex items-center justify-center shadow-2xs">
            <Sparkles className="w-3.5 h-3.5" />
          </div>
          <div>
            <h2 className="text-xs font-bold text-[#172033]">FlowInbox AI Assistant</h2>
            <p className="text-[10px] text-[#536176]">Search, summarize, and navigate</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="text-[11px] bg-white border border-[#DCE5EF] rounded-md px-2 py-0.5 text-[#536176] focus:outline-none"
          >
            <option value="Groq Llama 3 70B">Groq Llama 3 70B</option>
            <option value="Gemini 1.5 Pro">Gemini 1.5 Pro</option>
          </select>

          <button
            onClick={onClose}
            className="p-1 text-[#536176] hover:text-[#172033] hover:bg-[#EDF4FB] rounded-md transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Body / Chat Stream */}
      <div className="flex-1 overflow-y-auto bg-[#eaf3fb] p-4 flex flex-col gap-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center my-auto text-center py-6">
            <div className="w-12 h-12 rounded-2xl bg-[#E7F1FC] text-[#3186D8] flex items-center justify-center mb-3 shadow-2xs">
              <Sparkles className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-bold text-[#172033] mb-1">How can I help?</h3>
            <p className="text-xs text-[#536176] max-w-xs mb-6">
              Search, summarize, and navigate your inbox with AI.
            </p>

            <div className="flex flex-col gap-2 w-full">
              {promptSuggestions.map((prompt, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(prompt)}
                  className="w-full text-left px-3 py-2 bg-[#F7FAFD] hover:bg-[#E7F1FC] border border-[#E9EFF5] hover:border-[#CCE5FB] rounded-xl text-xs text-[#172033] transition-colors flex items-center justify-between group"
                >
                  <span>{prompt}</span>
                  <CornerDownLeft className="w-3 h-3 text-[#8995A7] group-hover:text-[#3186D8]" />
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, index) => (
          <div key={index} className={`flex flex-col gap-1.5 ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
            <div className="flex items-center gap-1.5 text-[10px] text-[#8995A7]">
              {msg.role === 'user' ? (
                <><span>You</span><User className="w-3 h-3" /></>
              ) : (
                <><Bot className="w-3 h-3 text-[#3186D8]" /><span>FlowInbox Agent</span></>
              )}
            </div>

            <div 
              className={`p-3 rounded-2xl text-xs max-w-[92%] leading-relaxed ${
                msg.role === 'user' 
                  ? 'bg-[#3186D8] text-white rounded-tr-xs font-medium' 
                  : msg.isError 
                    ? 'bg-[#FDF2F2] border border-[#F87171] text-[#991B1B] rounded-tl-xs'
                    : 'bg-white border border-[#E9EFF5] text-[#172033] rounded-tl-xs shadow-2xs'
              }`}
            >
              {msg.role === 'user' ? (
                msg.content
              ) : (
                <FormattedMarkdown content={msg.content} />
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 p-3 bg-[#F4F8FC] border border-[#E9EFF5] rounded-xl text-xs font-semibold text-[#3186D8]">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Agent is retrieving context...</span>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-3 border-t border-[#DCE5EF] bg-white">
        <form 
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="relative flex items-center"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Find, search, or ask anything..."
            disabled={loading}
            className="w-full h-9 pl-3 pr-9 bg-[#F4F8FC] border border-[#DCE5EF] rounded-xl text-xs text-[#172033] placeholder-[#8995A7] focus:outline-none focus:border-[#3186D8]"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="absolute right-1.5 w-6 h-6 bg-[#3186D8] hover:bg-[#2366A8] disabled:opacity-40 text-white rounded-lg flex items-center justify-center transition-colors"
          >
            <Send className="w-3 h-3" />
          </button>
        </form>
      </div>
    </aside>
  );
}
