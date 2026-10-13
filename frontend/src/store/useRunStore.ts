import { create } from 'zustand';
import { AgentId, AgentInfo, Particle, RunEvent, FileItem, RunnerTab } from '../types';

const INITIAL_AGENTS: Record<AgentId, AgentInfo> = {
  manager: {
    id: 'manager',
    name: 'Project Manager',
    role: 'Orchestrator',
    state: 'idle',
    statusText: 'Standing by',
    waitingOn: [],
    brief: '',
    output: '',
    files: [],
  },
  researcher: {
    id: 'researcher',
    name: 'Researcher',
    role: 'Constraints & Patterns',
    state: 'idle',
    statusText: 'Standing by',
    waitingOn: [],
    brief: '',
    output: '',
    files: [],
  },
  planner: {
    id: 'planner',
    name: 'Planner / Designer',
    role: 'Architecture & UI',
    state: 'idle',
    statusText: 'Standing by',
    waitingOn: [],
    brief: '',
    output: '',
    files: [],
  },
  developer: {
    id: 'developer',
    name: 'Developer',
    role: 'Implementation & Tools',
    state: 'idle',
    statusText: 'Standing by',
    waitingOn: [],
    brief: '',
    output: '',
    files: [],
  },
  reviewer: {
    id: 'reviewer',
    name: 'Reviewer',
    role: 'Validation & QA',
    state: 'idle',
    statusText: 'Standing by',
    waitingOn: [],
    brief: '',
    output: '',
    files: [],
  },
};

interface RunStore {
  runId: string | null;
  prompt: string;
  runState: 'idle' | 'running' | 'completed' | 'error';
  errorMessage: string | null;
  agents: Record<AgentId, AgentInfo>;
  particles: Particle[];
  activeAgentModal: AgentId | null;
  summary: string | null;
  files: FileItem[];
  selectedFile: FileItem | null;
  isMock: boolean;
  isReplay: boolean;
  backendHealthy: boolean;

  runnerModalOpen: boolean;
  runnerModalTab: RunnerTab;
  runnerModalFile: string | null;
  finishCardDismissed: boolean;

  setPrompt: (prompt: string) => void;
  setActiveAgentModal: (agentId: AgentId | null) => void;
  setSelectedFile: (file: FileItem | null) => void;
  setBackendHealthy: (healthy: boolean) => void;
  setIsMock: (isMock: boolean) => void;
  setIsReplay: (isReplay: boolean) => void;
  openRunnerModal: (tab?: RunnerTab, file?: string | null) => void;
  closeRunnerModal: () => void;
  dismissFinishCard: () => void;
  restoreFinishCard: () => void;
  resetRun: () => void;
  handleEvent: (event: RunEvent) => void;
  removeParticle: (particleId: string) => void;
}

