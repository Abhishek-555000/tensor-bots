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

export function streamRun(
  prompt: string,
  onEvent: (event: RunEvent) => void,
  onError: (err: any) => void
): () => void {
  const controller = new AbortController();

  const pump = async () => {
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
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        onError(err);
      }
    }
  };

  void pump();
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
        // Keep the demo lively while preserving a readable pause between steps.
        const next = events[i + 1];
        const delta = Math.max(180, Math.min(900, (next.ts - current.ts) * 350));
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

export async function openWorkspaceFolder(runId: string): Promise<boolean> {
  if ((window as any).electronAPI?.openFolder) {
    const res = await (window as any).electronAPI.openFolder(runId);
    return res?.success ?? true;
  }
  try {
    const res = await fetch(`${API_BASE}/api/open-folder/${runId}`, { method: 'POST' });
    return res.ok;
  } catch (err) {
    console.error('Failed to trigger open-folder via API:', err);
    return false;
  }
}

export async function launchProject(runId: string): Promise<boolean> {
  if ((window as any).electronAPI?.runProject) {
    const res = await (window as any).electronAPI.runProject(runId);
    return res?.success ?? true;
  }
  window.open(`${API_BASE}/api/preview/${runId}/`, '_blank');
  return true;
}

export async function fetchRunFiles(runId: string): Promise<Array<{ path: string; bytes: number }>> {
  try {
    const res = await fetch(`${API_BASE}/api/files/${runId}`);
    if (!res.ok) throw new Error('File list failed');
    const data = await res.json();
    return data.files || [];
  } catch (err) {
    console.error('Failed to list run files:', err);
    return [];
  }
}

export async function executePythonScript(
  runId: string,
  script?: string
): Promise<{ ok: boolean; stdout?: string; stderr?: string; exit_code?: number; duration?: number; error?: string }> {
  try {
    const query = script ? `?script=${encodeURIComponent(script)}` : '';
    const res = await fetch(`${API_BASE}/api/execute/${runId}${query}`);
    return await res.json();
  } catch (err) {
    return { ok: false, error: String(err) };
  }
}

export async function openInBrowser(runId: string): Promise<boolean> {
  const url = `${API_BASE}/api/preview/${runId}/`;
  if ((window as any).electronAPI?.openExternal) {
    const res = await (window as any).electronAPI.openExternal(url);
    return res?.success ?? true;
  }
  window.open(url, '_blank');
  return true;
}
