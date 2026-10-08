import { Task, WSMessage } from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = {
  async getHealth(): Promise<{ status: string }> {
    const res = await fetch(`${API_URL}/api/health`);
    if (!res.ok) throw new Error('Health check failed');
    return res.json();
  },

  async createTask(user_task: string): Promise<Task> {
    const res = await fetch(`${API_URL}/api/tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_task }),
    });
    if (!res.ok) throw new Error('Failed to create task');
    return res.json();
  },

  async listTasks(): Promise<Task[]> {
    const res = await fetch(`${API_URL}/api/tasks`);
    if (!res.ok) throw new Error('Failed to list tasks');
    return res.json();
  },

  async getTask(taskId: string): Promise<Task> {
    const res = await fetch(`${API_URL}/api/tasks/${taskId}`);
    if (!res.ok) throw new Error('Failed to fetch task');
    return res.json();
  },

  async runTask(taskId: string): Promise<Task> {
    const res = await fetch(`${API_URL}/api/tasks/${taskId}/run`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to run task');
    return res.json();
  },

  async cancelTask(taskId: string): Promise<{ message: string }> {
    const res = await fetch(`${API_URL}/api/tasks/${taskId}/cancel`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to cancel task');
    return res.json();
  },

  connectWebSocket(taskId: string, onMessage: (msg: WSMessage) => void): WebSocket {
    const wsUrl = API_URL.replace(/^http/, 'ws') + `/api/tasks/${taskId}/ws`;
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (err) {
        console.error('Error parsing WS message:', err);
      }
    };

    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
    };

    return ws;
  }
};
