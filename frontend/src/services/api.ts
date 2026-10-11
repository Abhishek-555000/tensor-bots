import { RunEvent } from '../types';
import replayData from '../assets/replay.json';

const API_BASE = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000';

export async function checkHealth(): Promise<{ ok: boolean; mock: boolean; model: string }> {
  try {
    const res = await fetch(`${API_BASE}/api/health`, { method: 'GET' });
    if (!res.ok) throw new Error('Health check returned non-200');
    return await res.json();
  } catch (err) {
    return { ok: false, mock: false, model: 'offline' };
  }
}

export async function fetchFileContent(runId: string, filePath: string): Promise<string> {
  try {
    const res = await fetch(`${API_BASE}/api/files/${runId}/${filePath}`);
    if (!res.ok) throw new Error('File fetch failed');
    return await res.text();
  } catch (err) {
    return `// Failed to load file content for: ${filePath}\n// ${String(err)}`;
  }
}

export async function streamRun(
  prompt: string,
  onEvent: (event: RunEvent) => void,
  onError: (err: any) => void
): Promise<() => void> {
  const controller = new AbortController();

  try {
    const response = await fetch(`${API_BASE}/api/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt }),
      signal: controller.signal,
    });

    if (!response.ok || !response.body) {
      throw new Error(`Failed to initiate run: status ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    const pump = async () => {
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith('data:')) {
              try {
                const jsonStr = trimmed.replace(/^data:\s*/, '');
                const eventObj = JSON.parse(jsonStr);
                onEvent(eventObj);
              } catch (parseErr) {
                console.warn('Could not parse SSE event JSON:', trimmed, parseErr);
              }
            }
          }
        }
      } catch (streamErr: any) {
        if (streamErr.name !== 'AbortError') {
          onError(streamErr);
        }
      }
    };

    pump();
  } catch (err: any) {
    if (err.name !== 'AbortError') {
      onError(err);
    }
  }

  return () => controller.abort();
}

export function replayRun(
  onEvent: (event: RunEvent) => void,
  onComplete: () => void
): () => void {
  let isCancelled = false;
  const events = replayData as RunEvent[];

  const runReplay = async () => {
    for (let i = 0; i < events.length; i++) {
      if (isCancelled) break;
      const current = events[i];
      onEvent(current);

      if (i < events.length - 1) {
        // Compute realistic delay between events (capped between 250ms and 1500ms)
        const next = events[i + 1];
        const delta = Math.max(300, Math.min(1500, (next.ts - current.ts) * 500));
        await new Promise((r) => setTimeout(r, delta));
      }
    }
    if (!isCancelled) onComplete();
  };

  runReplay();
  return () => {
    isCancelled = true;
  };
}
