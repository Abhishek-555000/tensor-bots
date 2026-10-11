import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FolderOpen, RotateCcw, CheckCircle, File } from 'lucide-react';
import { useRunStore } from '../store/useRunStore';

export const FinishCard: React.FC = () => {
  const { runId, runState, summary, files, resetRun } = useRunStore();

  if (runState !== 'completed') return null;

  const handleOpenFolder = () => {
    if ((window as any).electronAPI && runId) {
      (window as any).electronAPI.openFolder(`workspace/${runId}`);
    } else {
      alert(`Files saved in workspace/${runId}`);
    }
  };

  return (
    <AnimatePresence>
      <div className="fixed bottom-6 left-1/2 -translate-x-1/2 w-full max-w-xl px-4 z-40 pointer-events-auto">
        <motion.div
          initial={{ opacity: 0, y: 30, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 20, scale: 0.95 }}
          transition={{ type: 'spring', damping: 24, stiffness: 280 }}
          className="rounded-2xl bg-surface/95 border border-primary/30 p-5 shadow-2xl backdrop-blur-xl space-y-4"
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-border-subtle/50 pb-3">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-400" />
              <span className="text-sm font-semibold tracking-wide text-text">
                Done · {files.length} file{files.length !== 1 ? 's' : ''}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleOpenFolder}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-surface-elevated hover:bg-surface-elevated/80 border border-border-subtle text-xs font-mono text-primary-light transition-colors"
              >
                <FolderOpen className="w-3.5 h-3.5" />
                <span>Open folder</span>
              </button>
              <button
                onClick={resetRun}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-primary-deep hover:bg-primary-deep/90 text-white text-xs font-semibold transition-colors shadow-sm"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>New run</span>
              </button>
            </div>
          </div>

          {/* Manager's Summary */}
          {summary && (
            <p className="text-xs text-text-muted font-sans leading-relaxed whitespace-pre-line">
              {summary}
            </p>
          )}

          {/* Compact Deliverables List */}
          {files.length > 0 && (
            <div className="flex flex-wrap gap-2 pt-1">
              {files.map((f) => (
                <div
                  key={f.path}
                  className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-surface-elevated/50 border border-border-subtle/40 text-[11px] font-mono text-text-muted"
                >
                  <File className="w-3 h-3 text-primary-light/70" />
                  <span>{f.path}</span>
                </div>
              ))}
            </div>
          )}
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
