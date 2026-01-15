const { app, BrowserWindow, ipcMain, screen, dialog } = require('electron');
const path = require('path');
const os = require('os');
const fs = require('fs');
const http = require('http');

// Log file path
const LOG_FILE = path.join(__dirname, 'o-face.log');

// HTTP server for external sound triggers (Claude Code hooks, etc.)
const SOUND_SERVER_PORT = 9876;
let soundServer = null;

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

ipcMain.handle('window:openDevTools', (event) => {
    const win = BrowserWindow.fromWebContents(event.sender);
    if (win) win.webContents.toggleDevTools();
});

// App lifecycle
app.whenReady().then(() => {
    createMainWindow();
    startSoundServer();

    // Log renderer crashes
    mainWindow.webContents.on('crashed', (event, killed) => {
        writeLog('ERROR', 'Main', 'Renderer process crashed', { killed });
    });

    mainWindow.webContents.on('render-process-gone', (event, details) => {
        writeLog('ERROR', 'Main', 'Render process gone', details);
    });
});

app.on('window-all-closed', () => {
    stopSoundServer();
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createMainWindow();
    }
});

// Logging system
function writeLog(level, source, message, data) {
    const timestamp = new Date().toISOString();
    const logEntry = {
        timestamp,
        level,
        source,
        message,
        data: data || null
    };
    const line = JSON.stringify(logEntry) + '\n';

    fs.appendFile(LOG_FILE, line, (err) => {
        if (err) console.error('Failed to write log:', err);
    });

    // Also log to console
    console.log(`[${level}] [${source}] ${message}`, data || '');
}

ipcMain.handle('log:write', async (event, level, source, message, data) => {
    writeLog(level, source, message, data);
    return { success: true };
});

ipcMain.handle('log:clear', async () => {
    fs.writeFile(LOG_FILE, '', (err) => {
        if (err) console.error('Failed to clear log:', err);
    });
    return { success: true };
});

ipcMain.handle('log:read', async () => {
    try {
        const content = fs.readFileSync(LOG_FILE, 'utf8');
        return { success: true, content };
    } catch (err) {
        return { success: false, error: err.message };
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

// Start HTTP server for external sound triggers
function startSoundServer() {
    if (soundServer) {
        console.log('[SoundServer] Server already running');
        return;
    }

    console.log('[SoundServer] Starting HTTP server...');

    soundServer = http.createServer((req, res) => {
        const timestamp = new Date().toISOString();
        console.log(`[SoundServer] ${timestamp} ${req.method} ${req.url}`);

        // Enable CORS for local requests
        res.setHeader('Access-Control-Allow-Origin', '*');
        res.setHeader('Access-Control-Allow-Methods', 'GET, POST');

        if (req.url === '/play-done' || req.url === '/play-done/') {
            // Send play-done signal to all windows
            const windows = BrowserWindow.getAllWindows();
            console.log(`[SoundServer] Broadcasting sound:playDone to ${windows.length} window(s)`);

            windows.forEach((win, i) => {
                if (!win.isDestroyed()) {
                    console.log(`[SoundServer] Sending to window ${i}`);
                    win.webContents.send('sound:playDone');
                }
            });

            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ success: true, message: 'Sound triggered' }));
        } else if (req.url === '/health' || req.url === '/') {
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ status: 'ok', port: SOUND_SERVER_PORT }));
        } else {
            console.log(`[SoundServer] 404 - Unknown path: ${req.url}`);
            res.writeHead(404, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: 'Not found' }));
        }
    });

    soundServer.listen(SOUND_SERVER_PORT, '127.0.0.1', () => {
        console.log(`[SoundServer] Listening on http://127.0.0.1:${SOUND_SERVER_PORT}`);
        console.log('[SoundServer] Endpoints: /play-done, /health');
    });

    soundServer.on('error', (err) => {
        console.error('[SoundServer] Error:', err.message);
        if (err.code === 'EADDRINUSE') {
            console.error(`[SoundServer] Port ${SOUND_SERVER_PORT} already in use`);
        }
    });
}

function stopSoundServer() {
    if (soundServer) {
        console.log('[SoundServer] Stopping server...');
        soundServer.close();
        soundServer = null;
    }
}