export const useRunStore = create<RunStore>((set, get) => ({
  runId: null,
  prompt: '',
  runState: 'idle',
  errorMessage: null,
  agents: INITIAL_AGENTS,
  particles: [],
  activeAgentModal: null,
  summary: null,
  files: [],
  selectedFile: null,
  isMock: false,
  isReplay: false,
  backendHealthy: true,

  runnerModalOpen: false,
  runnerModalTab: 'preview',
  runnerModalFile: null,
  finishCardDismissed: false,

  setPrompt: (prompt) => set({ prompt }),
  setActiveAgentModal: (activeAgentModal) => set({ activeAgentModal }),
  setSelectedFile: (selectedFile) => set({ selectedFile }),
  setBackendHealthy: (backendHealthy) => set({ backendHealthy }),
  setIsMock: (isMock) => set({ isMock }),
  setIsReplay: (isReplay) => set({ isReplay }),

  openRunnerModal: (tab = 'preview', file = null) =>
    set({
      runnerModalOpen: true,
      runnerModalTab: tab,
      runnerModalFile: file,
    }),

  closeRunnerModal: () =>
    set({
      runnerModalOpen: false,
    }),

  dismissFinishCard: () => set({ finishCardDismissed: true }),
  restoreFinishCard: () => set({ finishCardDismissed: false }),

  resetRun: () =>
    set({
      runId: null,
      prompt: '',
      runState: 'idle',
      errorMessage: null,
      agents: JSON.parse(JSON.stringify(INITIAL_AGENTS)),
      particles: [],
      activeAgentModal: null,
      summary: null,
      files: [],
      selectedFile: null,
      runnerModalOpen: false,
      runnerModalTab: 'preview',
      runnerModalFile: null,
      finishCardDismissed: false,
    }),

  removeParticle: (id) =>
    set((state) => ({
      particles: state.particles.filter((p) => p.id !== id),
    })),

  handleEvent: (event: RunEvent) => {
    const etype = event.type;

    if (etype === 'run_started') {
      set({
        runId: event.run_id,
        prompt: event.prompt || get().prompt,
        runState: 'running',
        errorMessage: null,
        summary: null,
        files: [],
      });
      return;
    }

    if (etype === 'agent_started') {
      const agentId = (event.agent === 'manager_final' ? 'manager' : event.agent) as AgentId;
      if (get().agents[agentId]) {
        set((state) => ({
          agents: {
            ...state.agents,
            [agentId]: {
              ...state.agents[agentId],
              state: 'working',
              statusText: 'Working...',
            },
          },
        }));
      }
      return;
    }

    if (etype === 'agent_status') {
      const agentId = (event.agent === 'manager_final' ? 'manager' : event.agent) as AgentId;
      if (get().agents[agentId]) {
        set((state) => ({
          agents: {
            ...state.agents,
            [agentId]: {
              ...state.agents[agentId],
              statusText: event.text || state.agents[agentId].statusText,
            },
          },
        }));
      }
      return;
    }

    if (etype === 'agent_waiting') {
      const agentId = (event.agent === 'manager_final' ? 'manager' : event.agent) as AgentId;
      if (get().agents[agentId]) {
        set((state) => ({
          agents: {
            ...state.agents,
            [agentId]: {
              ...state.agents[agentId],
              state: 'waiting',
              waitingOn: event.on || [],
              statusText: `Waiting on ${((event.on || []) as string[]).join(', ')}`,
            },
          },
        }));
      }
      return;
    }

    if (etype === 'handoff') {
      const from = (event.from === 'manager_final' ? 'manager' : event.from) as AgentId;
      const to = (event.to === 'manager_final' ? 'manager' : event.to) as AgentId;
      const label = event.label || 'handoff';
      const particleColor = label.toLowerCase().includes('change') ? '#F472B6' : '#A78BFA';
      const newParticle: Particle = {
        id: `p_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
        from,
        to,
        label,
        progress: 0,
        color: particleColor,
      };

      set((state) => {
        // Limit max simultaneous particles to 4
        const updatedParticles = [...state.particles.slice(-3), newParticle];
        return { particles: updatedParticles };
      });
      return;
    }

    if (etype === 'agent_output') {
      const agentId = (event.agent === 'manager_final' ? 'manager' : event.agent) as AgentId;
      if (get().agents[agentId]) {
        set((state) => ({
          agents: {
            ...state.agents,
            [agentId]: {
              ...state.agents[agentId],
              output: event.text || '',
            },
          },
        }));
      }
      return;
    }

    if (etype === 'file_written') {
      const path = event.path;
      const bytes = event.bytes || 0;
      set((state) => {
        const existingIdx = state.files.findIndex((f) => f.path === path);
        const updatedFiles = [...state.files];
        if (existingIdx >= 0) {
          updatedFiles[existingIdx] = { path, bytes };
        } else {
          updatedFiles.push({ path, bytes });
        }
        return {
          files: updatedFiles,
          agents: {
            ...state.agents,
            developer: {
              ...state.agents.developer,
              files: updatedFiles.map((f) => f.path),
            },
          },
        };
      });
      return;
    }

    if (etype === 'review_verdict') {
      set((state) => ({
        agents: {
          ...state.agents,
          reviewer: {
            ...state.agents.reviewer,
            verdict: {
              approved: event.approved,
              issues: event.issues || [],
              iteration: event.iteration || 1,
            },
          },
        },
      }));
      return;
    }

    if (etype === 'agent_done') {
      const agentId = (event.agent === 'manager_final' ? 'manager' : event.agent) as AgentId;
      if (get().agents[agentId]) {
        set((state) => ({
          agents: {
            ...state.agents,
            [agentId]: {
              ...state.agents[agentId],
              state: 'done',
              statusText: event.summary || 'Completed task.',
            },
          },
        }));
      }
      return;
    }

    if (etype === 'run_finished') {
      set((state) => {
        // Mark all agents done upon run finished
        const finalAgents = { ...state.agents };
        Object.keys(finalAgents).forEach((k) => {
          const aId = k as AgentId;
          finalAgents[aId] = {
            ...finalAgents[aId],
            state: 'done',
          };
        });
        return {
          runState: 'completed',
          finishCardDismissed: false,
          summary: event.summary || 'Run completed successfully.',
          agents: finalAgents,
        };
      });
      return;
    }

    if (etype === 'run_error') {
      set({
        runState: 'error',
        errorMessage: event.message || 'An error occurred during execution.',
      });
      return;
    }
  },
}));
