import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Check, Hash, Search, Sparkles, Users } from 'lucide-react';

const inboxRows = [
  ['Louis Lecat', 'Welcome to FlowInbox', 'Hey Ansh, welcome aboard. The first feature is ready...', '6:25 PM'],
  ['Subhash .', 'Action Required: Round 1 Submission', 'Please submit your assignment before the deadline...', '2:25 PM'],
  ['Jane Street', 'Interview schedule confirmation', 'Thanks for your interest. Could you do Tuesday at 2 PM?', 'Sep 4'],
  ['Microsoft', 'Thank you for your interest', 'We received your application and will be in touch.', 'Sep 1'],
];

function Logo() {
  return <div className="flex items-center gap-2"><span className="flex h-8 w-8 items-center justify-center rounded-xl bg-[#172335] text-sm font-bold text-white">F</span><span className="font-semibold tracking-[-0.03em]">FlowInbox</span></div>;
}

function ProductPreview() {
  return (
    <div className="relative mx-auto mt-14 w-full max-w-6xl overflow-hidden rounded-[28px] border border-white/80 bg-white/75 p-2 shadow-[0_24px_70px_rgba(42,71,105,0.18)] backdrop-blur-sm">
      <div className="flex h-9 items-center gap-2 rounded-t-[20px] border-b border-[#dbe5ef] bg-[#edf5fb] px-4 text-[11px] text-[#65778b]"><span className="h-2.5 w-2.5 rounded-full bg-[#efaa9f]" /><span className="h-2.5 w-2.5 rounded-full bg-[#f1d58e]" /><span className="h-2.5 w-2.5 rounded-full bg-[#a8d4bc]" /><span className="ml-3">app.flowinbox.ai/inbox</span></div>
      <div className="grid min-h-[390px] grid-cols-[190px_1fr] text-left md:grid-cols-[235px_1fr]">
        <aside className="border-r border-[#dbe5ef] bg-[#eaf3fb] p-4">
          <div className="mb-6 flex items-center gap-2 text-xs font-semibold"><span className="flex h-6 w-6 items-center justify-center rounded-lg bg-[#2d7ed0] text-white">A</span> Acme Corp</div>
          <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.18em] text-[#8092a5]">Inbox</div>
          {['Inbox', 'Needs Reply', 'Follow Ups', 'Starred'].map((item, index) => <div key={item} className={`mb-1 rounded-lg px-2.5 py-2 text-xs ${index === 0 ? 'bg-white font-semibold text-[#215e98] shadow-sm' : 'text-[#60758b]'}`}>{item}</div>)}
          <div className="mb-3 mt-6 text-[10px] font-bold uppercase tracking-[0.18em] text-[#8092a5]">Channels</div>
          {['general', 'customer-feedback', 'receipts'].map(item => <div key={item} className="flex items-center gap-2 px-2.5 py-2 text-xs text-[#60758b]"><Hash className="h-3.5 w-3.5" />{item}</div>)}
        </aside>
        <section className="bg-white">
          <div className="flex h-14 items-center justify-between border-b border-[#e5edf4] px-5"><div className="flex items-center gap-2 rounded-lg border border-[#d9e5ef] bg-[#f8fbfe] px-3 py-2 text-xs text-[#8ba0b2]"><Search className="h-3.5 w-3.5" /> Search emails...</div><span className="rounded-lg bg-[#172335] px-3 py-2 text-xs font-semibold text-white">Ask Agent <ArrowRight className="ml-1 inline h-3 w-3" /></span></div>
          <div className="flex gap-5 border-b border-[#e5edf4] px-5 pt-4 text-xs font-semibold text-[#75879a]"><span className="border-b-2 border-[#2d7ed0] pb-3 text-[#172335]">Primary</span><span>Needs Reply</span><span>Follow Ups</span><span className="hidden sm:inline">Promotions</span></div>
          <div>{inboxRows.map(([sender, subject, snippet, time], index) => <div key={sender} className={`grid grid-cols-[24px_minmax(105px,155px)_1fr_60px] items-center gap-3 border-b border-[#edf2f6] px-5 py-4 text-xs ${index === 0 ? 'bg-[#eef6fd]' : ''}`}><span className={`h-7 w-7 rounded-full text-center pt-1.5 text-[10px] font-bold text-white ${['bg-[#6c9ac2]', 'bg-[#b78aa8]', 'bg-[#7ca58b]', 'bg-[#d29d72]'][index]}`}>{sender[0]}</span><span className="truncate font-semibold text-[#26374a]">{sender}</span><span className="truncate"><b className="font-semibold text-[#26374a]">{subject}</b><span className="text-[#8b9aaa]"> &nbsp;{snippet}</span></span><span className="text-right text-[10px] text-[#91a0af]">{time}</span></div>)}</div>
        </section>
      </div>
    </div>
  );
}

