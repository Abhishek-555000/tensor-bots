const { app, BrowserWindow, ipcMain, shell, Menu } = require('electron');
const path = require('path');
const fs = require('fs');

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1240,
    height: 840,
    minWidth: 960,
    minHeight: 640,
    backgroundColor: '#0B0D12',
    titleBarStyle: 'hiddenInset',
    frame: true,
    titleBarOverlay: process.platform === 'win32' ? {
      color: '#0B0D12',
      symbolColor: '#EEF0F6',
      height: 32,
    } : false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  const devUrl = 'http://localhost:5173';
  if (process.env.NODE_ENV === 'development' || !app.isPackaged) {
    mainWindow.loadURL(devUrl);
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }
}

// Robust workspace path resolution relative to project root
function resolveWorkspaceDir(folderOrRunId) {
  const PROJECT_ROOT = path.resolve(__dirname, '../..');
  const WORKSPACE_DIR = path.resolve(PROJECT_ROOT, 'workspace');

  if (!folderOrRunId) {
    return WORKSPACE_DIR;
  }
  if (path.isAbsolute(folderOrRunId)) {
    return folderOrRunId;
  }
  if (folderOrRunId.startsWith('workspace/') || folderOrRunId.startsWith('workspace\\')) {
    return path.resolve(PROJECT_ROOT, folderOrRunId);
  }
  return path.resolve(WORKSPACE_DIR, folderOrRunId);
}

// IPC: Open Project Folder in OS File Explorer
ipcMain.handle('open-folder', async (_event, folderOrRunId) => {
  try {
    const targetDir = resolveWorkspaceDir(folderOrRunId);
    if (!fs.existsSync(targetDir)) {
      fs.mkdirSync(targetDir, { recursive: true });
    }
    const err = await shell.openPath(targetDir);
    if (err) {
      console.error('shell.openPath error:', err);
      return { success: false, error: err };
    }
    return { success: true, path: targetDir };
  } catch (err) {
    console.error('Failed to open folder:', err);
    return { success: false, error: err.message };
  }
});

// IPC: Open URL in default system browser
ipcMain.handle('open-external', async (_event, url) => {
  try {
    if (url) {
      await shell.openExternal(url);
      return { success: true };
    }
    return { success: false, error: 'No URL provided' };
  } catch (err) {
    console.error('Failed to open external URL:', err);
    return { success: false, error: err.message };
  }
});

// IPC: Run Project in a dedicated preview window
ipcMain.handle('run-project', async (_event, runId) => {
  try {
    const targetDir = resolveWorkspaceDir(runId);
    if (!fs.existsSync(targetDir)) {
      fs.mkdirSync(targetDir, { recursive: true });
    }

    const previewUrl = `http://localhost:8000/api/preview/${runId}/`;
    const indexHtmlPath = path.join(targetDir, 'index.html');
    const hasIndexHtml = fs.existsSync(indexHtmlPath);

    // Create a dedicated runner window
    const runnerWin = new BrowserWindow({
      width: 1080,
      height: 760,
      minWidth: 480,
      minHeight: 380,
      backgroundColor: '#0B0D12',
      title: `Tensor Bots — Running Project [${runId}]`,
      autoHideMenuBar: false,
      webPreferences: {
        contextIsolation: true,
        nodeIntegration: false,
      },
    });

    // Custom runner application menu with quick developer tools
    const menuTemplate = [
      {
        label: 'Project Actions',
        submenu: [
          {
            label: '📂 Open Folder in Explorer',
            click: () => {
              shell.openPath(targetDir);
            },
          },
          {
            label: '🌐 Open in Default Browser',
            click: () => {
              shell.openExternal(previewUrl);
            },
          },
          { type: 'separator' },
          {
            label: '🔄 Reload Project',
            accelerator: 'CmdOrCtrl+R',
            click: () => runnerWin.reload(),
          },
          {
            label: '🛠 Toggle Developer Tools',
            accelerator: 'CmdOrCtrl+Shift+I',
            click: () => runnerWin.webContents.toggleDevTools(),
          },
          { type: 'separator' },
          {
            label: '✕ Close Window',
            accelerator: 'CmdOrCtrl+W',
            click: () => runnerWin.close(),
          },
        ],
      },
      {
        label: 'View',
        submenu: [
          { role: 'resetZoom' },
          { role: 'zoomIn' },
          { role: 'zoomOut' },
          { type: 'separator' },
          { role: 'togglefullscreen' },
        ],
      },
    ];
    runnerWin.setMenu(Menu.buildFromTemplate(menuTemplate));

    // Try loading previewUrl from FastAPI; if backend is offline, fallback to local index.html directly
    runnerWin.loadURL(previewUrl).catch((navErr) => {
      console.warn('Backend server offline, falling back to local file load:', navErr.message);
      if (hasIndexHtml) {
        runnerWin.loadFile(indexHtmlPath);
      }
    });

    return { success: true, folder: targetDir, previewUrl };
  } catch (err) {
    console.error('Failed to run project:', err);
    return { success: false, error: err.message };
  }
});

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
