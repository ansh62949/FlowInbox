import React, { useState, useEffect } from 'react';
import { RefreshCw } from 'lucide-react';
import agentsApi from '../api/agents';

import { useAuth } from '../context/AuthContext';

export default function AgentActivityPage() {
  const { user } = useAuth();
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadActivity();
  }, [user]);

  const loadActivity = async () => {
    setLoading(true);
    try {
      const data = await agentsApi.getAgentActivity(user?.id || 'default');
      setRuns(data || []);
    } catch (err) {
      console.error('Error loading agent activity:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto w-full flex flex-col gap-6 select-none bg-[#f8fbfe] min-h-full">
      <div className="flex items-center justify-between pb-4 border-b border-[#DCE5EF]">
        <div>
          <h1 className="text-xl font-bold text-[#172335]">Agent Activity</h1>
          <p className="text-xs text-[#64788c]">Technical runs, intent classification, tool calls, and audit history.</p>
        </div>

        <button
          onClick={loadActivity}
          className="h-8 px-3 bg-[#F4F8FC] hover:bg-[#EDF4FB] border border-[#DCE5EF] text-[#536176] text-xs font-semibold rounded-lg flex items-center gap-1.5 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Logs</span>
        </button>
      </div>

      <div className="bg-white border border-[#DCE5EF] rounded-2xl overflow-hidden shadow-2xs">
        <div className="px-5 py-3 border-b border-[#DCE5EF] bg-[#F7FAFD]">
          <span className="text-xs font-bold text-[#172033]">LangGraph Execution History</span>
        </div>

        <div className="divide-y divide-[#E9EFF5]">
          {loading ? (
            <div className="p-6 text-center text-xs text-[#536176]">Loading execution logs...</div>
          ) : runs.length === 0 ? (
            <div className="p-8 text-center text-xs text-[#536176]">No agent execution runs recorded yet.</div>
          ) : (
            runs.map((run) => (
              <div key={run.id} className="p-5 flex flex-col gap-2 hover:bg-[#F4F8FC] transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#ECFDF5] text-[#047857]">
                      {run.status || 'SUCCESS'}
                    </span>
                    <span className="text-xs font-bold text-[#172033]">Intent: {run.intent || 'General Task'}</span>
                  </div>
                  <span className="text-[11px] text-[#8995A7]">{new Date(run.created_at).toLocaleString()}</span>
                </div>
                <div className="text-xs text-[#172033]"><strong>Request:</strong> "{run.request_text}"</div>
                {run.final_response && (
                  <div className="p-3 bg-[#F7FAFD] border border-[#E9EFF5] rounded-xl text-xs text-[#536176] font-mono leading-relaxed mt-1">
                    {run.final_response}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
