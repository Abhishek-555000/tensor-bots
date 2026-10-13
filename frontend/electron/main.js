const { app, BrowserWindow, ipcMain, shell } = require('electron');
const path = require('path');

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 820,
    minWidth: 960,
    minHeight: 640,
    backgroundColor: '#07040F',
    titleBarStyle: 'hiddenInset',
    frame: true,
    titleBarOverlay: process.platform === 'win32' ? {
      color: '#07040F',
      symbolColor: '#E4E0F0',
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
    console.log(`[Electron] Launching window with ${devUrl}...`);
    mainWindow.loadURL(devUrl);
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }

  mainWindow.webContents.on('did-finish-load', () => {
    console.log('[Electron] Desktop window loaded successfully.');
  });

  mainWindow.webContents.on('did-fail-load', (_event, errorCode, errorDescription) => {
    console.error(`[Electron] Failed to load URL: ${errorDescription} (${errorCode})`);
  });
}

ipcMain.handle('open-folder', async (_event, folderPath) => {
  try {
    if (folderPath) {
      await shell.openPath(folderPath);
      return { success: true };
    }
  } catch (err) {
    console.error('Failed to open folder:', err);
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
