export type AgentId = 'manager' | 'researcher' | 'planner' | 'developer' | 'reviewer';

export type AgentState = 'idle' | 'waiting' | 'working' | 'done' | 'error';

export interface AgentInfo {
  id: AgentId;
  name: string;
  role: string;
  state: AgentState;
  statusText: string;
  waitingOn: string[];
  brief: string;
  output: string;
  files: string[];
  verdict?: {
    approved: boolean;
    issues: string[];
    iteration: number;
  };
}

export interface Particle {
  id: string;
  from: AgentId;
  to: AgentId;
  label: string;
  progress: number;
  color?: string;
}

export interface RunEvent {
  type: string;
  ts: number;
  [key: string]: any;
}

export interface FileItem {
  path: string;
  bytes: number;
  content?: string;
}
