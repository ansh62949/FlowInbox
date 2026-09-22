import React from 'react';
import { useNavigate } from 'react-router-dom';
import authApi from '../api/auth';

export default function LoginPage() {
  const navigate = useNavigate();

  const handleGoogleLogin = () => {
    window.location.href = authApi.getLoginUrl();
  };

  const handleDemoAccess = () => {
    navigate('/inbox');
  };

  return (
    <div className="relative min-h-screen w-screen flex items-center justify-center overflow-hidden select-none bg-[#EBF2FA]">
      {/* Blurred Application Background Simulation (Matching Screenshot 5) */}
      <div className="absolute inset-0 filter blur-md opacity-40 pointer-events-none scale-105 flex">
        <div className="w-12 bg-[#E4EEF8]" />
        <div className="w-56 bg-[#EDF4FB]" />
        <div className="flex-1 bg-white p-6 space-y-4">
          <div className="h-10 bg-[#F4F8FC] rounded-xl w-3/4" />
          <div className="h-14 bg-[#E7F1FC] rounded-xl" />
          <div className="h-14 bg-white rounded-xl" />
          <div className="h-14 bg-white rounded-xl" />
        </div>
      </div>

      <div className="absolute inset-0 bg-black/10 backdrop-blur-xs" />

      {/* Centered Modal Card (Matching Screenshot 5) */}
      <div className="relative z-10 w-full max-w-3xl bg-white rounded-3xl shadow-modal overflow-hidden flex flex-col md:flex-row animate-scale-in border border-[#DCE5EF]">
        {/* Left Side Auth Form */}
        <div className="flex-1 p-8 md:p-10 flex flex-col justify-between items-center text-center">
          <div className="w-full flex flex-col items-center">
            {/* FlowInbox Mark */}
            <div className="flex items-center gap-2 mb-8 cursor-pointer" onClick={() => navigate('/')}>
              <div className="w-7 h-7 rounded-lg bg-[#172033] text-white flex items-center justify-center font-extrabold text-xs shadow-2xs">
                F
              </div>
              <span className="font-extrabold text-base tracking-tight text-[#172033]">flowinbox</span>
            </div>

            <h1 className="text-2xl font-extrabold text-[#172033] mb-2 tracking-tight">
              Emails that sound like you
            </h1>

            <p className="text-xs text-[#536176] max-w-xs mb-8 leading-relaxed">
              Write faster, stay focused, and enjoy your emails again
            </p>

            <button
              onClick={handleGoogleLogin}
              className="w-full max-w-xs h-11 bg-[#3186D8] hover:bg-[#2366A8] text-white font-bold text-xs rounded-2xl flex items-center justify-center gap-2 shadow-2xs transition-colors mb-3"
            >
              <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
                <path d="M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z"/>
              </svg>
              <span>Continue with Google</span>
            </button>

            <button
              onClick={handleDemoAccess}
              className="text-xs text-[#536176] hover:text-[#3186D8] font-semibold underline transition-colors"
            >
              Enter Demo Workspace
            </button>
          </div>

          <div className="text-[11px] text-[#8995A7] mt-8">
            By continuing, you agree to our <a href="#" className="underline hover:text-[#536176]">Privacy Policy</a>
          </div>
        </div>

        {/* Right Side Testimonial Card (Matching Screenshot 5) */}
        <div className="w-full md:w-[320px] bg-[#F2F6FA] p-8 flex flex-col items-center justify-center border-t md:border-t-0 md:border-l border-[#DCE5EF]">
          <div className="p-5 bg-white rounded-2xl shadow-card flex flex-col gap-4">
            <p className="text-xs text-[#172033] leading-relaxed">
              "I used to dread my inbox. With FlowInbox everything is already sorted and half the replies are drafted. I actually <span className="text-[#3186D8] font-bold">enjoy doing email</span> now – didn't think I'd ever say that."
            </p>

            <div className="flex items-center gap-3 pt-1">
              <div className="w-8 h-8 rounded-full bg-[#3186D8] text-white font-bold text-xs flex items-center justify-center shadow-2xs">
                JW
              </div>
              <div>
                <div className="text-xs font-bold text-[#172033]">Jo Widawski</div>
                <div className="text-[10px] text-[#536176]">Founder & CEO, Maze</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
