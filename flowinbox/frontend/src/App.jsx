import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AppShell from './components/layout/AppShell';

import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import OnboardingPage from './pages/OnboardingPage';
import PrivacyPage from './pages/PrivacyPage';

import InboxPage from './pages/InboxPage';
import ThreadDetailPage from './pages/ThreadDetailPage';
import ChannelsPage from './pages/ChannelsPage';
import TeamPage from './pages/TeamPage';
import AgentsPage from './pages/AgentsPage';
import AgentActivityPage from './pages/AgentActivityPage';
import ApprovalsPage from './pages/ApprovalsPage';
import ForAgentsPage from './pages/ForAgentsPage';
import SettingsPage from './pages/SettingsPage';

import { AuthProvider, useAuth } from './context/AuthContext';

function RequireOnboarding({ children }) {
  const { user, loading } = useAuth();
  const localCompleted = localStorage.getItem('flowinbox_onboarding_completed') === 'true';

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#FAF6F0] text-xs font-semibold text-[#64748B]">
        Loading FlowInbox workspace...
      </div>
    );
  }

  if (user && !user.has_completed_onboarding && !localCompleted) {
    return <Navigate to="/onboarding" replace />;
  }

  return children;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
      <Routes>
        {/* Public Marketing & Authentication Routes */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/signin" element={<LoginPage />} />
        <Route path="/onboarding" element={<OnboardingPage />} />
        <Route path="/privacy" element={<PrivacyPage />} />

        {/* Workspace Application Routes wrapped in AppShell & RequireOnboarding */}
        <Route
          path="/inbox"
          element={
            <RequireOnboarding>
              <AppShell>
                <InboxPage />
              </AppShell>
            </RequireOnboarding>
          }
        />
        <Route
          path="/inbox/:category"
          element={
            <RequireOnboarding>
              <AppShell>
                <InboxPage />
              </AppShell>
            </RequireOnboarding>
          }
        />
        <Route
          path="/thread/:threadId"
          element={
            <RequireOnboarding>
              <AppShell>
                <ThreadDetailPage />
              </AppShell>
            </RequireOnboarding>
          }
        />
        <Route
          path="/channels"
          element={
            <RequireOnboarding>
              <AppShell>
                <ChannelsPage />
              </AppShell>
            </RequireOnboarding>
          }
        />
        <Route
          path="/channels/:channelId"
          element={
            <RequireOnboarding>
              <AppShell>
                <ChannelsPage />
              </AppShell>
            </RequireOnboarding>
          }
        />
        <Route
          path="/team"
          element={
            <RequireOnboarding>
              <AppShell>
                <TeamPage />
              </AppShell>
            </RequireOnboarding>
          }
        />
        <Route
          path="/agents"
          element={
            <RequireOnboarding>
              <AppShell>
                <AgentsPage />
              </AppShell>
            </RequireOnboarding>
          }
        />
        <Route
          path="/agent-activity"
          element={
            <RequireOnboarding>
              <AppShell>
                <AgentActivityPage />
              </AppShell>
            </RequireOnboarding>
          }
        />
        <Route
          path="/approvals"
          element={
            <RequireOnboarding>
              <AppShell>
                <ApprovalsPage />
              </AppShell>
            </RequireOnboarding>
          }
        />
        <Route path="/for-agents" element={<ForAgentsPage />} />
        <Route
          path="/settings"
          element={
            <RequireOnboarding>
              <AppShell>
                <SettingsPage />
              </AppShell>
            </RequireOnboarding>
          }
        />
        <Route
          path="/settings/:tab"
          element={
            <RequireOnboarding>
              <AppShell>
                <SettingsPage />
              </AppShell>
            </RequireOnboarding>
          }
        />

        {/* Catch-all Fallback */}
        <Route path="*" element={<Navigate to="/inbox" replace />} />
      </Routes>
    </BrowserRouter>
  </AuthProvider>
  );
}
