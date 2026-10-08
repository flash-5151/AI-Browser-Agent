import React from 'react';
import { Eye, Lock, Globe, Loader2, Play, CheckCircle2, AlertTriangle, ArrowRight } from 'lucide-react';

interface LiveBrowserProps {
  currentUrl?: string;
  currentTitle?: string;
  screenshotB64?: string;
  browserStatus: string;
  currentThought?: string;
  currentAction?: string;
  currentArgs?: Record<string, any>;
  stepNumber: number;
}

export const LiveBrowser: React.FC<LiveBrowserProps> = ({
  currentUrl = 'about:blank',
  currentTitle = 'Ready',
  screenshotB64,
  browserStatus,
  currentThought,
  currentAction,
  currentArgs,
  stepNumber
}) => {
  return (
    <div className="bg-[#161b22] border border-[#30363d] rounded-2xl overflow-hidden shadow-2xl flex flex-col h-full">
      {/* Panel Header */}
      <div className="px-5 py-3 border-b border-[#30363d] bg-[#0d1117] flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Eye className="h-4 w-4 text-blue-400" />
          <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">Live Browser Viewport</h3>
        </div>

        <div className="flex items-center space-x-3">
          <div className="text-xs text-slate-400 font-mono">
            Step <span className="text-blue-400 font-bold">{stepNumber}</span> / 30
          </div>
          <div className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
            browserStatus === 'completed'
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
              : browserStatus === 'running' || browserStatus.includes('AI')
              ? 'bg-blue-500/10 text-blue-400 border-blue-500/30'
              : browserStatus === 'failed'
              ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
              : 'bg-slate-800 text-slate-400 border-slate-700'
          }`}>
            {(browserStatus === 'running' || browserStatus.includes('deciding')) && (
              <Loader2 className="h-3 w-3 animate-spin" />
            )}
            <span>{browserStatus}</span>
          </div>
        </div>
      </div>

      {/* Browser Navigation Address Bar */}
      <div className="px-4 py-2.5 bg-[#161b22] border-b border-[#30363d] flex items-center space-x-3">
        <div className="flex items-center space-x-1.5">
          <div className="h-3 w-3 rounded-full bg-rose-500/80" />
          <div className="h-3 w-3 rounded-full bg-amber-500/80" />
          <div className="h-3 w-3 rounded-full bg-emerald-500/80" />
        </div>

        <div className="flex-1 bg-[#0d1117] border border-[#30363d] rounded-lg px-3 py-1.5 flex items-center space-x-2 text-xs font-mono text-slate-300 overflow-hidden">
          <Lock className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
          <span className="truncate text-slate-300">{currentUrl}</span>
        </div>

        <div className="text-xs text-slate-400 font-medium truncate max-w-[200px]" title={currentTitle}>
          {currentTitle}
        </div>
      </div>

      {/* Live AI Decision Banner */}
      {(currentAction || currentThought) && (
        <div className="bg-blue-950/40 border-b border-blue-500/20 px-4 py-3 flex items-start space-x-3 text-xs">
          <div className="p-1 rounded-md bg-blue-500/20 text-blue-400 mt-0.5">
            <ArrowRight className="h-3.5 w-3.5" />
          </div>
          <div className="flex-1 space-y-1">
            <div className="font-semibold text-blue-300 flex items-center gap-2">
              <span>Current AI Decision:</span>
              <span className="font-mono px-2 py-0.5 rounded bg-blue-500/20 text-blue-200 border border-blue-500/30 uppercase text-[10px]">
                {currentAction}
              </span>
            </div>
            {currentThought && (
              <p className="text-slate-300 italic">{currentThought}</p>
            )}
            {currentArgs && Object.keys(currentArgs).length > 0 && (
              <pre className="text-[11px] font-mono text-slate-400 bg-[#0d1117] p-1.5 rounded border border-[#30363d] overflow-x-auto">
                {JSON.stringify(currentArgs)}
              </pre>
            )}
          </div>
        </div>
      )}

      {/* Viewport Frame */}
      <div className="relative flex-1 bg-[#090d13] min-h-[380px] flex items-center justify-center p-2 overflow-hidden">
        {screenshotB64 ? (
          <img
            src={`data:image/jpeg;base64,${screenshotB64}`}
            alt="Live Playwright Chromium Viewport"
            className="w-full h-full object-contain rounded-lg border border-[#30363d] shadow-inner max-h-[500px]"
          />
        ) : (
          <div className="flex flex-col items-center justify-center text-center p-8 space-y-3">
            <div className="h-16 w-16 rounded-full bg-[#161b22] border border-[#30363d] flex items-center justify-center text-slate-500">
              <Globe className="h-8 w-8 text-slate-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-300">Browser Viewport Standby</p>
              <p className="text-xs text-slate-500">Run a task to see real-time Playwright Chromium interactions</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