export default function LandingPage() {
  const navigate = useNavigate();
  return <div className="min-h-screen overflow-hidden bg-[#fbfcfd] text-[#172335]">
    <header className="fixed left-1/2 top-5 z-30 flex w-[calc(100%-32px)] max-w-[970px] -translate-x-1/2 items-center justify-between rounded-full border border-white/70 bg-[#b9c9de]/85 px-5 py-3 text-sm shadow-[0_12px_28px_rgba(48,75,105,0.16)] backdrop-blur-md md:px-8"><Logo /><nav className="hidden items-center gap-8 font-medium text-white/90 md:flex"><a href="#product">Product</a><a href="#teams">For Teams</a><a href="#agents">For Agents</a></nav><div className="flex items-center gap-2"><button onClick={() => navigate('/signin')} className="px-3 py-2 font-medium text-white">Login</button><button onClick={() => navigate('/signin')} className="rounded-full bg-[#f39a00] px-5 py-2 font-semibold text-white shadow-sm transition-transform hover:scale-[1.03]">Get started</button></div></header>
    <main>
      <section id="product" className="relative min-h-[760px] bg-[radial-gradient(circle_at_50%_5%,#fff8ee_0%,transparent_34%),linear-gradient(180deg,#eef7ff_0%,#fbfcfd_68%)] px-5 pb-20 pt-44 text-center"><div className="mx-auto max-w-4xl"><p className="mb-5 text-xs font-semibold uppercase tracking-[0.24em] text-[#67809a]">A calmer way to work</p><h1 className="text-5xl font-semibold leading-[0.98] tracking-[-0.07em] sm:text-7xl md:text-8xl">Your inbox,<br /><span className="text-[#8293a5]">finally working for you.</span></h1><p className="mx-auto mt-7 max-w-xl text-base leading-7 text-[#64788c] md:text-lg">An AI-native inbox where people, teams, and agents get work done together.</p><div className="mt-8 flex justify-center gap-3"><button onClick={() => navigate('/signin')} className="rounded-full bg-[#172335] px-6 py-3 text-sm font-semibold text-white transition-transform hover:scale-[1.02]">Get started <ArrowRight className="ml-1 inline h-4 w-4" /></button><a href="#teams" className="rounded-full border border-[#d4e1ed] bg-white/70 px-6 py-3 text-sm font-semibold text-[#40566c]">See how it works</a></div></div><ProductPreview /></section>
      <section id="teams" className="bg-[#dcedf8] px-5 py-24"><div className="mx-auto grid max-w-6xl gap-12 md:grid-cols-2 md:items-center"><div><p className="mb-4 text-xs font-bold uppercase tracking-[0.2em] text-[#537b9e]">Email, organized</p><h2 className="max-w-lg text-4xl font-semibold leading-tight tracking-[-0.05em] md:text-6xl">The work is in your inbox. Now it has a home.</h2><p className="mt-6 max-w-md text-base leading-7 text-[#5d7489]">FlowInbox quietly sorts conversations, spots what needs a reply, and keeps your team in the loop without breaking the context.</p></div><div className="grid gap-3 sm:grid-cols-2">{[['AI-native inbox', Sparkles], ['Shared channels', Hash], ['Human approvals', Check], ['Team context', Users]].map(([label, Icon]) => <div key={label} className="rounded-2xl border border-white/70 bg-white/65 p-5 shadow-sm"><Icon className="mb-8 h-5 w-5 text-[#2d7ed0]" /><p className="text-sm font-semibold">{label}</p></div>)}</div></div></section>
      <section id="agents" className="bg-[#fff3e9] px-5 py-24 text-center"><p className="mb-4 text-xs font-bold uppercase tracking-[0.2em] text-[#b17d67]">Made for people and agents</p><h2 className="mx-auto max-w-3xl text-4xl font-semibold leading-tight tracking-[-0.05em] md:text-6xl">Let the routine move forward.<br /><span className="text-[#a98981]">Keep the important choices yours.</span></h2><p className="mx-auto mt-6 max-w-xl text-base leading-7 text-[#806d6b]">Drafts, follow-ups, receipts, and scheduling stay grounded in your conversations and behind clear approval gates.</p><button onClick={() => navigate('/signin')} className="mt-8 rounded-full bg-[#172335] px-7 py-3 text-sm font-semibold text-white">Bring your team to FlowInbox <ArrowRight className="ml-1 inline h-4 w-4" /></button></section>
    </main>
    <footer className="flex flex-col items-center justify-between gap-4 bg-white px-6 py-8 text-xs text-[#75879a] md:flex-row md:px-12"><Logo /><span>© {new Date().getFullYear()} FlowInbox. Built for focused work.</span></footer>
  </div>;
}
