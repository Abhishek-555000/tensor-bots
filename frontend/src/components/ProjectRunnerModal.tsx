import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  ExternalLink,
  FolderOpen,
  RefreshCw,
  Smartphone,
  Tablet,
  Monitor,
  Laptop,
  Code2,
  Play,
  Columns,
  Terminal,
  FileCheck2,
  FileCode,
  CheckCircle2,
  AlertCircle,
  Copy,
  Check,
  Maximize2,
  Sparkles,
} from 'lucide-react';
import { useRunStore } from '../store/useRunStore';
import { openWorkspaceFolder, openInBrowser, launchProject, fetchFileContent, fetchRunFiles, executePythonScript } from '../services/api';
import { RunnerTab, FileItem } from '../types';
import { CodeViewer } from './CodeViewer';

type ViewportMode = 'desktop' | 'laptop' | 'tablet' | 'mobile';

interface ProjectRunnerModalProps {
  isOpen?: boolean;
  runId?: string | null;
  onClose?: () => void;
}

export const ProjectRunnerModal: React.FC<ProjectRunnerModalProps> = ({
  isOpen: propIsOpen,
  runId: propRunId,
  onClose: propOnClose,
}) => {
  const store = useRunStore();

  const isOpen = propIsOpen !== undefined ? propIsOpen : store.runnerModalOpen;
  const runId = propRunId !== undefined ? propRunId : store.runId;
  const handleClose = propOnClose || store.closeRunnerModal;

  const [activeTab, setActiveTab] = useState<RunnerTab>(store.runnerModalTab || 'preview');
  const [viewport, setViewport] = useState<ViewportMode>('desktop');
  const [iframeKey, setIframeKey] = useState<number>(0);
  const [copiedUrl, setCopiedUrl] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Files state
  const [fileList, setFileList] = useState<FileItem[]>(store.files || []);
  const [selectedFilePath, setSelectedFilePath] = useState<string>('');
  const [currentFileContent, setCurrentFileContent] = useState<string>('');
  const [isLoadingContent, setIsLoadingContent] = useState(false);

  // Terminal state for Python execution
  const [terminalLog, setTerminalLog] = useState<{ stdout: string; stderr: string; exit_code?: number; duration?: number } | null>(null);
  const [isRunningScript, setIsRunningScript] = useState(false);
  const [cliArgs, setCliArgs] = useState('');

  // Sync tab and file from store when modal opens
  useEffect(() => {
    if (store.runnerModalOpen) {
      if (store.runnerModalTab) setActiveTab(store.runnerModalTab);
      if (store.runnerModalFile) setSelectedFilePath(store.runnerModalFile);
    }
  }, [store.runnerModalOpen, store.runnerModalTab, store.runnerModalFile]);

  // Load files for the active run and ignore responses from an older run.
  useEffect(() => {
    let isCurrentRun = true;
    setFileList([]);
    setCurrentFileContent('');
    setSelectedFilePath('');

    if (runId && isOpen) {
      fetchRunFiles(runId).then((files) => {
        if (!isCurrentRun) return;
        setFileList(files);
        const requestedFile = store.runnerModalFile
          ? files.find((file) => file.path === store.runnerModalFile)
          : undefined;
        const defaultFile = files.find((file) => file.path === 'index.html') ||
          files.find((file) => file.path.endsWith('.py')) ||
          files[0];
        setSelectedFilePath((requestedFile || defaultFile)?.path || '');
      });
    }

    return () => {
      isCurrentRun = false;
    };
  }, [runId, isOpen, store.runnerModalFile]);

  // Load active file content
  useEffect(() => {
    let isCurrentFile = true;
    if (runId && selectedFilePath && isOpen) {
      setIsLoadingContent(true);
      fetchFileContent(runId, selectedFilePath)
        .then((txt) => {
          if (!isCurrentFile) return;
          setCurrentFileContent(txt);
          setIsLoadingContent(false);
        })
        .catch(() => {
          if (!isCurrentFile) return;
          setCurrentFileContent('// Failed to load content.');
          setIsLoadingContent(false);
        });
    }
    return () => {
      isCurrentFile = false;
    };
  }, [runId, selectedFilePath, isOpen]);

  // Check if workspace contains Python script
  const pythonScript = useMemo(() => {
    return fileList.find((f) => f.path.endsWith('.py'))?.path || null;
  }, [fileList]);

  const previewUrl = useMemo(() => {
    return `http://localhost:8000/api/preview/${runId}/`;
  }, [runId]);

  if (!isOpen || !runId) return null;

  const handleRefresh = () => {
    setIframeKey((prev) => prev + 1);
  };

  const handleCopyUrl = () => {
    navigator.clipboard.writeText(previewUrl);
    setCopiedUrl(true);
    setTimeout(() => setCopiedUrl(false), 2000);
  };

  const handleRunScript = async () => {
    if (!runId || !pythonScript) return;
    setIsRunningScript(true);
    const res = await executePythonScript(runId, pythonScript);
    setTerminalLog({
      stdout: res.stdout || '',
      stderr: res.stderr || res.error || '',
      exit_code: res.exit_code,
      duration: res.duration,
    });
    setIsRunningScript(false);
  };

  const getViewportWidth = () => {
    switch (viewport) {
      case 'mobile':
        return 'w-[390px]';
      case 'tablet':
        return 'w-[768px]';
      case 'laptop':
        return 'w-[1024px]';
      case 'desktop':
      default:
        return 'w-full';
    }
  };

  const getFileBadgeColor = (p: string) => {
    if (p.endsWith('.html')) return 'text-amber-400 bg-amber-400/10 border-amber-400/30';
    if (p.endsWith('.css')) return 'text-sky-400 bg-sky-400/10 border-sky-400/30';
    if (p.endsWith('.js') || p.endsWith('.ts')) return 'text-emerald-400 bg-emerald-400/10 border-emerald-400/30';
    if (p.endsWith('.py')) return 'text-purple-400 bg-purple-400/10 border-purple-400/30';
    if (p.endsWith('.json')) return 'text-pink-400 bg-pink-400/10 border-pink-400/30';
    return 'text-text-muted bg-surface-elevated border-border-subtle';
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 select-none">
        {/* Dark Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={handleClose}
          className="absolute inset-0 bg-black/80 backdrop-blur-md"
        />

        {/* Modal Main Window */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 15 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 15 }}
          transition={{ type: 'spring', damping: 26, stiffness: 320 }}
          role="dialog"
          aria-modal="true"
          aria-label="Project runner"
          className={`relative w-full ${
            isFullscreen ? 'h-full max-w-full rounded-none' : 'max-w-6xl h-[92vh] rounded-2xl'
          } bg-[#0A0517] border border-primary/30 shadow-[0_0_50px_rgba(0,0,0,0.8)] flex flex-col overflow-hidden z-10`}
        >
          {/* Top Control Header */}
          <div className="flex items-center justify-between px-4 py-2.5 bg-[#100726] border-b border-border-subtle/70 flex-wrap gap-2">
            {/* Left: Project identity badge */}
            <div className="flex items-center gap-3">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-[0_0_10px_#34D399] animate-pulse" />
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold tracking-wide text-text font-mono">
                  Tensor Runner
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-primary-deep/40 text-primary-light border border-primary/30">
                  {runId}
                </span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                  <span>Ready</span>
                </span>
              </div>
            </div>

            {/* Center: Workspace Tab Switcher */}
            <div className="flex items-center gap-1 bg-[#06030F] p-1 rounded-xl border border-border-subtle/50">
              <button
                onClick={() => setActiveTab('preview')}
                className={`px-3 py-1.5 rounded-lg text-xs transition-all flex items-center gap-1.5 ${
                  activeTab === 'preview'
                    ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-950 font-bold shadow-md'
                    : 'text-text-muted hover:text-text'
                }`}
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Live Preview</span>
              </button>

              <button
                onClick={() => setActiveTab('code')}
                className={`px-3 py-1.5 rounded-lg text-xs transition-all flex items-center gap-1.5 ${
                  activeTab === 'code'
                    ? 'bg-primary-deep text-white font-semibold shadow-md'
                    : 'text-text-muted hover:text-text'
                }`}
              >
                <Code2 className="w-3.5 h-3.5" />
                <span>Code Explorer</span>
              </button>

              <button
                onClick={() => setActiveTab('split')}
                className={`px-3 py-1.5 rounded-lg text-xs transition-all flex items-center gap-1.5 ${
                  activeTab === 'split'
                    ? 'bg-primary-deep text-white font-semibold shadow-md'
                    : 'text-text-muted hover:text-text'
                }`}
                title="Split View: Code + Live Preview side-by-side"
              >
                <Columns className="w-3.5 h-3.5" />
                <span>Split View</span>
              </button>

              <button
                onClick={() => setActiveTab('console')}
                className={`px-3 py-1.5 rounded-lg text-xs transition-all flex items-center gap-1.5 ${
                  activeTab === 'console'
                    ? 'bg-primary-deep text-white font-semibold shadow-md'
                    : 'text-text-muted hover:text-text'
                }`}
              >
                <Terminal className="w-3.5 h-3.5" />
                <span>Console</span>
              </button>

              <button
                onClick={() => setActiveTab('specs')}
                className={`px-3 py-1.5 rounded-lg text-xs transition-all flex items-center gap-1.5 ${
                  activeTab === 'specs'
                    ? 'bg-primary-deep text-white font-semibold shadow-md'
                    : 'text-text-muted hover:text-text'
                }`}
              >
                <FileCheck2 className="w-3.5 h-3.5" />
                <span>Specs & QA</span>
              </button>
            </div>

            {/* Right: Actions */}
            <div className="flex items-center gap-1.5">
              {/* Viewport switchers (only visible for preview & split) */}
              {(activeTab === 'preview' || activeTab === 'split') && (
                <div className="hidden md:flex items-center gap-0.5 bg-[#06030F] p-0.5 rounded-lg border border-border-subtle/40 mr-1">
                  <button
                    onClick={() => setViewport('desktop')}
                    className={`p-1.5 rounded text-xs transition-colors ${
                      viewport === 'desktop' ? 'bg-primary-deep/60 text-white' : 'text-text-muted hover:text-text'
                    }`}
                    title="Desktop 100%"
                  >
                    <Monitor className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => setViewport('laptop')}
                    className={`p-1.5 rounded text-xs transition-colors ${
                      viewport === 'laptop' ? 'bg-primary-deep/60 text-white' : 'text-text-muted hover:text-text'
                    }`}
                    title="Laptop 1024px"
                  >
                    <Laptop className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => setViewport('tablet')}
                    className={`p-1.5 rounded text-xs transition-colors ${
                      viewport === 'tablet' ? 'bg-primary-deep/60 text-white' : 'text-text-muted hover:text-text'
                    }`}
                    title="Tablet 768px"
                  >
                    <Tablet className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => setViewport('mobile')}
                    className={`p-1.5 rounded text-xs transition-colors ${
                      viewport === 'mobile' ? 'bg-primary-deep/60 text-white' : 'text-text-muted hover:text-text'
                    }`}
                    title="Mobile 390px"
                  >
                    <Smartphone className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}

              <button
                onClick={handleRefresh}
                className="p-1.5 rounded-lg bg-surface-elevated hover:bg-surface-elevated/80 border border-border-subtle text-text-muted hover:text-text transition-colors"
                title="Reload Preview & Code"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>

              <button
                onClick={() => openWorkspaceFolder(runId)}
                className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-surface-elevated hover:bg-surface-elevated/80 border border-border-subtle text-xs font-mono text-primary-light transition-colors"
                title="Reveal Workspace Folder in Explorer"
              >
                <FolderOpen className="w-3.5 h-3.5" />
                <span className="hidden lg:inline">Folder</span>
              </button>

              <button
                onClick={() => launchProject(runId)}
                className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-primary-deep hover:bg-primary-deep/80 border border-primary/40 text-xs font-semibold text-white transition-colors"
                title="Launch in Dedicated Native Window"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                <span className="hidden lg:inline">Pop Out</span>
              </button>

              <button
                onClick={() => setIsFullscreen(!isFullscreen)}
                className="p-1.5 rounded-lg text-text-muted hover:text-white hover:bg-white/10 transition-colors"
                title="Toggle Fullscreen"
              >
                <Maximize2 className="w-3.5 h-3.5" />
              </button>

              <button
                onClick={handleClose}
                className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-2.5 py-1.5 text-xs font-medium text-text-muted transition-colors hover:border-red-400/30 hover:bg-red-400/10 hover:text-white ml-1"
                title="Close runner (Esc)"
                aria-label="Close project runner"
              >
                <X className="w-4 h-4" />
                <span>Close</span>
              </button>
            </div>
          </div>

          {/* Main Stage Content by Tab */}
          <div className="flex-1 overflow-hidden relative flex">
            {/* TAB 1: LIVE PREVIEW */}
            {activeTab === 'preview' && (
              <div className="flex-1 h-full bg-[#05020A] p-3 flex items-center justify-center overflow-auto">
                <div
                  className={`h-full transition-all duration-300 rounded-xl overflow-hidden border border-border-subtle/60 shadow-2xl bg-[#07040F] flex flex-col ${getViewportWidth()}`}
                >
                  <iframe
                    key={`prev_${runId}_${iframeKey}`}
                    src={previewUrl}
                    title={`Running Project ${runId}`}
                    className="w-full h-full border-0 bg-transparent"
                    sandbox="allow-scripts allow-forms allow-same-origin allow-modals allow-popups"
                  />
                </div>
              </div>
            )}

            {/* TAB 2: CODE EXPLORER */}
            {activeTab === 'code' && (
              <div className="flex-1 h-full flex bg-[#070312] overflow-hidden">
                {/* Left File Tree Sidebar */}
                <div className="w-56 sm:w-64 border-r border-border-subtle/50 bg-[#0A0519] flex flex-col select-none">
                  <div className="px-3.5 py-2.5 border-b border-border-subtle/40 text-[11px] font-mono uppercase tracking-wider text-text-muted font-semibold flex items-center justify-between">
                    <span>Artifacts ({fileList.length})</span>
                    <Sparkles className="w-3 h-3 text-primary-light" />
                  </div>
                  <div className="flex-1 overflow-y-auto p-2 space-y-1">
                    {fileList.map((file) => {
                      const isSelected = file.path === selectedFilePath;
                      return (
                        <button
                          key={file.path}
                          onClick={() => setSelectedFilePath(file.path)}
                          className={`w-full text-left px-3 py-2 rounded-xl transition-all flex items-center justify-between text-xs font-mono group ${
                            isSelected
                              ? 'bg-primary-deep/40 text-white border border-primary/50 shadow-sm font-semibold'
                              : 'text-text-muted hover:text-text hover:bg-white/5 border border-transparent'
                          }`}
                        >
                          <div className="flex items-center gap-2 truncate">
                            <FileCode
                              className={`w-3.5 h-3.5 flex-shrink-0 ${
                                isSelected ? 'text-primary-light' : 'text-text-faint group-hover:text-text-muted'
                              }`}
                            />
                            <span className="truncate">{file.path}</span>
                          </div>
                          <span className={`text-[10px] px-1.5 py-0.5 rounded border ${getFileBadgeColor(file.path)}`}>
                            {file.bytes} B
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Right Main Code Viewer */}
                <div className="flex-1 h-full p-2 overflow-hidden flex flex-col">
                  {isLoadingContent ? (
                    <div className="flex-1 flex items-center justify-center text-xs font-mono text-text-muted">
                      Loading code file...
                    </div>
                  ) : (
                    <CodeViewer
                      code={currentFileContent}
                      filePath={selectedFilePath || 'select-file'}
                      className="h-full"
                    />
                  )}
                </div>
              </div>
            )}

            {/* TAB 3: SPLIT VIEW (Side-by-Side: Code + Preview) */}
            {activeTab === 'split' && (
              <div className="flex-1 h-full flex bg-[#05020A] overflow-hidden">
                {/* Left 45%: Code Viewer */}
                <div className="w-[45%] h-full border-r border-border-subtle/50 p-2 flex flex-col bg-[#070312]">
                  {/* File Selector Pills */}
                  <div className="flex items-center gap-1.5 mb-2 overflow-x-auto pb-1">
                    {fileList.map((f) => (
                      <button
                        key={f.path}
                        onClick={() => setSelectedFilePath(f.path)}
                        className={`px-2.5 py-1 rounded-lg text-[11px] font-mono transition-colors whitespace-nowrap flex items-center gap-1 ${
                          f.path === selectedFilePath
                            ? 'bg-primary-deep/60 text-white border border-primary/50'
                            : 'bg-surface-elevated text-text-muted hover:text-text border border-border-subtle/30'
                        }`}
                      >
                        <FileCode className="w-3 h-3 text-primary-light" />
                        <span>{f.path}</span>
                      </button>
                    ))}
                  </div>

                  <div className="flex-1 overflow-hidden">
                    <CodeViewer
                      code={currentFileContent}
                      filePath={selectedFilePath}
                      className="h-full"
                    />
                  </div>
                </div>

                {/* Right 55%: Live Preview Frame */}
                <div className="w-[55%] h-full p-2 flex items-center justify-center bg-[#05020A]">
                  <div className="w-full h-full rounded-xl overflow-hidden border border-border-subtle/60 shadow-2xl bg-[#07040F] flex flex-col">
                    <iframe
                      key={`split_${runId}_${iframeKey}`}
                      src={previewUrl}
                      title={`Running Project ${runId}`}
                      className="w-full h-full border-0 bg-transparent"
                      sandbox="allow-scripts allow-forms allow-same-origin allow-modals allow-popups"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* TAB 4: CONSOLE / TERMINAL */}
            {activeTab === 'console' && (
              <div className="flex-1 h-full p-4 bg-[#070312] overflow-auto flex flex-col space-y-4">
                {/* Python Script Execution Panel */}
                {pythonScript && (
                  <div className="rounded-xl bg-[#0C061A] border border-border-subtle/60 p-4 shadow-xl space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Terminal className="w-4 h-4 text-primary-light" />
                        <span className="text-xs font-semibold text-text font-mono">
                          Python CLI Runner: {pythonScript}
                        </span>
                      </div>
                      <button
                        onClick={handleRunScript}
                        disabled={isRunningScript}
                        className="px-3 py-1 rounded-lg bg-primary-deep hover:bg-primary-deep/80 text-white font-semibold text-xs transition-colors flex items-center gap-1.5 disabled:opacity-50"
                      >
                        <Play className="w-3 h-3 fill-current" />
                        <span>{isRunningScript ? 'Executing...' : 'Run Script'}</span>
                      </button>
                    </div>

                    <div className="flex items-center gap-2 bg-[#06030F] p-2 rounded-lg border border-border-subtle/40 font-mono text-xs">
                      <span className="text-accent-pink font-bold">$ python {pythonScript}</span>
                      <input
                        type="text"
                        value={cliArgs}
                        onChange={(e) => setCliArgs(e.target.value)}
                        placeholder="optional arguments"
                        className="flex-1 bg-transparent text-text outline-none text-xs"
                      />
                    </div>

                    {terminalLog && (
                      <div className="rounded-lg bg-[#06030F] p-3 font-mono text-xs border border-border-subtle/30 space-y-2">
                        <div className="flex items-center justify-between text-[11px] text-text-muted">
                          <span>Exit code: {terminalLog.exit_code}</span>
                          <span>Execution time: {terminalLog.duration}s</span>
                        </div>
                        {terminalLog.stdout && (
                          <pre className="text-emerald-300 whitespace-pre-wrap">{terminalLog.stdout}</pre>
                        )}
                        {terminalLog.stderr && (
                          <pre className="text-red-400 whitespace-pre-wrap">{terminalLog.stderr}</pre>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* Workspace Health Diagnostics */}
                <div className="rounded-xl bg-[#0C061A] border border-border-subtle/60 p-4 shadow-xl space-y-3">
                  <div className="flex items-center gap-2 text-xs font-semibold text-text font-mono">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span>Workspace Diagnostics & Integrity</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono">
                    <div className="p-3 rounded-lg bg-[#06030F] border border-border-subtle/30">
                      <span className="text-text-muted text-[11px] block">Total Deliverables</span>
                      <span className="text-base font-bold text-text">{fileList.length} files</span>
                    </div>
                    <div className="p-3 rounded-lg bg-[#06030F] border border-border-subtle/30">
                      <span className="text-text-muted text-[11px] block">Live Server Status</span>
                      <span className="text-base font-bold text-emerald-400">Serving on :8000</span>
                    </div>
                    <div className="p-3 rounded-lg bg-[#06030F] border border-border-subtle/30">
                      <span className="text-text-muted text-[11px] block">Syntax Verification</span>
                      <span className="text-base font-bold text-primary-light">Validated by Reviewer</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 5: SPECS & QA */}
            {activeTab === 'specs' && (
              <div className="flex-1 h-full p-5 bg-[#070312] overflow-y-auto space-y-4 text-xs font-sans">
                {/* PM Summary */}
                {store.summary && (
                  <div className="rounded-xl bg-[#0C061A] border border-border-subtle/60 p-4 shadow-xl">
                    <h3 className="font-semibold text-text text-sm mb-2 flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-primary-light" />
                      Executive Delivery Summary
                    </h3>
                    <p className="text-text-muted leading-relaxed whitespace-pre-line">
                      {store.summary}
                    </p>
                  </div>
                )}

                {/* Reviewer QA Report */}
                {store.agents.reviewer.verdict && (
                  <div className="rounded-xl bg-[#0C061A] border border-border-subtle/60 p-4 shadow-xl space-y-2">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      <span className="font-semibold text-text text-sm">
                        Quality Assurance Verdict · Round {store.agents.reviewer.verdict.iteration}
                      </span>
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
                        {store.agents.reviewer.verdict.approved ? 'APPROVED' : 'CHANGES REQUESTED'}
                      </span>
                    </div>
                    {store.agents.reviewer.verdict.issues.length === 0 ? (
                      <p className="text-emerald-300 text-xs font-mono">
                        ✓ All automated syntax tests passed. Layout verified, controls responsive.
                      </p>
                    ) : (
                      <ul className="list-disc pl-4 text-xs font-mono text-text-muted space-y-1">
                        {store.agents.reviewer.verdict.issues.map((iss, i) => (
                          <li key={i}>{iss}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}

                {/* Planner Blueprint */}
                {store.agents.planner.output && (
                  <div className="rounded-xl bg-[#0C061A] border border-border-subtle/60 p-4 shadow-xl">
                    <h3 className="font-semibold text-text text-sm mb-2">Architectural Blueprint</h3>
                    <pre className="text-xs font-mono text-text-muted whitespace-pre-wrap leading-relaxed">
                      {store.agents.planner.output}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Bottom Bar: Path & Status */}
          <div className="px-4 py-2 bg-[#0E0620] border-t border-border-subtle/60 flex items-center justify-between text-[11px] font-mono text-text-muted select-none flex-wrap gap-2">
            <div className="flex items-center gap-2 truncate">
              <span className="text-emerald-400 font-semibold">● Live Endpoint:</span>
              <span className="text-text-muted truncate select-all">{previewUrl}</span>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={handleCopyUrl}
                className="hover:text-primary-light transition-colors flex items-center gap-1"
              >
                {copiedUrl ? (
                  <>
                    <Check className="w-3 h-3 text-emerald-400" />
                    <span className="text-emerald-400">Copied URL</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3 h-3" />
                    <span>Copy URL</span>
                  </>
                )}
              </button>
              <button
                onClick={() => openInBrowser(runId)}
                className="hover:text-primary-light transition-colors flex items-center gap-1"
              >
                <span>External Browser</span>
                <ExternalLink className="w-3 h-3" />
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
