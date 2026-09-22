import React, { useState, useEffect } from 'react';
import { Users, UserPlus, Shield, Mail, AlertCircle } from 'lucide-react';
import workspacesApi from '../api/workspaces';
import { useAuth } from '../context/AuthContext';

export default function TeamPage() {
  const { user } = useAuth();
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('MEMBER');

  useEffect(() => {
    loadTeamData();
  }, [user]);

  const loadTeamData = async () => {
    setLoading(true);
    setErrorMessage('');
    try {
      const workspaceId = user?.id || 'default';
      const data = await workspacesApi.getMembers(workspaceId).catch(() => null);
      if (data && data.length) {
        setMembers(data);
      } else if (user) {
        setMembers([
          { id: user.id, email: user.email, full_name: user.full_name || 'You', role: 'OWNER', joined_at: new Date().toISOString() }
        ]);
      } else {
        setMembers([]);
      }
    } catch (err) {
      console.error('Error loading team members:', err);
      setErrorMessage('Couldn’t load team members. Please check connection and retry.');
    } finally {
      setLoading(false);
    }
  };

  const handleInvite = async (e) => {
    e.preventDefault();
    if (!inviteEmail.trim()) return;
    setErrorMessage('');
    try {
      const workspaceId = user?.id || 'default';
      const newM = await workspacesApi.inviteMember(workspaceId, inviteEmail.trim(), inviteRole);
      setMembers((prev) => [...prev, newM]);
      setInviteEmail('');
      setShowInviteModal(false);
    } catch (err) {
      setErrorMessage('Failed to send invite: ' + (err.message || 'Server error'));
    }
  };

  return (
    <div className="p-6 max-w-5xl mx-auto w-full flex flex-col gap-6 select-none bg-[#f8fbfe] min-h-full">
      <div className="flex items-center justify-between pb-4 border-b border-[#DCE5EF]">
        <div>
          <h1 className="text-xl font-bold text-[#172033]">Workspace Team & Members</h1>
          <p className="text-xs text-[#536176]">Manage teammates, roles, and shared inbox assignments.</p>
        </div>

        <button
          onClick={() => setShowInviteModal(true)}
          className="h-8 px-4 bg-[#172335] hover:bg-[#2d7ed0] text-white text-xs font-semibold rounded-lg flex items-center gap-1.5 shadow-2xs transition-colors"
        >
          <UserPlus className="w-3.5 h-3.5" />
          <span>Invite Teammate</span>
        </button>
      </div>

      <div className="bg-white border border-[#d7e3ee] rounded-2xl overflow-hidden shadow-sm">
        <div className="px-5 py-3.5 border-b border-[#DCE5EF] bg-[#F7FAFD]">
          <span className="text-xs font-bold text-[#172033]">Teammates ({members.length})</span>
        </div>

        <div className="divide-y divide-[#E9EFF5]">
          {members.map((m) => (
            <div key={m.id} className="p-4 flex items-center justify-between hover:bg-[#F4F8FC] transition-colors">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-[#3186D8] text-white font-bold text-xs flex items-center justify-center shadow-2xs">
                  {m.full_name ? m.full_name.charAt(0) : m.email.charAt(0).toUpperCase()}
                </div>
                <div>
                  <div className="text-xs font-bold text-[#172033]">{m.full_name || m.email}</div>
                  <div className="text-[11px] text-[#536176]">{m.email}</div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                  m.role === 'OWNER' ? 'bg-[#E7F1FC] text-[#3186D8]' : 'bg-[#F4F8FC] text-[#536176]'
                }`}>
                  {m.role}
                </span>
                <span className="text-[11px] text-[#8995A7]">
                  Joined {new Date(m.joined_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {showInviteModal && (
        <div className="fixed inset-0 bg-black/20 backdrop-blur-xs flex items-center justify-center z-50 animate-fade-in">
          <div className="bg-white rounded-2xl shadow-xl border border-[#DCE5EF] p-5 w-96 animate-scale-in">
            <h3 className="text-sm font-bold text-[#172033] mb-1">Invite Team Member</h3>
            <form onSubmit={handleInvite} className="flex flex-col gap-3 mt-3">
              <input
                type="email"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                placeholder="colleague@company.com"
                className="w-full h-8 px-3 bg-[#F7FAFD] border border-[#DCE5EF] rounded-xl text-xs"
                required
              />
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowInviteModal(false)}
                  className="px-3 h-8 text-xs font-medium text-[#536176]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 h-8 text-xs font-semibold bg-[#3186D8] text-white rounded-xl shadow-2xs"
                >
                  Send Invite
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
