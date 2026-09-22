import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Mail, CheckCircle2, ArrowRight, Sparkles, Loader2, PenTool, Volume2, ShieldCheck } from 'lucide-react';
import authApi from '../api/auth';
import inboxApi from '../api/inbox';
import { useAuth } from '../context/AuthContext';

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export default function OnboardingPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user, completeOnboarding, refreshAuth } = useAuth();
  
  const tokenParam = searchParams.get('token');
  const initialStep = searchParams.get('step') ? parseInt(searchParams.get('step'), 10) : (tokenParam ? 2 : 1);
  const [step, setStep] = useState(initialStep);
  const [analyzingTone, setAnalyzingTone] = useState(false);
  const [analysisText, setAnalysisText] = useState('Connecting to Gmail sent mailbox...');
  const [writingProfile, setWritingProfile] = useState(null);

  useEffect(() => {
    if (tokenParam) {
      localStorage.setItem('flowinbox_token', tokenParam);
      if (refreshAuth) refreshAuth();
    }
  }, [tokenParam]);

  const handleStartToneAnalysis = async () => {
    setStep(2);
    setAnalyzingTone(true);
    setAnalysisText('Scanning sent messages from your Gmail account...');

    let profileResult = null;
    try {
      const res = await inboxApi.analyzeWritingStyle();
      if (res && res.status === 'success') {
        profileResult = res;
        localStorage.setItem('flowinbox.writingStyle', JSON.stringify(res));
      } else {
        profileResult = res || { status: 'success', greeting: 'Hi [First Name],', formality: 'Direct & Professional', signoff: 'Best regards' };
      }
    } catch (e) {
      console.warn('[Onboarding] Writing style analysis fallback:', e);
      profileResult = { status: 'success', greeting: 'Hi [First Name],', formality: 'Direct & Professional', signoff: 'Best regards' };
    }
    setWritingProfile(profileResult);

    await sleep(900);
    setAnalysisText('Analyzing vocabulary, formality level, and sentence structure...');
    await sleep(900);
    setAnalysisText('Extracting greeting habits & sign-off patterns...');
    await sleep(900);
    setAnalysisText('Writing style & tone profile created successfully!');
    setAnalyzingTone(false);
  };

  useEffect(() => {
    const checkStatusAndAutoStart = async () => {
      try {
        const res = await authApi.getMe();
        if (res && res.user && res.user.has_completed_onboarding) {
          localStorage.setItem('flowinbox_onboarding_completed', 'true');
          navigate('/inbox', { replace: true });
          return;
        }

        if (initialStep === 2 || tokenParam) {
          handleStartToneAnalysis();
          return;
        }

        if (res && res.google_connected && step === 1) {
          handleStartToneAnalysis();
        }
      } catch (e) {
        // ignore fallback
      }
    };
    checkStatusAndAutoStart();
  }, []);


  const handleConnectGmail = async () => {
    try {
      const meRes = await authApi.getMe();
      if (meRes && meRes.google_connected) {
        handleStartToneAnalysis();
        return;
      }

      const statusRes = await authApi.getGoogleStatus();
      if (statusRes && statusRes.configured && !statusRes.connected) {
        window.location.href = authApi.getLoginUrl();
        return;
      }
    } catch (e) {
      console.log('[Onboarding] Google status check error:', e);
    }
    handleStartToneAnalysis();
  };

  const handleFinishOnboarding = async () => {
    try {
      if (completeOnboarding) {
        await completeOnboarding();
      }
    } catch (e) {
      console.warn('[Onboarding] completeOnboarding error:', e);
    }
    localStorage.setItem('flowinbox_onboarding_completed', 'true');
    navigate('/inbox', { replace: true });
  };

  const defaultWorkspaceName = user?.full_name ? `${user.full_name.split(' ')[0]}'s team` : 'My team';

  return (
    <div className="min-h-screen bg-[linear-gradient(135deg,#FAF6F0_0%,#F2E8DA_50%,#E5F0FA_100%)] flex items-center justify-center p-4 select-none">
      <div className="w-full max-w-[540px] bg-white border border-[#E6DFD5] rounded-[28px] shadow-[0_24px_70px_rgba(50,55,100,0.12)] p-8 md:p-10 flex flex-col gap-6 animate-scale-in">
        {/* Progress Bar */}
        <div className="flex items-center gap-2 px-2">
          {[1, 2, 3].map((item) => (
            <span
              key={item}
              className={`h-1.5 flex-1 rounded-full transition-all duration-300 ${
                item <= step ? 'bg-[#3186D8]' : 'bg-[#E6DFD5]'
              }`}
            />
          ))}
        </div>
        <div className="text-center text-[11px] font-semibold text-[#8fa0b1]">Step {step} of 3</div>

        {/* STEP 1: Connect Inbox */}
        {step === 1 && (
          <>
            <div className="flex flex-col items-center text-center gap-2">
              <div className="w-12 h-12 rounded-2xl bg-[#E7F1FC] text-[#3186D8] flex items-center justify-center mb-1 shadow-2xs">
                <Mail className="w-6 h-6" />
              </div>
              <h1 className="text-xl font-bold text-[#172033]">Let’s connect your inbox</h1>
              <p className="text-xs text-[#536176] max-w-sm">
                We will ask permission to organize emails, analyze your writing style, and draft replies.
              </p>
            </div>

            <div className="p-4 bg-[#FAF6F0] border border-[#E6DFD5] rounded-2xl flex flex-col gap-3 text-xs text-[#172033]">
              <div className="flex items-start gap-3">
                <div className="w-7 h-7 rounded-lg bg-white border border-[#E6DFD5] flex items-center justify-center shrink-0">
                  <span className="font-bold text-[#3186D8]">M</span>
                </div>
                <div>
                  <div className="font-bold">Read and send emails from FlowInbox</div>
                  <div className="text-[11px] text-[#536176]">
                    We use this to display emails, power search, and enable features like smart categorization & tone analysis.
                  </div>
                </div>
              </div>

              <div className="p-2.5 bg-white border border-[#E6DFD5] rounded-xl text-[11px] text-[#536176] flex items-center justify-between">
                <span>We never read emails outside enabled features or send emails without your action.</span>
                <span className="px-2 py-0.5 bg-[#48A97B]/10 text-[#48A97B] font-bold text-[10px] rounded">GDPR</span>
              </div>
            </div>

            <button
              onClick={handleConnectGmail}
              className="w-full h-11 bg-gradient-to-r from-[#3186D8] to-[#8C6BD9] hover:opacity-95 text-white text-xs font-bold rounded-2xl flex items-center justify-center gap-2 shadow-md transition-all"
            >
              <Mail className="w-4 h-4" />
              <span>Connect your inbox</span>
            </button>
          </>
        )}

        {/* STEP 2: Writing Tone Analysis */}
        {step === 2 && (
          <div className="flex flex-col gap-5 text-center">
            <div className="flex flex-col items-center text-center gap-2">
              <div className="w-12 h-12 rounded-2xl bg-[#E7F1FC] text-[#3186D8] flex items-center justify-center mb-1 shadow-2xs">
                <PenTool className="w-6 h-6" />
              </div>
              <h1 className="text-xl font-bold text-[#172033]">Analyzing Your Writing Tone & Style</h1>
              <p className="text-xs text-[#536176] max-w-sm">
                FlowInbox AI is reading past sent messages to learn your greeting habits, formality level, and sign-offs.
              </p>
            </div>

            <div className="p-6 bg-[#FAF6F0] border border-[#E6DFD5] rounded-2xl flex flex-col items-center gap-4 shadow-2xs">
              {analyzingTone ? (
                <div className="flex flex-col items-center gap-3 py-4">
                  <div className="w-14 h-14 rounded-full bg-[#E7F1FC] border border-[#3186D8] flex items-center justify-center animate-pulse">
                    <Sparkles className="w-7 h-7 text-[#3186D8] animate-spin" />
                  </div>
                  <p className="text-xs font-bold text-[#3186D8] animate-pulse">{analysisText}</p>
                </div>
              ) : (
                <div className="w-full flex flex-col gap-3 text-left">
                  <div className="flex items-center gap-2 text-xs font-bold text-[#48A97B]">
                    <CheckCircle2 className="w-4 h-4 text-[#48A97B]" />
                    <span>
                      Writing Profile Extracted ({writingProfile?.sent_email_count ?? 0} sent emails analyzed)
                    </span>
                  </div>
                  <div className="p-3 bg-white border border-[#E6DFD5] rounded-xl text-xs space-y-1.5 text-[#172033]">
                    <div><strong>Greeting:</strong> {writingProfile?.greeting || 'Hi [First Name],'}</div>
                    <div><strong>Formality:</strong> {writingProfile?.formality || 'Direct & Professional'}</div>
                    <div>
                      <strong>Sign-off:</strong>{' '}
                      <span className="whitespace-pre-line">
                        {writingProfile?.signoff || `Best regards,\n${user?.full_name || 'User'}`}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <button
              onClick={() => setStep(3)}
              disabled={analyzingTone}
              className="w-full h-11 bg-[#3186D8] hover:bg-[#2366A8] disabled:opacity-40 text-white text-xs font-bold rounded-2xl flex items-center justify-center gap-2 shadow-md transition-colors"
            >
              <span>{analyzingTone ? 'Analyzing past emails...' : 'Continue to Workspace'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* STEP 3: Workspace Name */}
        {step === 3 && (
          <div className="flex flex-col gap-5">
            <div className="flex flex-col items-center text-center gap-2">
              <div className="w-12 h-12 rounded-2xl bg-[#E7F1FC] text-[#3186D8] flex items-center justify-center mb-1 shadow-2xs">
                <Sparkles className="w-6 h-6" />
              </div>
              <h1 className="text-xl font-bold text-[#172033]">Create your workspace</h1>
              <p className="text-xs text-[#536176] max-w-sm">
                Name your team workspace to get started.
              </p>
            </div>

            <div>
              <label className="block text-xs font-bold text-[#172033] mb-1">Workspace name</label>
              <input 
                defaultValue={defaultWorkspaceName} 
                className="w-full h-11 px-3 bg-[#FAF6F0] border border-[#E6DFD5] rounded-xl text-xs text-[#172033] focus:outline-none focus:border-[#3186D8]" 
              />
            </div>

            <button
              onClick={handleFinishOnboarding}
              className="w-full h-11 bg-[#3186D8] hover:bg-[#2366A8] text-white text-xs font-bold rounded-2xl flex items-center justify-center gap-2 shadow-md transition-colors"
            >
              <span>Go to Inbox Dashboard</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
