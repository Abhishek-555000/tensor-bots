import React from 'react';
import { PlayCircle, ShieldCheck } from 'lucide-react';
import { useRunStore } from '../store/useRunStore';

interface HeaderProps {
  onTriggerReplay: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onTriggerReplay }) => {
  const { backendHealthy, isMock, isReplay, runState } = useRunStore();

  return (
    <header className="fixed top-0 left-0 right-0 h-11 flex items-center justify-between px-6 z-30 select-none bg-gradient-to-b from-[#07040F] via-[#07040F]/80 to-transparent">
      {/* Left: Window branding & Draggable region */}
      <div className="flex items-center gap-2.5">
        <div className="w-5 h-5 rounded-lg bg-primary-deep/40 border border-primary/30 flex items-center justify-center">
          <div className="w-2 h-2 rounded-full bg-primary-light" />
        </div>
        <span className="text-xs font-semibold tracking-wider text-text font-mono uppercase">
          Tensor Bots
        </span>
      </div>

      {/* Right: Controls & Health Status */}
      <div className="flex items-center gap-3">
        {/* Replay Mode Trigger */}
        <button
          onClick={onTriggerReplay}
          disabled={runState === 'running'}
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-surface-elevated/80 hover:bg-surface-elevated border border-border-subtle text-[11px] font-mono text-text-muted hover:text-primary-light transition-all disabled:opacity-30"
          title="Replay a previously recorded run offline"
        >
          <PlayCircle className="w-3.5 h-3.5" />
          <span>{isReplay ? 'Replaying...' : 'Demo Replay'}</span>
        </button>

        {/* Mock Mode Pill */}
        {isMock && (
          <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-purple-900/40 text-purple-300 border border-purple-700/40">
            mock
          </span>
        )}

        {/* Backend Health Dot */}
        <div className="flex items-center gap-1.5 pl-1" title={backendHealthy ? 'Backend Connected' : 'Backend Offline'}>
          <div
            className={`w-2 h-2 rounded-full transition-colors ${
              backendHealthy ? 'bg-emerald-400 shadow-[0_0_6px_#34D399]' : 'bg-red-400 shadow-[0_0_6px_#F87171]'
            }`}
          />
        </div>
      </div>
    </header>
  );
};
