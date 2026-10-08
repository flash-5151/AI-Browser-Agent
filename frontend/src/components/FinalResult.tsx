import React, { useState } from 'react';
import { Award, Copy, Check, Sparkles } from 'lucide-react';

interface FinalResultProps {
  finalResult?: string;
  status?: string;
}

export const FinalResult: React.FC<FinalResultProps> = ({ finalResult, status }) => {
  const [copied, setCopied] = useState(false);

  if (!finalResult && status !== 'completed') return null;

  const handleCopy = () => {
    if (finalResult) {
      navigator.clipboard.writeText(finalResult);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="bg-[#161b22] border border-emerald-500/30 rounded-2xl p-5 shadow-2xl space-y-3 relative overflow-hidden bg-gradient-to-br from-[#161b22] via-[#161b22] to-emerald-950/20">
      <div className="flex items-center justify-between border-b border-[#30363d] pb-3">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <Award className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Final Task Answer / Result</h3>
            <p className="text-xs text-emerald-400 font-medium">Task Completed Successfully</p>
          </div>
        </div>

        {finalResult && (
          <button
            onClick={handleCopy}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#0d1117] hover:bg-[#21262d] border border-[#30363d] text-xs text-slate-300 transition-colors"
          >
            {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5 text-slate-400" />}
            <span>{copied ? 'Copied!' : 'Copy Result'}</span>
          </button>
        )}
      </div>

      <div className="bg-[#0d1117] border border-[#30363d] rounded-xl p-4 text-sm text-slate-200 whitespace-pre-wrap font-sans leading-relaxed shadow-inner">
        {finalResult || 'Task finished without explicit text response.'}
      </div>
    </div>
  );
};
