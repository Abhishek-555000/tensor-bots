import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Send, Square, Sparkles } from 'lucide-react';
import { useRunStore } from '../store/useRunStore';

interface InputBarProps {
  onSubmit: (prompt: string) => void;
  onCancel?: () => void;
}

const EXAMPLE_CHIPS = [
  'A pomodoro timer web page',
  'A Python CLI that renames files by date',
  'A personal landing page with dark theme',
];

export const InputBar: React.FC<InputBarProps> = ({ onSubmit, onCancel }) => {
  const { prompt, setPrompt, runState } = useRunStore();
  const [localInput, setLocalInput] = useState('');

  const isRunning = runState === 'running';

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !isRunning) {
      const val = localInput.trim();
      if (val) {
        setPrompt(val);
        onSubmit(val);
      }
    }
  };

  const handleSend = () => {
    const val = localInput.trim();
    if (val && !isRunning) {
      setPrompt(val);
      onSubmit(val);
    }
  };

  const handleChipClick = (chip: string) => {
    setLocalInput(chip);
    setPrompt(chip);
    onSubmit(chip);
  };

  return (
    <>
      {/* Collapsed Prompt Pill at Top Center (when running or completed) */}
      {isRunning && (
        <motion.div
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          className="fixed top-12 left-1/2 -translate-x-1/2 px-4 py-1.5 rounded-full bg-surface-elevated/80 border border-border-subtle backdrop-blur-md text-xs font-mono text-text flex items-center gap-2.5 shadow-lg z-20"
        >
          <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
          <span className="text-text-muted font-normal">Active Prompt:</span>
          <span className="font-semibold text-text truncate max-w-sm">{prompt}</span>
        </motion.div>
      )}

      {/* Floating Bottom Input Bar */}
      <div className="fixed bottom-8 left-1/2 -translate-x-1/2 w-full max-w-xl px-4 z-20">
        {!isRunning && runState === 'idle' && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center justify-center gap-2 mb-3"
          >
            {EXAMPLE_CHIPS.map((chip) => (
              <button
                key={chip}
                onClick={() => handleChipClick(chip)}
                className="text-[11px] font-mono text-text-muted hover:text-primary-light bg-surface/70 hover:bg-surface-elevated border border-border-subtle/60 rounded-full px-3 py-1 transition-all flex items-center gap-1.5 backdrop-blur-sm"
              >
                <Sparkles className="w-3 h-3 text-primary-light/70" />
                <span>{chip}</span>
              </button>
            ))}
          </motion.div>
        )}

        <div className="relative flex items-center rounded-2xl bg-surface/90 border border-border-subtle hover:border-primary/40 focus-within:border-primary/70 transition-all duration-200 backdrop-blur-xl shadow-subtle-panel overflow-hidden px-4 py-2.5">
          <input
            type="text"
            value={localInput}
            onChange={(e) => setLocalInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isRunning}
            placeholder={isRunning ? 'Agents collaborating on your request...' : 'Ask the Project Manager to build something...'}
            className="flex-1 bg-transparent text-sm text-text placeholder:text-text-faint focus:outline-none disabled:opacity-50 font-sans"
          />

          {isRunning ? (
            <button
              onClick={onCancel}
              className="p-1.5 rounded-lg bg-surface-elevated hover:bg-red-500/20 text-text-muted hover:text-red-400 transition-colors ml-2"
              title="Stop execution"
            >
              <Square className="w-4 h-4 fill-current" />
            </button>
          ) : (
            <button
              onClick={handleSend}
              disabled={!localInput.trim()}
              className="p-1.5 rounded-lg bg-primary-deep/40 hover:bg-primary-deep text-primary-light hover:text-white transition-all disabled:opacity-30 disabled:hover:bg-primary-deep/40 ml-2"
              title="Dispatch to Project Manager"
            >
              <Send className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </>
  );
};
