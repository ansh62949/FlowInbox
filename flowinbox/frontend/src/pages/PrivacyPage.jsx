import React from 'react';
import { useNavigate } from 'react-router-dom';

export default function PrivacyPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#FAF6F0] text-[#1E293B] font-sans py-12 px-6">
      <div className="max-w-3xl mx-auto bg-white rounded-2xl p-8 md:p-12 shadow-sm border border-[#E2E8F0]">
        <div className="flex items-center justify-between mb-8 pb-6 border-b border-[#E2E8F0]">
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/')}>
            <div className="w-8 h-8 rounded-lg bg-[#1E293B] text-white flex items-center justify-center font-bold text-sm">
              F
            </div>
            <span className="font-extrabold text-lg text-[#1E293B]">FlowInbox AI</span>
          </div>
          <button
            onClick={() => navigate('/')}
            className="text-xs font-medium text-[#64748B] hover:text-[#1E293B] transition-colors"
          >
            ← Back to Home
          </button>
        </div>

        <h1 className="text-3xl font-extrabold text-[#0F172A] mb-2 tracking-tight">Privacy Policy</h1>
        <p className="text-xs text-[#64748B] mb-8">Last updated: September 24, 2026</p>

        <div className="space-y-6 text-sm leading-relaxed text-[#334155]">
          <section>
            <h2 className="text-base font-bold text-[#0F172A] mb-2">1. Introduction</h2>
            <p>
              FlowInbox AI ("we", "our", or "us") is an AI-native email and workspace productivity assistant.
              This Privacy Policy explains how we collect, use, and protect your information when you connect your
              Google account and use our services at <strong>https://flow-inbox.vercel.app</strong>.
            </p>
          </section>

          <section>
            <h2 className="text-base font-bold text-[#0F172A] mb-2">2. Information We Collect</h2>
            <p className="mb-2">
              When you authorize FlowInbox AI via Google OAuth, we access only the data necessary to provide smart email features:
            </p>
            <ul className="list-disc pl-5 space-y-1 text-xs">
              <li><strong>Google Profile & Email Address:</strong> Used to authenticate your account.</li>
              <li><strong>Gmail Messages & Threads:</strong> Used to display inbox threads, generate AI summaries, search emails, and draft responses.</li>
              <li><strong>Google Calendar Events:</strong> Used to check availability and format interview preparation briefs.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-base font-bold text-[#0F172A] mb-2">3. Google User Data Policy & Limited Use</h2>
            <p>
              FlowInbox AI's use and transfer to any other app of information received from Google APIs will adhere to the{' '}
              <a
                href="https://developers.google.com/terms/api-services-user-data-policy"
                target="_blank"
                rel="noreferrer"
                className="text-[#2563EB] underline"
              >
                Google API Services User Data Policy
              </a>
              , including the Limited Use requirements.
            </p>
            <p className="mt-2 text-xs text-[#475569]">
              We do NOT sell, rent, or share your Google user data with third-party advertisers or data brokers.
              Your email content is processed strictly to execute actions requested by you.
            </p>
          </section>

          <section>
            <h2 className="text-base font-bold text-[#0F172A] mb-2">4. Data Security & Storage</h2>
            <p>
              All OAuth access tokens are encrypted using AES-256 Fernet encryption before being stored in our database.
              Communication between your browser, our API backend, and Google API servers uses mandatory HTTPS encryption.
            </p>
          </section>

          <section>
            <h2 className="text-base font-bold text-[#0F172A] mb-2">5. User Control & Data Deletion</h2>
            <p>
              You may revoke FlowInbox AI's access to your Google Account at any time via your{' '}
              <a
                href="https://myaccount.google.com/permissions"
                target="_blank"
                rel="noreferrer"
                className="text-[#2563EB] underline"
              >
                Google Account Security Settings
              </a>
              . You may also request complete deletion of your account and synced threads by contacting us.
            </p>
          </section>

          <section>
            <h2 className="text-base font-bold text-[#0F172A] mb-2">6. Contact Us</h2>
            <p>
              If you have any questions or concerns about this Privacy Policy, please contact the developer at{' '}
              <a href="mailto:pathakansh007@gmail.com" className="text-[#2563EB] underline font-medium">
                pathakansh007@gmail.com
              </a>
              .
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
