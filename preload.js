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
        openTerminal: () => ipcRenderer.invoke('window:openTerminal'),
        openDevTools: () => ipcRenderer.invoke('window:openDevTools')
    },
    dialog: {
        openAudioFiles: () => ipcRenderer.invoke('dialog:openAudioFiles')
    },
    sound: {
        onPlayDone: (callback) => {
            console.log('[Preload] Registering sound:playDone listener');
            ipcRenderer.on('sound:playDone', () => {
                console.log('[Preload] Received sound:playDone IPC message');
                callback();
            });
        }
    },
    log: {
        write: (level, source, message, data) => ipcRenderer.invoke('log:write', level, source, message, data),
        error: (source, message, data) => ipcRenderer.invoke('log:write', 'ERROR', source, message, data),
        warn: (source, message, data) => ipcRenderer.invoke('log:write', 'WARN', source, message, data),
        info: (source, message, data) => ipcRenderer.invoke('log:write', 'INFO', source, message, data),
        debug: (source, message, data) => ipcRenderer.invoke('log:write', 'DEBUG', source, message, data),
        clear: () => ipcRenderer.invoke('log:clear'),
        read: () => ipcRenderer.invoke('log:read')
    },
    platform: process.platform,
    isElectron: true
});
