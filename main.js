const { app, BrowserWindow, ipcMain, screen, dialog } = require('electron');
const path = require('path');
const os = require('os');

// Handle node-pty native module
let pty;
try {
    pty = require('node-pty');
} catch (e) {
    console.error('node-pty not available:', e.message);
}

let mainWindow;
let terminalWindow;
const ptyProcesses = new Map(); // Track multiple terminals by ID
let nextPtyId = 0;

function createMainWindow() {
    const primaryDisplay = screen.getPrimaryDisplay();
    const { width, height } = primaryDisplay.workAreaSize;

    mainWindow = new BrowserWindow({
        width: width,
        height: height,
        x: 0,
        y: 0,
        icon: path.join(__dirname, 'icon.png'),
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        backgroundColor: '#18181C',
        frame: false,
        titleBarStyle: 'hidden'
    });

    mainWindow.loadFile('splash.html');
    mainWindow.maximize();

    if (process.argv.includes('--dev')) {
        mainWindow.webContents.openDevTools();
    }

    mainWindow.on('closed', () => {
        mainWindow = null;
        // Close terminal window if main closes
        if (terminalWindow && !terminalWindow.isDestroyed()) {
            terminalWindow.close();
        }
    });
}

function createTerminalWindow() {
    // If terminal window exists, just focus it
    if (terminalWindow && !terminalWindow.isDestroyed()) {
        terminalWindow.focus();
        return;
    }

    const primaryDisplay = screen.getPrimaryDisplay();
    const { width, height } = primaryDisplay.workAreaSize;

    terminalWindow = new BrowserWindow({
        width: Math.floor(width * 0.8),
        height: Math.floor(height * 0.8),
        icon: path.join(__dirname, 'icon.png'),
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        backgroundColor: '#0c0c0c',
        frame: false,
        titleBarStyle: 'hidden',
        parent: null, // Independent window
        modal: false
    });

    terminalWindow.loadFile('terminals.html');
    terminalWindow.center();

    if (process.argv.includes('--dev')) {
        terminalWindow.webContents.openDevTools();
    }

    terminalWindow.on('closed', () => {
        terminalWindow = null;
        // Kill all PTY processes when terminal window closes
        for (const [id, proc] of ptyProcesses) {
            proc.kill();
        }
        ptyProcesses.clear();
        nextPtyId = 0;
    });
}

// Open terminal window
ipcMain.handle('window:openTerminal', () => {
    createTerminalWindow();
    return { success: true };
});

// Create a new PTY process
ipcMain.handle('terminal:create', async (event, terminalId) => {
    if (!pty) {
        return { error: 'node-pty not available. Run: npm install' };
    }

    const id = terminalId || `term-${nextPtyId++}`;
    const shell = os.platform() === 'win32' ? 'powershell.exe' : 'bash';

    const ptyProcess = pty.spawn(shell, [], {
        name: 'xterm-color',
        cols: 80,
        rows: 24,
        cwd: process.env.HOME || process.env.USERPROFILE,
        env: process.env
    });

    ptyProcesses.set(id, ptyProcess);

    ptyProcess.onData((data) => {
        // Send to terminal window
        if (terminalWindow && !terminalWindow.isDestroyed()) {
            terminalWindow.webContents.send('terminal:data', { id, data });
        }
    });

    ptyProcess.onExit(() => {
        ptyProcesses.delete(id);
        if (terminalWindow && !terminalWindow.isDestroyed()) {
            terminalWindow.webContents.send('terminal:exit', { id });
        }
    });

    return { success: true, id, shell };
});

// Write to a specific terminal
ipcMain.handle('terminal:write', async (event, id, data) => {
    const proc = ptyProcesses.get(id);
    if (proc) {
        proc.write(data);
        return { success: true };
    }
    return { error: 'Terminal not found: ' + id };
});

// Resize a specific terminal
ipcMain.handle('terminal:resize', async (event, id, cols, rows) => {
    const proc = ptyProcesses.get(id);
    if (proc) {
        proc.resize(cols, rows);
        return { success: true };
    }
    return { error: 'Terminal not found: ' + id };
});

// Kill a specific terminal
ipcMain.handle('terminal:kill', async (event, id) => {
    const proc = ptyProcesses.get(id);
    if (proc) {
        proc.kill();
        ptyProcesses.delete(id);
        return { success: true };
    }
    return { error: 'Terminal not found: ' + id };
});

// Kill all terminals
ipcMain.handle('terminal:killAll', async () => {
    for (const [id, proc] of ptyProcesses) {
        proc.kill();
    }
    ptyProcesses.clear();
    nextPtyId = 0;
    return { success: true };
});

// Window controls (works for whichever window calls it)
ipcMain.handle('window:minimize', (event) => {
    const win = BrowserWindow.fromWebContents(event.sender);
    if (win) win.minimize();
});

ipcMain.handle('window:maximize', (event) => {
    const win = BrowserWindow.fromWebContents(event.sender);
    if (win) {
        if (win.isMaximized()) {
            win.unmaximize();
        } else {
            win.maximize();
        }
    }
});

ipcMain.handle('window:close', (event) => {
    const win = BrowserWindow.fromWebContents(event.sender);
    if (win) win.close();
});

// App lifecycle
app.whenReady().then(createMainWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createMainWindow();
    }
});

// File dialog for audio player
ipcMain.handle('dialog:openAudioFiles', async () => {
    const result = await dialog.showOpenDialog({
        properties: ['openFile', 'multiSelections'],
        filters: [
            { name: 'Audio Files', extensions: ['mp3', 'wav', 'ogg', 'flac', 'm4a', 'aac'] }
        ]
    });
    return result.canceled ? [] : result.filePaths;
});
