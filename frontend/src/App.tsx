import React, { useEffect, useRef } from 'react';
import { Header } from './components/Header';
import { Constellation } from './components/Constellation';
import { InputBar } from './components/InputBar';
import { DetailPanel } from './components/DetailPanel';
import { FinishCard } from './components/FinishCard';
import { useRunStore } from './store/useRunStore';
import { checkHealth, streamRun, replayRun } from './services/api';

export const App: React.FC = () => {
  const {
    runState,
    errorMessage,
    setBackendHealthy,
    setIsMock,
    setIsReplay,
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
    setIsReplay(false);

    if (abortStreamRef.current) {
      abortStreamRef.current();
    }

    const abortFn = await streamRun(
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
    <div className="relative w-screen h-screen bg-background text-text overflow-hidden bg-grid-pattern flex flex-col justify-between">
      {/* Ambient center radial glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] bg-primary-deep/10 rounded-full blur-[140px] pointer-events-none" />

      {/* Top Header */}
      <Header onTriggerReplay={handleTriggerReplay} />

      {/* Error notification banner if run_error */}
      {errorMessage && runState === 'error' && (
        <div className="fixed top-14 left-1/2 -translate-x-1/2 px-4 py-2 rounded-xl bg-red-950/80 border border-error/40 text-error text-xs font-mono backdrop-blur-md z-30 shadow-lg">
          Error: {errorMessage}
        </div>
      )}

      {/* Main Center Stage Constellation */}
      <main className="flex-1 flex items-center justify-center p-4">
        <Constellation />
      </main>

      {/* Bottom Floating Input Bar */}
      <InputBar onSubmit={handleSubmitPrompt} onCancel={handleCancelRun} />

      {/* Slide-Over Detail Drawer */}
      <DetailPanel />

      {/* Completion Summary Card */}
      <FinishCard />
    </div>
  );
};

export default App;
