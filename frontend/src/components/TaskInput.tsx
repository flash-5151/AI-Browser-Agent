import React from 'react';
import { Play, Square, Sparkles, Compass, Search } from 'lucide-react';

interface TaskInputProps {
  taskInput: string;
  setTaskInput: (val: string) => void;
  onRunTask: () => void;
  onCancelTask: () => void;
  isRunning: boolean;
}

export const TaskInput: React.FC<TaskInputProps> = ({
  taskInput,
  setTaskInput,
  onRunTask,
  onCancelTask,
  isRunning
}) => {
  const presets = [
    {
      title: "Test 1: Example.com Title",
      icon: Compass,
      query: "Open https://example.com and tell me the page title."
    },
    {
      title: "Test 2: Search FastAPI Tutorials",
      icon: Search,
      query: "Search the internet for 3 FastAPI tutorials and give me their titles and links."
    }
  ];

  return (
    <div className="bg-[#161b22] border border-[#30363d] rounded-2xl p-5 shadow-xl space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-blue-400" />
          Agent Task Input
        </h2>
        <span className="text-xs text-slate-400">Describe what you want the browser agent to do</span>
      </div>

      <div className="relative">
        <textarea
          value={taskInput}
          onChange={(e) => setTaskInput(e.target.value)}
          disabled={isRunning}
          placeholder="Search Google for top news about Python or Open example.com"
          className="w-full bg-[#0d1117] border border-[#30363d] rounded-xl p-4 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all resize-none min-h-[90px] disabled:opacity-60 font-sans"
        />
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
        {/* Presets */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">Quick Presets:</span>
          {presets.map((preset, idx) => {
            const Icon = preset.icon;
            return (
              <button
                key={idx}
                onClick={() => setTaskInput(preset.query)}
                disabled={isRunning}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#0d1117] hover:bg-[#21262d] border border-[#30363d] text-xs text-slate-300 transition-colors disabled:opacity-50"
              >
                <Icon className="h-3.5 w-3.5 text-blue-400" />
                <span>{preset.title}</span>
              </button>
            );
          })}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-3">
          {isRunning ? (
            <button
              onClick={onCancelTask}
              className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-medium text-sm shadow-lg shadow-rose-600/20 transition-all active:scale-95"
            >
              <Square className="h-4 w-4 fill-white" />
              <span>Stop Task</span>
            </button>
          ) : (
            <button
              onClick={onRunTask}
              disabled={!taskInput.trim()}
              className="flex items-center space-x-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-medium text-sm shadow-lg shadow-blue-600/25 transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Play className="h-4 w-4 fill-white" />
              <span>Run Agent Task</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
