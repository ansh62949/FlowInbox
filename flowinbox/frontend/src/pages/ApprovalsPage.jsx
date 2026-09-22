import React, { useState, useEffect } from 'react';
import { ShieldCheck, CheckCircle2, XCircle, AlertTriangle, RefreshCw } from 'lucide-react';
import approvalsApi from '../api/approvals';

export default function ApprovalsPage() {
  const [approvals, setApprovals] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadApprovals();
  }, []);

  const loadApprovals = async () => {
    setLoading(true);
    try {
      const data = await approvalsApi.getPendingApprovals();
      setApprovals(data || []);
    } catch (err) {
      console.error('Error loading approvals:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (id) => {
    try {
      await approvalsApi.approve(id);
      alert('Action approved & dispatched to Gmail/Calendar tool execution!');
      loadApprovals();
    } catch (err) {
      alert('Approval error: ' + err.message);
    }
  };

  const handleReject = async (id) => {
    try {
      await approvalsApi.reject(id);
      alert('Action rejected.');
      loadApprovals();
    } catch (err) {
      alert('Rejection error: ' + err.message);
    }
  };

  return (
    <div className="p-6 max-w-5xl mx-auto w-full flex flex-col gap-6 select-none bg-[#f8fbfe] min-h-full">
      <div className="flex items-center justify-between pb-4 border-b border-[#DCE5EF]">
        <div>
          <h1 className="text-xl font-bold text-[#172335]">Approvals</h1>
          <p className="text-xs text-[#64788c]">Review consequential actions before they reach your inbox or calendar.</p>
        </div>

        <button
          onClick={loadApprovals}
          className="h-8 px-3 bg-[#F4F8FC] hover:bg-[#EDF4FB] border border-[#DCE5EF] text-[#536176] text-xs font-semibold rounded-lg flex items-center gap-1.5 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      <div className="flex flex-col gap-4">
        {loading ? (
          <div className="p-8 text-center text-xs text-[#536176]">Loading pending approvals...</div>
        ) : approvals.length === 0 ? (
          <div className="p-10 bg-[#F7FAFD] border border-[#E9EFF5] rounded-2xl text-center flex flex-col items-center justify-center">
            <div className="w-12 h-12 rounded-2xl bg-[#ECFDF5] text-[#48A97B] flex items-center justify-center mb-3">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-bold text-[#172033] mb-1">No Pending Approvals</h3>
            <p className="text-xs text-[#536176]">All agent tasks are clear or automatically approved based on workspace policy.</p>
          </div>
        ) : (
          approvals.map((appr) => (
            <div key={appr.id} className="p-5 bg-white border border-[#DCE5EF] rounded-2xl shadow-2xs flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded-full bg-[#FFFBEB] border border-[#FDE68A] text-[#B45309] text-[10px] font-bold uppercase flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3" />
                    Action: {appr.action_type}
                  </span>
                  <span className="text-xs font-bold text-[#172033]">Requested by FlowInbox Agent</span>
                </div>
                <span className="text-[11px] text-[#8995A7]">{new Date(appr.requested_at).toLocaleString()}</span>
              </div>

              <div className="p-3 bg-[#F7FAFD] border border-[#E9EFF5] rounded-xl text-xs text-[#172033] font-mono leading-relaxed">
                <pre className="whitespace-pre-wrap">{JSON.stringify(appr.payload, null, 2)}</pre>
              </div>

              <div className="flex items-center justify-end gap-3 pt-1">
                <button
                  onClick={() => handleReject(appr.id)}
                  className="px-4 h-8 bg-[#FDF2F2] hover:bg-[#FEE2E2] text-[#D95D5D] border border-[#FCA5A5] rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors"
                >
                  <XCircle className="w-3.5 h-3.5" />
                  <span>Reject</span>
                </button>

                <button
                  onClick={() => handleApprove(appr.id)}
                  className="px-4 h-8 bg-[#3186D8] hover:bg-[#2366A8] text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 shadow-2xs transition-colors"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Approve & Execute</span>
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
