const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  openFolder: (folderPath) => ipcRenderer.invoke('open-folder', folderPath),
  runProject: (runId) => ipcRenderer.invoke('run-project', runId),
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
  isElectron: true,
});
