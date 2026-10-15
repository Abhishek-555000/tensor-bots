import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FolderOpen,
  RotateCcw,
  CheckCircle,
  AlertTriangle,
  FileCode,
  Play,
  ExternalLink,
  Columns,
  Sparkles,
  ArrowRight,
  X,
} from 'lucide-react';
import { useRunStore } from '../store/useRunStore';
import { openWorkspaceFolder, launchProject, openInBrowser } from '../services/api';

export const FinishCard: React.FC = () => {
  const {
    runId,
    prompt,
    runState,
    summary,
    files,
    agents,
    resetRun,
    openRunnerModal,
    dismissFinishCard,
  } = useRunStore();
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  if (runState !== 'completed' || !runId) return null;

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const handleRunProject = async () => {
    openRunnerModal('preview');
    const launched = await launchProject(runId);
    if (launched) {
      showToast(`Project preview opened for workspace/${runId}`);
    } else {
      showToast('Could not open the project preview.');
    }
  };

  const handleOpenFolder = async () => {
    await openWorkspaceFolder(runId);
    showToast(`📂 Opened folder: workspace/${runId}`);
  };

  const handleOpenBrowser = async () => {
    await openInBrowser(runId);
  };

  const handleOpenSplit = () => {
    openRunnerModal('split');
  };

  const handleFileClick = (filePath: string) => {
    openRunnerModal('code', filePath);
  };

  const reviewerVerdict = agents.reviewer?.verdict;

  return (
    <AnimatePresence>
      <div className="fixed bottom-6 left-1/2 -translate-x-1/2 w-full max-w-3xl px-4 z-40 pointer-events-auto">
        {/* Floating Notification Toast */}
        {toastMessage && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="mb-2 px-3.5 py-1.5 rounded-xl bg-[#170E33] border border-emerald-500/40 text-emerald-300 text-xs font-mono shadow-2xl flex items-center justify-between mx-auto w-fit"
          >
            <span>{toastMessage}</span>
          </motion.div>
        )}

        <motion.div
          initial={{ opacity: 0, y: 30, scale: 0.96 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 20, scale: 0.96 }}
          transition={{ type: 'spring', damping: 24, stiffness: 280 }}
          className="rounded-2xl bg-[#120A24]/95 border border-primary/40 p-5 shadow-[0_20px_60px_rgba(0,0,0,0.85)] backdrop-blur-2xl space-y-4"
        >
          {/* Top Status Header */}
          <div className="flex items-center justify-between border-b border-border-subtle/50 pb-3.5 flex-wrap gap-2">
            <div className="flex items-center gap-2.5">
              <div
                className={`w-8 h-8 rounded-xl border flex items-center justify-center ${
                  reviewerVerdict?.approved
                    ? 'bg-emerald-500/10 border-emerald-500/30'
                    : 'bg-amber-500/10 border-amber-500/30'
                }`}
              >
                {reviewerVerdict?.approved ? (
                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-amber-300" />
                )}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold tracking-wide text-text">
                    {reviewerVerdict?.approved ? 'Project ready to run' : 'Review needs attention'}
                  </span>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-full border font-semibold ${
                      reviewerVerdict?.approved
                        ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                        : 'bg-amber-500/10 text-amber-200 border-amber-500/30'
                    }`}
                  >
                    {reviewerVerdict?.approved ? 'Approved by reviewer' : 'Not fully verified'}
                  </span>
                </div>
                <p className="text-[11px] font-mono text-text-muted mt-0.5">
                  {files.length} deliverable{files.length !== 1 ? 's' : ''} in workspace/{runId}
                </p>
                {prompt && (
                  <p className="mt-1 max-w-[min(70vw,560px)] truncate text-[11px] text-text-faint" title={prompt}>
                    Prompt: {prompt}
                  </p>
                )}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-2 flex-wrap">
              <button
                onClick={dismissFinishCard}
                className="inline-flex items-center gap-1.5 rounded-xl border border-border-subtle bg-surface-elevated/60 px-3 py-2 text-xs font-mono text-text-muted transition-colors hover:bg-surface-elevated hover:text-white"
                title="Dismiss results (press Escape)"
                aria-label="Dismiss project results"
              >
                <X className="h-3.5 w-3.5" />
                <span>Close</span>
              </button>

              {/* PRIMARY RUN BUTTON */}
              <button
                onClick={handleRunProject}
                id="run-project-button"
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-500 via-teal-400 to-emerald-400 hover:from-emerald-400 hover:to-teal-300 text-slate-950 font-bold text-xs shadow-[0_0_20px_rgba(16,185,129,0.45)] hover:shadow-[0_0_30px_rgba(16,185,129,0.7)] transition-all transform hover:-translate-y-0.5 active:translate-y-0 cursor-pointer"
                title="Execute & launch project now"
              >
                <Play className="w-3.5 h-3.5 fill-slate-950 text-slate-950" />
                <span>Run Project</span>
              </button>

              {/* In-App Code & Preview Split View */}
              <button
                onClick={handleOpenSplit}
                className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-primary-deep/50 hover:bg-primary-deep border border-primary/40 text-xs font-semibold text-primary-light hover:text-white transition-all shadow-sm"
                title="Inspect code and preview side-by-side"
              >
                <Columns className="w-3.5 h-3.5" />
                <span>Code & Preview</span>
              </button>

              {/* Open Folder in Explorer */}
              <button
                onClick={handleOpenFolder}
                className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-surface-elevated hover:bg-surface-elevated/80 border border-border-subtle text-xs font-mono text-text-muted hover:text-text transition-colors"
                title="Open project folder in Windows Explorer"
              >
                <FolderOpen className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Folder</span>
              </button>

              {/* External Browser */}
              <button
                onClick={handleOpenBrowser}
                className="p-2 rounded-xl bg-surface-elevated hover:bg-surface-elevated/80 border border-border-subtle text-xs font-mono text-text-muted hover:text-text transition-colors"
                title="Open in external browser window"
              >
                <ExternalLink className="w-3.5 h-3.5" />
              </button>

              {/* New Run Button */}
              <button
                onClick={resetRun}
                className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-surface-elevated/60 hover:bg-surface-elevated border border-border-subtle text-text-muted hover:text-white text-xs font-mono transition-colors shadow-sm ml-1"
                title="Start a new project run"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>New run</span>
              </button>
            </div>
          </div>

          {/* Manager's Summary */}
          {summary && (
            <p className="text-xs text-text-muted font-sans leading-relaxed whitespace-pre-line bg-[#0E061E] p-3 rounded-xl border border-border-subtle/30">
              {summary}
            </p>
          )}

          {/* Deliverables List (Clickable to open specific file in Code Explorer) */}
          {files.length > 0 && (
            <div className="space-y-2 pt-1">
              <div className="text-[10px] font-mono uppercase tracking-wider text-text-muted/80 flex items-center justify-between">
                <span>Deliverables (click to inspect code):</span>
                <span className="text-primary-light flex items-center gap-1">
                  <span>Interactive Editor</span>
                  <ArrowRight className="w-3 h-3" />
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {files.map((f) => (
                  <button
                    key={f.path}
                    onClick={() => handleFileClick(f.path)}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-surface-elevated/80 hover:bg-primary-deep/30 border border-border-subtle/60 hover:border-primary/60 text-xs font-mono text-text-muted hover:text-white transition-all cursor-pointer group shadow-sm"
                    title={`Click to view code of: ${f.path}`}
                  >
                    <FileCode className="w-3.5 h-3.5 text-primary-light group-hover:scale-110 transition-transform" />
                    <span className="font-medium text-text group-hover:text-primary-light">{f.path}</span>
                    <span className="text-[10px] text-text-faint bg-[#0A0517] px-1.5 py-0.5 rounded border border-border-subtle/30">
                      {f.bytes} B
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
