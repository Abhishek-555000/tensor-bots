import React from 'react';
import { PlayCircle, Play, Sparkles, Wifi, WifiOff, Eye } from 'lucide-react';
import { useRunStore } from '../store/useRunStore';

interface HeaderProps {
  onTriggerReplay: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onTriggerReplay }) => {
  const {
    backendHealthy,
    isMock,
    isReplay,
    runState,
    runId,
    finishCardDismissed,
    openRunnerModal,
    restoreFinishCard,
  } = useRunStore();

  return (
    <header className="relative z-30 flex h-16 shrink-0 items-center justify-between border-b border-white/[0.06] bg-background/75 px-5 backdrop-blur-xl sm:px-8">
      <div className="flex min-w-0 items-center gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-primary-light/20 bg-primary/10 text-primary-light">
          <Sparkles className="h-4 w-4" />
        </div>
        <div className="min-w-0">
          <span className="block truncate text-sm font-semibold tracking-tight text-white">
            Tensor Bots
          </span>
          <span className="hidden text-[11px] text-text-muted sm:block">AI project studio</span>
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-2 sm:gap-3">
        {runState === 'completed' && finishCardDismissed && (
          <button
            onClick={restoreFinishCard}
            className="inline-flex items-center gap-2 rounded-lg border border-primary/25 bg-primary/10 px-3 py-2 text-xs font-medium text-primary-light transition-colors hover:bg-primary/15 hover:text-white"
            title="Show the completed project results"
          >
            <Eye className="h-3.5 w-3.5" />
            <span>Show results</span>
          </button>
        )}

        {runId && (
          <button
            onClick={() => openRunnerModal('preview')}
            className="inline-flex items-center gap-2 rounded-lg border border-emerald-400/20 bg-emerald-400/[0.08] px-3 py-2 text-xs font-medium text-emerald-300 transition-colors hover:bg-emerald-400/[0.14]"
            title="Open Interactive Project Runner"
          >
            <Play className="h-3.5 w-3.5 fill-current" />
            <span className="hidden sm:inline">Open preview</span>
          </button>
        )}

        <button
          onClick={onTriggerReplay}
          disabled={runState === 'running'}
          className="inline-flex items-center gap-2 rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-xs font-medium text-text-muted transition-colors hover:border-white/[0.14] hover:bg-white/[0.06] hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
          title="Run a sample project to see the team in action"
        >
          <PlayCircle className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">{isReplay ? 'Playing demo' : 'Try a demo'}</span>
        </button>

        {isMock && (
          <span className="hidden rounded-md border border-violet-400/20 bg-violet-400/[0.08] px-2 py-1 text-[10px] font-medium uppercase tracking-wider text-violet-200 sm:inline">
            Demo mode
          </span>
        )}

        <div
          className={`hidden items-center gap-2 border-l border-white/[0.08] pl-3 text-[11px] sm:flex ${
            backendHealthy ? 'text-emerald-300' : 'text-text-muted'
          }`}
          title={backendHealthy ? 'FastAPI Backend Online' : 'FastAPI Backend Offline'}
        >
          {backendHealthy ? <Wifi className="h-3.5 w-3.5" /> : <WifiOff className="h-3.5 w-3.5" />}
          <span>{backendHealthy ? 'Connected' : 'Offline'}</span>
        </div>
      </div>
    </header>
  );
};
