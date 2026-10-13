import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Square, Sparkles, Cpu } from 'lucide-react';
import { useRunStore } from '../store/useRunStore';

interface InputBarProps {
  onSubmit: (prompt: string) => void;
  onCancel?: () => void;
}

const EXAMPLE_CHIPS = [
  { label: 'Focus timer', prompt: 'A modern Pomodoro timer with ambient sounds' },
  { label: 'Attendance tracker', prompt: 'A sleek attendance manager with records table' },
  { label: 'Calculator', prompt: 'A cyberpunk calculator with sound & history' },
  { label: 'File organizer', prompt: 'A Python CLI tool that renames files by date' },
];

export const InputBar: React.FC<InputBarProps> = ({ onSubmit, onCancel }) => {
  const { prompt, setPrompt, runState, agents } = useRunStore();

  const isRunning = runState === 'running';

  // When run is completed, hide input bar to eliminate overlap with FinishCard
  if (runState === 'completed') {
    return null;
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !isRunning) {
      const val = prompt.trim();
      if (val) {
        setPrompt(val);
        onSubmit(val);
      }
    }
  };

  const handleSend = () => {
    const val = prompt.trim();
    if (val && !isRunning) {
      setPrompt(val);
      onSubmit(val);
    }
  };

  const handleChipClick = (examplePrompt: string) => {
    setPrompt(examplePrompt);
    onSubmit(examplePrompt);
  };

  // Determine active agent in pipeline
  const getActiveAgentLabel = () => {
    if (agents.reviewer.state === 'working') return 'Reviewer: Validating deliverables...';
    if (agents.developer.state === 'working') return 'Developer: Generating complete code...';
    if (agents.planner.state === 'working') return 'Planner: Designing architecture & UI...';
    if (agents.researcher.state === 'working') return 'Researcher: Analyzing patterns...';
    if (agents.manager.state === 'working') return 'Project Manager: Coordinating team...';
    return 'Agents collaborating on your build...';
  };

  return (
    <>
      <div className="fixed bottom-5 left-1/2 z-20 w-full max-w-3xl -translate-x-1/2 px-4 sm:bottom-7">
        <AnimatePresence>
          {!isRunning && runState === 'idle' && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 4 }}
              className="mb-3 flex flex-wrap items-center justify-center gap-2"
            >
              {EXAMPLE_CHIPS.map((example) => (
                <button
                  key={example.label}
                  onClick={() => handleChipClick(example.prompt)}
                  className="inline-flex items-center gap-2 rounded-full border border-white/[0.08] bg-surface/90 px-3 py-1.5 text-[11px] font-medium text-text-muted shadow-sm backdrop-blur-xl transition-colors hover:border-primary/40 hover:bg-surface-elevated hover:text-white"
                  title={`Build: ${example.prompt}`}
                >
                  <Sparkles className="h-3 w-3 text-primary-light/80" />
                  <span>{example.label}</span>
                </button>
              ))}
            </motion.div>
          )}

          {isRunning && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 4 }}
              className="mb-3 flex items-center justify-between gap-4 rounded-xl border border-primary/20 bg-surface/95 px-4 py-3 text-xs shadow-xl backdrop-blur-xl"
            >
              <div className="flex min-w-0 items-center gap-2.5 text-primary-light">
                <Cpu className="h-4 w-4 shrink-0 animate-pulse text-primary" />
                <span className="truncate font-medium">{getActiveAgentLabel()}</span>
              </div>
              <div className="hidden shrink-0 items-center gap-1.5 text-[10px] text-text-muted sm:flex">
                {[
                  ['PM', agents.manager.state],
                  ['Research', agents.researcher.state],
                  ['Plan', agents.planner.state],
                  ['Build', agents.developer.state],
                  ['Review', agents.reviewer.state],
                ].map(([label, state]) => (
                  <span
                    key={label}
                    className={`rounded-md px-1.5 py-1 ${
                      state === 'done'
                        ? 'bg-emerald-400/10 text-emerald-300'
                        : state === 'working'
                        ? 'bg-primary/15 text-primary-light'
                        : 'bg-white/[0.04] text-text-faint'
                    }`}
                  >
                    {label}
                  </span>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <div className="flex items-center gap-3 rounded-2xl border border-white/[0.1] bg-surface/95 px-4 py-3 shadow-[0_16px_50px_rgba(0,0,0,0.45)] backdrop-blur-2xl transition-colors focus-within:border-primary/50 sm:px-5">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isRunning}
            placeholder={
              isRunning
                ? 'Agents collaborating on your build...'
                : 'Describe an app or script for the agent team to build...'
            }
            className="min-w-0 flex-1 bg-transparent py-1 text-sm text-text placeholder:text-text-faint focus:outline-none disabled:opacity-50"
          />

          {isRunning ? (
            <button
              onClick={onCancel}
              className="inline-flex shrink-0 items-center gap-2 rounded-lg border border-red-400/20 bg-red-400/[0.08] px-3 py-2 text-xs font-medium text-red-300 transition-colors hover:bg-red-400/[0.15] hover:text-white"
              title="Cancel the current run"
              aria-label="Cancel current run"
            >
              <Square className="h-3.5 w-3.5 fill-current" />
              <span>Cancel</span>
            </button>
          ) : (
            <button
              onClick={handleSend}
              disabled={!prompt.trim()}
              className="inline-flex shrink-0 items-center gap-2 rounded-lg bg-primary px-4 py-2 text-xs font-semibold text-white transition-colors hover:bg-primary-light hover:text-background disabled:pointer-events-none disabled:opacity-40"
              title="Dispatch to Project Manager"
            >
              <span>Build</span>
              <Send className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
      </div>
    </>
  );
};
