import React from 'react';
import { History, Clock, ChevronRight, CheckCircle2, XCircle, AlertCircle, StopCircle } from 'lucide-react';
import { Task } from '../types';

interface TaskHistoryProps {
  tasks: Task[];
  activeTaskId?: string;
  onSelectTask: (task: Task) => void;
}

export const TaskHistory: React.FC<TaskHistoryProps> = ({
  tasks,
  activeTaskId,
  onSelectTask
}) => {
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />;
      case 'running':
        return <span className="h-2 w-2 rounded-full bg-blue-400 animate-ping" />;
      case 'cancelled':
        return <StopCircle className="h-3.5 w-3.5 text-amber-400" />;
      case 'failed':
        return <XCircle className="h-3.5 w-3.5 text-rose-400" />;
      default:
        return <Clock className="h-3.5 w-3.5 text-slate-400" />;
    }
  };

  return (
    <div className="bg-[#161b22] border border-[#30363d] rounded-2xl p-5 shadow-xl flex flex-col h-full space-y-4">
      <div className="flex items-center justify-between border-b border-[#30363d] pb-3">
        <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
          <History className="h-4 w-4 text-purple-400" />
          Task History
        </h3>
        <span className="text-xs text-slate-400 font-mono">{tasks.length} Tasks</span>
      </div>

      <div className="flex-1 overflow-y-auto space-y-2 pr-1 max-h-[500px]">
        {tasks.length === 0 ? (
          <div className="text-center py-10 text-slate-500 text-xs">
            No previous tasks found.
          </div>
        ) : (
          tasks.map((t) => {
            const isSelected = t.id === activeTaskId;
            return (
              <button
                key={t.id}
                onClick={() => onSelectTask(t)}
                className={`w-full text-left p-3 rounded-xl border transition-all flex items-center justify-between group ${
                  isSelected
                    ? 'bg-blue-950/30 border-blue-500/50 shadow-md'
                    : 'bg-[#0d1117] border-[#30363d] hover:border-slate-700'
                }`}
              >
                <div className="space-y-1 overflow-hidden pr-2">
                  <div className="flex items-center space-x-2">
                    {getStatusBadge(t.status)}
                    <span className="text-xs font-semibold text-slate-200 truncate capitalize">
                      {t.status}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 font-medium line-clamp-2 leading-relaxed">
                    {t.user_task}
                  </p>
                  <p className="text-[10px] text-slate-500 font-mono">
                    {new Date(t.created_at).toLocaleString()}
                  </p>
                </div>

                <ChevronRight className={`h-4 w-4 shrink-0 transition-transform group-hover:translate-x-0.5 ${
                  isSelected ? 'text-blue-400' : 'text-slate-600'
                }`} />
              </button>
            );
          })
        )}
      </div>
    </div>
  );
};
