import React from 'react';
import { Bot, Globe, ShieldCheck, Activity } from 'lucide-react';

interface HeaderProps {
  apiOnline: boolean;
}

export const Header: React.FC<HeaderProps> = ({ apiOnline }) => {
  return (
    <header className="border-b border-[#30363d] bg-[#161b22] px-6 py-4 flex items-center justify-between sticky top-0 z-50">
      <div className="flex items-center space-x-3">
        <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-500 to-purple-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
          <Bot className="h-6 w-6 text-white" />
        </div>
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            AI Browser Agent
            <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono">
              v1.0 Real-Time
            </span>
          </h1>
          <p className="text-xs text-slate-400">Playwright + Chromium + Gemini Autonomous Agent</p>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-[#0d1117] border border-[#30363d] text-xs">
          <Globe className="h-4 w-4 text-slate-400" />
          <span className="text-slate-300 font-mono">Chromium Engine</span>
        </div>

        <div className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors ${
          apiOnline 
            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' 
            : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
        }`}>
          <span className={`h-2 w-2 rounded-full ${apiOnline ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
          <span>{apiOnline ? 'Backend Connected' : 'Backend Disconnected'}</span>
        </div>
      </div>
    </header>
  );
};
