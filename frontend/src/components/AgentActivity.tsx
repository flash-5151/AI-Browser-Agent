import React from 'react';
import { Activity, CheckCircle, ArrowRight, CornerDownRight, Clock } from 'lucide-react';
import { ExecutionStep } from '../types';

interface AgentActivityProps {
  steps: ExecutionStep[];
  liveStep?: any;
}

export const AgentActivity: React.FC<AgentActivityProps> = ({ steps, liveStep }) => {
  return (
    <div className="bg-[#161b22] border border-[#30363d] rounded-2xl p-5 shadow-xl flex flex-col h-full space-y-4">
      <div className="flex items-center justify-between border-b border-[#30363d] pb-3">
        <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
          <Activity className="h-4 w-4 text-indigo-400" />
          Execution Timeline & Activity
        </h3>
        <span className="text-xs text-slate-400 font-mono">{steps.length} Steps</span>
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 pr-1 max-h-[450px]">
        {steps.length === 0 && !liveStep ? (
          <div className="flex flex-col items-center justify-center text-center py-12 text-slate-500">
            <Clock className="h-8 w-8 mb-2 opacity-50 text-slate-600" />
            <p className="text-sm">No activity recorded yet</p>
            <p className="text-xs">Timeline logs will appear in real time during execution</p>
          </div>
        ) : (
          steps.map((step) => (
            <div
              key={step.id || step.step_number}
              className="bg-[#0d1117] border border-[#30363d] rounded-xl p-3.5 space-y-2 text-xs transition-all hover:border-slate-700"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="h-5 w-5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/30 flex items-center justify-center font-mono font-bold text-[10px]">
                    {step.step_number}
                  </span>
                  <span className="font-semibold text-slate-200 uppercase font-mono px-2 py-0.5 rounded bg-slate-800 text-[11px]">
                    {step.action}
                  </span>
                </div>
                <span className="text-[10px] text-slate-500 font-mono">
                  {step.created_at ? new Date(step.created_at).toLocaleTimeString() : 'Just now'}
                </span>
              </div>

              {step.url && (
                <div className="text-[11px] text-slate-400 font-mono truncate">
                  <span className="text-slate-500">URL:</span> {step.url}
                </div>
              )}

              {step.action_input && step.action_input !== '{}' && (
                <div className="bg-[#161b22] p-2 rounded border border-[#30363d] font-mono text-[11px] text-indigo-300 overflow-x-auto">
                  <span className="text-slate-500">Input:</span> {step.action_input}
                </div>
              )}

              {step.result && (
                <div className="flex items-start space-x-1.5 text-emerald-400 font-mono text-[11px] bg-emerald-950/20 p-2 rounded border border-emerald-500/20">
                  <CornerDownRight className="h-3.5 w-3.5 shrink-0 mt-0.5 text-emerald-500" />
                  <span className="break-all">{step.result}</span>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
