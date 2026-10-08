import React, { useState, useEffect, useRef } from 'react';
import { Header } from './components/Header';
import { TaskInput } from './components/TaskInput';
import { LiveBrowser } from './components/LiveBrowser';
import { AgentActivity } from './components/AgentActivity';
import { FinalResult } from './components/FinalResult';
import { TaskHistory } from './components/TaskHistory';
import { api } from './api/client';
import { Task, ExecutionStep, WSMessage } from './types';

export const App: React.FC = () => {
  const [apiOnline, setApiOnline] = useState<boolean>(false);
  const [taskInput, setTaskInput] = useState<string>('');
  const [tasks, setTasks] = useState<Task[]>([]);
  const [activeTask, setActiveTask] = useState<Task | null>(null);
  const [steps, setSteps] = useState<ExecutionStep[]>([]);
  
  // Live Browser Viewport state
  const [currentUrl, setCurrentUrl] = useState<string>('about:blank');
  const [currentTitle, setCurrentTitle] = useState<string>('Browser Idle');
  const [screenshotB64, setScreenshotB64] = useState<string>('');
  const [browserStatus, setBrowserStatus] = useState<string>('Idle');
  const [currentThought, setCurrentThought] = useState<string>('');
  const [currentAction, setCurrentAction] = useState<string>('');
  const [currentArgs, setCurrentArgs] = useState<Record<string, any>>({});
  const [stepNumber, setStepNumber] = useState<number>(0);

  const wsRef = useRef<WebSocket | null>(null);

  // Check health and load past tasks on mount
  useEffect(() => {
    checkHealth();
    loadTasks();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const checkHealth = async () => {
    try {
      await api.getHealth();
      setApiOnline(true);
    } catch {
      setApiOnline(false);
    }
  };

  const loadTasks = async () => {
    try {
      const list = await api.listTasks();
      setTasks(list);
    } catch (e) {
      console.error('Failed to load tasks:', e);
    }
  };

  // Close active WS on unmount or task switch
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const handleRunTask = async () => {
    if (!taskInput.trim()) return;

    try {
      // 1. Create task
      const newTask = await api.createTask(taskInput);
      setActiveTask(newTask);
      setSteps([]);
      setScreenshotB64('');
      setCurrentUrl('about:blank');
      setCurrentTitle('Starting Browser...');
      setBrowserStatus('Starting');
      setCurrentThought('Initializing browser session and agent planner...');
      setCurrentAction('navigate');
      setCurrentArgs({});
      setStepNumber(0);

      // 2. Connect WebSocket for live updates
      if (wsRef.current) wsRef.current.close();
      const ws = api.connectWebSocket(newTask.id, handleWSMessage);
      wsRef.current = ws;

      // 3. Trigger run endpoint
      await api.runTask(newTask.id);
      loadTasks();
    } catch (err) {
      console.error('Error starting task:', err);
      setBrowserStatus('Error');
    }
  };

  const handleCancelTask = async () => {
    if (!activeTask) return;
    try {
      await api.cancelTask(activeTask.id);
      setBrowserStatus('Cancelled');
      loadTasks();
    } catch (err) {
      console.error('Error cancelling task:', err);
    }
  };

  const handleWSMessage = (msg: WSMessage) => {
    console.log('WS Message received:', msg.type, msg);

    if (msg.step_number) setStepNumber(msg.step_number);
    if (msg.url) setCurrentUrl(msg.url);
    if (msg.title) setCurrentTitle(msg.title);
    if (msg.screenshot_b64) setScreenshotB64(msg.screenshot_b64);
    if (msg.thought) setCurrentThought(msg.thought);
    if (msg.action) setCurrentAction(msg.action);
    if (msg.args) setCurrentArgs(msg.args);

    switch (msg.type) {
      case 'status_update':
        setBrowserStatus(msg.status || 'Running');
        break;
      case 'page_observation':
        setBrowserStatus('AI Deciding Next Action');
        break;
      case 'action_decided':
        setBrowserStatus(`Executing Action: ${msg.action}`);
        break;
      case 'step_completed':
        setBrowserStatus(`Step ${msg.step_number} Complete`);
        setSteps((prev) => [
          ...prev,
          {
            id: `step-${msg.step_number}-${Date.now()}`,
            execution_id: activeTask?.id || '',
            step_number: msg.step_number!,
            action: msg.action || '',
            action_input: msg.args ? JSON.stringify(msg.args) : '',
            result: msg.result,
            url: msg.url,
            screenshot_b64: msg.screenshot_b64,
            created_at: new Date().toISOString()
          }
        ]);
        break;
      case 'task_completed':
        setBrowserStatus('Completed');
        setActiveTask((prev) => prev ? { ...prev, status: 'completed', final_result: msg.final_result } : null);
        loadTasks();
        break;
      case 'task_failed':
        setBrowserStatus('Failed');
        setActiveTask((prev) => prev ? { ...prev, status: 'failed' } : null);
        loadTasks();
        break;
      case 'task_cancelled':
        setBrowserStatus('Cancelled');
        setActiveTask((prev) => prev ? { ...prev, status: 'cancelled' } : null);
        loadTasks();
        break;
    }
  };

  const handleSelectTask = async (task: Task) => {
    setActiveTask(task);
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    try {
      const detail = await api.getTask(task.id);
      setActiveTask(detail);
      const latestExec = detail.executions && detail.executions.length > 0 ? detail.executions[0] : null;
      if (latestExec) {
        setSteps(latestExec.steps || []);
        const lastStep = latestExec.steps && latestExec.steps.length > 0 ? latestExec.steps[latestExec.steps.length - 1] : null;
        if (lastStep) {
          setCurrentUrl(lastStep.url || 'about:blank');
          if (lastStep.screenshot_b64) setScreenshotB64(lastStep.screenshot_b64);
        }
      } else {
        setSteps([]);
      }
      setBrowserStatus(detail.status);
    } catch (e) {
      console.error('Error fetching task details:', e);
    }
  };

  const isRunning = activeTask?.status === 'running' || browserStatus === 'Starting' || browserStatus.includes('Executing');

  return (
    <div className="min-h-screen bg-[#0d1117] flex flex-col font-sans">
      <Header apiOnline={apiOnline} />

      <main className="flex-1 p-6 max-w-[1600px] w-full mx-auto space-y-6">
        {/* Top Section: Task Input */}
        <TaskInput
          taskInput={taskInput}
          setTaskInput={setTaskInput}
          onRunTask={handleRunTask}
          onCancelTask={handleCancelTask}
          isRunning={isRunning}
        />

        {/* Final Result Banner (if task completed) */}
        {activeTask && (activeTask.final_result || activeTask.status === 'completed') && (
          <FinalResult finalResult={activeTask.final_result} status={activeTask.status} />
        )}

        {/* Main Grid Section */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Live Browser Panel */}
          <div className="lg:col-span-7 h-[680px]">
            <LiveBrowser
              currentUrl={currentUrl}
              currentTitle={currentTitle}
              screenshotB64={screenshotB64}
              browserStatus={browserStatus}
              currentThought={currentThought}
              currentAction={currentAction}
              currentArgs={currentArgs}
              stepNumber={stepNumber}
            />
          </div>

          {/* Right Column: Execution Timeline & Task History */}
          <div className="lg:col-span-5 grid grid-cols-1 gap-6 h-[680px]">
            <div className="h-[340px]">
              <AgentActivity steps={steps} />
            </div>

            <div className="h-[316px]">
              <TaskHistory
                tasks={tasks}
                activeTaskId={activeTask?.id}
                onSelectTask={handleSelectTask}
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;
