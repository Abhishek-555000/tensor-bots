import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { X, ChevronDown, ChevronUp, FileCode, CheckCircle, AlertTriangle } from 'lucide-react';
import { useRunStore } from '../store/useRunStore';
import { fetchFileContent } from '../services/api';
import { CodeViewer } from './CodeViewer';

export const DetailPanel: React.FC = () => {
  const { runId, activeAgentModal, setActiveAgentModal, agents, files } = useRunStore();
  const [briefExpanded, setBriefExpanded] = useState(false);
  const [activeCodeFile, setActiveCodeFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>('');

  const agent = activeAgentModal ? agents[activeAgentModal] : null;

  // Handle escape key to close
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (activeCodeFile) {
          setActiveCodeFile(null);
        } else {
          setActiveAgentModal(null);
        }
      }
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [activeCodeFile, setActiveAgentModal]);

  // Load file content when activeCodeFile changes
  useEffect(() => {
    if (activeCodeFile && runId) {
      fetchFileContent(runId, activeCodeFile).then((txt) => setFileContent(txt));
    }
  }, [activeCodeFile, runId]);

  if (!agent) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex justify-end">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={() => setActiveAgentModal(null)}
          className="absolute inset-0 bg-black/40 backdrop-blur-[2px]"
        />

        {/* Slide-Over Panel */}
        <motion.div
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', damping: 28, stiffness: 300 }}
          className="relative w-full max-w-[420px] h-full bg-[#120A24]/95 border-l border-border-subtle backdrop-blur-xl shadow-2xl flex flex-col z-10 text-text"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-5 border-b border-border-subtle/60">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-surface-elevated border border-border-subtle flex items-center justify-center text-primary-light font-bold text-sm">
                {agent.name.charAt(0)}
              </div>
              <div>
                <h3 className="text-sm font-semibold tracking-wide text-text">{agent.name}</h3>
                <p className="text-[11px] font-mono text-text-muted uppercase">{agent.role}</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span
                className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded-full ${
                  agent.state === 'working'
                    ? 'bg-primary-deep/30 text-primary-light border border-primary/30'
                    : agent.state === 'done'
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : agent.state === 'waiting'
                    ? 'bg-purple-900/40 text-purple-300 border border-purple-700/30'
                    : 'bg-white/5 text-text-muted border border-white/10'
                }`}
              >
                {agent.state}
              </span>
              <button
                onClick={() => setActiveAgentModal(null)}
                className="p-1 rounded-lg text-text-muted hover:text-white hover:bg-white/5 transition-colors"
                title="Close panel (Esc)"
                aria-label="Close agent details"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Panel Body */}
          <div className="flex-1 overflow-y-auto p-5 space-y-5 text-sm">
            {/* Status Pill */}
            <div className="p-3 rounded-xl bg-surface-elevated/60 border border-border-subtle/50 font-mono text-xs text-text-muted flex items-center gap-2">
              <div
                className={`w-2 h-2 rounded-full ${
                  agent.state === 'working'
                    ? 'bg-primary-light animate-pulse'
                    : agent.state === 'done'
                    ? 'bg-emerald-400'
                    : 'bg-text-faint'
                }`}
              />
              <span className="truncate">{agent.statusText || 'Standing by'}</span>
            </div>

            {/* Brief Section */}
            {agent.brief && (
              <div className="rounded-xl bg-surface-elevated/40 border border-border-subtle/40 p-3.5">
                <div
                  onClick={() => setBriefExpanded(!briefExpanded)}
                  className="flex items-center justify-between cursor-pointer text-xs font-semibold text-text-muted uppercase tracking-wider mb-1"
                >
                  <span>Assigned Brief</span>
                  {briefExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                </div>
                <p className={`text-xs text-text-muted font-sans leading-relaxed ${!briefExpanded ? 'line-clamp-3' : ''}`}>
                  {agent.brief}
                </p>
              </div>
            )}

            {/* Reviewer Verdict Section */}
            {agent.id === 'reviewer' && agent.verdict && (
              <div className="rounded-xl bg-surface-elevated/60 border border-border-subtle/50 p-4 space-y-2">
                <div className="flex items-center gap-2">
                  {agent.verdict.approved ? (
                    <CheckCircle className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 text-accent-pink" />
                  )}
                  <span className="text-xs font-semibold font-mono uppercase tracking-wider">
                    Round {agent.verdict.iteration} — {agent.verdict.approved ? 'Approved' : 'Changes Requested'}
                  </span>
                </div>
                {agent.verdict.issues && agent.verdict.issues.length > 0 && (
                  <ul className="mt-2 text-xs font-mono text-text-muted space-y-1 pl-4 list-disc">
                    {agent.verdict.issues.map((iss, idx) => (
                      <li key={idx}>{iss}</li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            {/* Files List (Developer & Reviewer) */}
            {(agent.id === 'developer' || agent.id === 'reviewer') && files.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2">
                  Workspace Artifacts ({files.length})
                </h4>
                <div className="space-y-1.5">
                  {files.map((file) => (
                    <button
                      key={file.path}
                      onClick={() => setActiveCodeFile(file.path)}
                      className="w-full text-left p-2.5 rounded-lg bg-surface-elevated/40 hover:bg-surface-elevated border border-border-subtle/40 hover:border-primary/40 transition-colors flex items-center justify-between text-xs font-mono"
                    >
                      <div className="flex items-center gap-2 text-text">
                        <FileCode className="w-3.5 h-3.5 text-primary-light" />
                        <span>{file.path}</span>
                      </div>
                      <span className="text-text-muted text-[11px]">{file.bytes} B</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Main Agent Markdown Output */}
            {agent.output && (
              <div>
                <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2">
                  Agent Result
                </h4>
                <div className="prose prose-invert prose-xs max-w-none text-text-muted font-sans leading-relaxed p-3.5 rounded-xl bg-surface-elevated/30 border border-border-subtle/40">
                  <ReactMarkdown>{agent.output}</ReactMarkdown>
                </div>
              </div>
            )}
          </div>
        </motion.div>

        {/* Monospace Syntax-Highlighted Code Viewer Modal */}
        {activeCodeFile && (
          <div className="fixed inset-0 z-60 flex items-center justify-center p-4 sm:p-6 bg-black/80 backdrop-blur-md">
            <div className="w-full max-w-4xl h-[82vh] rounded-2xl bg-[#090514] border border-primary/40 shadow-2xl flex flex-col overflow-hidden">
              <div className="flex items-center justify-between px-5 py-3 border-b border-border-subtle/60 bg-[#0E081F]">
                <div className="flex items-center gap-2 text-xs font-mono text-primary-light">
                  <FileCode className="w-4 h-4 text-emerald-400" />
                  <span className="font-bold">{activeCodeFile}</span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => {
                      const f = activeCodeFile;
                      setActiveCodeFile(null);
                      useRunStore.getState().openRunnerModal('code', f);
                    }}
                    className="px-2.5 py-1 rounded-lg bg-primary-deep/50 hover:bg-primary-deep text-white text-xs font-mono transition-colors"
                  >
                    Open in Workspace Runner
                  </button>
                  <button
                    onClick={() => setActiveCodeFile(null)}
                    className="p-1 rounded-lg text-text-muted hover:text-white hover:bg-white/10"
                    title="Close code preview (Esc)"
                    aria-label="Close code preview"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <div className="flex-1 overflow-hidden p-2 bg-[#07040F]">
                <CodeViewer
                  code={fileContent}
                  filePath={activeCodeFile}
                  className="h-full border-0"
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </AnimatePresence>
  );
};
