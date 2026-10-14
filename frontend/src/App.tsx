import React, { useEffect, useRef } from 'react';
import { Header } from './components/Header';
import { Constellation } from './components/Constellation';
import { InputBar } from './components/InputBar';
import { DetailPanel } from './components/DetailPanel';
import { FinishCard } from './components/FinishCard';
import { ProjectRunnerModal } from './components/ProjectRunnerModal';
import { useRunStore } from './store/useRunStore';
import { checkHealth, streamRun, replayRun } from './services/api';

export const App: React.FC = () => {
  const {
    runState,
    errorMessage,
    activeAgentModal,
    runnerModalOpen,
    finishCardDismissed,
    setBackendHealthy,
    setIsMock,
    setIsReplay,
    closeRunnerModal,
    dismissFinishCard,
    setPrompt,
    resetRun,
    handleEvent,
  } = useRunStore();

  const abortStreamRef = useRef<(() => void) | null>(null);

  // Poll backend health on startup and periodically
  useEffect(() => {
    const updateHealth = async () => {
      const health = await checkHealth();
      setBackendHealthy(health.ok);
      setIsMock(health.mock);
    };

    updateHealth();
    const interval = setInterval(updateHealth, 10000);
    return () => clearInterval(interval);
  }, [setBackendHealthy, setIsMock]);

  // Handle live submission
  const handleSubmitPrompt = async (promptText: string) => {
    resetRun();
    setPrompt(promptText);
    setIsReplay(false);

    if (abortStreamRef.current) {
      abortStreamRef.current();
    }

    const abortFn = streamRun(
      promptText,
      (event) => handleEvent(event),
      (err) => {
        handleEvent({
          type: 'run_error',
          ts: Date.now() / 1000,
          message: err.message || 'Stream connection lost.',
        });
      }
    );

    abortStreamRef.current = abortFn;
  };

  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') return;
      const target = event.target;
      if (
        target instanceof HTMLElement &&
        target.closest('input, textarea, select, [contenteditable="true"]')
      ) {
        return;
      }

      if (activeAgentModal) return;
      if (runnerModalOpen) {
        closeRunnerModal();
      } else if (runState === 'completed' && !finishCardDismissed) {
        dismissFinishCard();
      } else if (errorMessage) {
        useRunStore.setState({ errorMessage: null });
      }
    };

    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [
    activeAgentModal,
    closeRunnerModal,
    dismissFinishCard,
    errorMessage,
    finishCardDismissed,
    runState,
    runnerModalOpen,
  ]);

  // Handle offline demo replay
  const handleTriggerReplay = () => {
    resetRun();
    setIsReplay(true);

    if (abortStreamRef.current) {
      abortStreamRef.current();
    }

    const stopReplay = replayRun(
      (event) => handleEvent(event),
      () => setIsReplay(false)
    );

    abortStreamRef.current = stopReplay;
  };

  // Handle abort/cancel
  const handleCancelRun = () => {
    if (abortStreamRef.current) {
      abortStreamRef.current();
      abortStreamRef.current = null;
    }
    resetRun();
  };

  return (
    <div className="app-shell relative h-screen min-h-0 w-screen bg-background text-text overflow-hidden bg-grid-pattern">
      <Header onTriggerReplay={handleTriggerReplay} />

      <div className="pointer-events-none absolute left-1/2 top-1/2 h-[min(72vh,760px)] w-[min(72vw,1100px)] -translate-x-1/2 -translate-y-1/2 rounded-full bg-primary-deep/[0.08] blur-[120px]" />

      {errorMessage && (
        <div className="fixed top-20 left-1/2 -translate-x-1/2 max-w-lg px-4 py-2.5 rounded-xl bg-red-950/90 border border-red-500/40 text-red-300 text-xs font-mono backdrop-blur-md z-40 shadow-xl flex items-start justify-between gap-3">
          <span className="line-clamp-2 leading-relaxed">
            {errorMessage.length > 200 ? `${errorMessage.slice(0, 200)}...` : errorMessage}
          </span>
          <button
            onClick={() => useRunStore.setState({ errorMessage: null })}
            className="text-red-400 hover:text-white p-0.5 rounded transition-colors text-xs"
          >
            ✕
          </button>
        </div>
      )}

      <main className="workspace-stage absolute inset-3 z-0 flex items-center justify-center overflow-hidden rounded-[28px] border border-white/[0.07] bg-surface/[0.2] shadow-[0_24px_80px_rgba(0,0,0,0.22)] sm:inset-5">
        <Constellation />
      </main>

      <InputBar onSubmit={handleSubmitPrompt} onCancel={handleCancelRun} />

      <DetailPanel />

      <FinishCard />

      <ProjectRunnerModal />
    </div>
  );
};

export default App;
