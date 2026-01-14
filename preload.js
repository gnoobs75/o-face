const { contextBridge, ipcRenderer } = require('electron');

// Expose terminal API to renderer - supports multiple terminals
contextBridge.exposeInMainWorld('electronAPI', {
    terminal: {
        create: (id) => ipcRenderer.invoke('terminal:create', id),
        write: (id, data) => ipcRenderer.invoke('terminal:write', id, data),
        resize: (id, cols, rows) => ipcRenderer.invoke('terminal:resize', id, cols, rows),
        kill: (id) => ipcRenderer.invoke('terminal:kill', id),
        killAll: () => ipcRenderer.invoke('terminal:killAll'),
        onData: (callback) => {
            ipcRenderer.on('terminal:data', (event, { id, data }) => callback(id, data));
        },
        onExit: (callback) => {
            ipcRenderer.on('terminal:exit', (event, { id }) => callback(id));
        }
    },
    window: {
        minimize: () => ipcRenderer.invoke('window:minimize'),
        maximize: () => ipcRenderer.invoke('window:maximize'),
        close: () => ipcRenderer.invoke('window:close'),
        openTerminal: () => ipcRenderer.invoke('window:openTerminal')
    },
    dialog: {
        openAudioFiles: () => ipcRenderer.invoke('dialog:openAudioFiles')
    },
    platform: process.platform,
    isElectron: true
});
