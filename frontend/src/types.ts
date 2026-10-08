export interface ExecutionStep {
  id: string;
  execution_id: string;
  step_number: number;
  action: string;
  action_input?: string;
  result?: string;
  url?: string;
  screenshot_b64?: string;
  created_at: string;
}

export interface Execution {
  id: string;
  task_id: string;
  status: 'running' | 'completed' | 'failed' | 'cancelled';
  started_at: string;
  completed_at?: string;
  steps: ExecutionStep[];
}

export interface Task {
  id: string;
  user_task: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  final_result?: string;
  created_at: string;
  updated_at: string;
  executions?: Execution[];
}

export interface WSMessage {
  type: 'status_update' | 'page_observation' | 'action_decided' | 'step_completed' | 'task_completed' | 'task_failed' | 'task_cancelled';
  status?: string;
  step_number?: number;
  url?: string;
  title?: string;
  screenshot_b64?: string;
  thought?: string;
  action?: string;
  args?: Record<string, any>;
  result?: string;
  final_result?: string;
  message?: string;
  error?: string;
}
