const { app, BrowserWindow, ipcMain, screen, dialog, desktopCapturer, clipboard } = require('electron');
const path = require('path');
const os = require('os');
const fs = require('fs');
const http = require('http');
const { exec, spawn } = require('child_process');

// Hardware acceleration enabled (MIDI player was causing crashes, now disabled)

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

    mainWindow.loadFile('dashboard.html');
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

// Save file dialog
ipcMain.handle('dialog:saveFile', async (event, options) => {
    const result = await dialog.showSaveDialog(options);
    return result;
});

// ==========================================
// FILESYSTEM HANDLERS
// ==========================================

ipcMain.handle('fs:readDir', async (event, dirPath) => {
    try {
        const items = fs.readdirSync(dirPath, { withFileTypes: true });
        const result = items
            .filter(item => !item.name.startsWith('.')) // Hide hidden files
            .map(item => {
                const fullPath = path.join(dirPath, item.name);
                let size = 0;
                try {
                    if (!item.isDirectory()) {
                        size = fs.statSync(fullPath).size;
                    }
                } catch (e) {}
                return {
                    name: item.name,
                    path: fullPath,
                    isDir: item.isDirectory(),
                    size: size
                };
            });
        return { success: true, path: dirPath, items: result };
    } catch (err) {
        return { success: false, error: err.message };
    }
});

ipcMain.handle('fs:getHomeDir', () => os.homedir());

ipcMain.handle('fs:getDrives', async () => {
    if (os.platform() !== 'win32') {
        // On Mac/Linux, just return root
        return { success: true, drives: [{ letter: '/', label: 'Root', path: '/' }] };
    }

    try {
        // On Windows, check common drive letters
        const drives = [];
        const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');

        for (const letter of letters) {
            const drivePath = `${letter}:\\`;
            try {
                fs.accessSync(drivePath, fs.constants.R_OK);
                drives.push({
                    letter: letter,
                    label: `${letter}: Drive`,
                    path: drivePath
                });
            } catch (e) {
                // Drive doesn't exist or not accessible
            }
        }

        return { success: true, drives };
    } catch (err) {
        return { success: false, error: err.message };
    }
});

ipcMain.handle('fs:pathJoin', (event, ...args) => path.join(...args));

ipcMain.handle('fs:writeFile', async (event, filePath, dataUrl) => {
    try {
        // Ensure parent directory exists
        const dir = path.dirname(filePath);
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }

        // Convert data URL to buffer
        const base64Data = dataUrl.replace(/^data:image\/\w+;base64,/, '');
        const buffer = Buffer.from(base64Data, 'base64');
        fs.writeFileSync(filePath, buffer);
        return { success: true };
    } catch (err) {
        console.error('fs:writeFile error:', err);
        return { success: false, error: err.message };
    }
});

ipcMain.handle('fs:deleteFile', async (event, filePath) => {
    try {
        fs.unlinkSync(filePath);
        return { success: true };
    } catch (err) {
        return { success: false, error: err.message };
    }
});

// ==========================================
// SHELL EXECUTION HANDLER
// ==========================================

ipcMain.handle('shell:exec', async (event, command, options = {}) => {
    return new Promise((resolve) => {
        const timeout = options.timeout || 30000; // 30s default
        const cwd = options.cwd || process.env.HOME || process.env.USERPROFILE;

        exec(command, { timeout, cwd, maxBuffer: 10 * 1024 * 1024 }, (error, stdout, stderr) => {
            resolve({
                success: !error,
                stdout: stdout || '',
                stderr: stderr || '',
                error: error?.message || null,
                code: error?.code || 0
            });
        });
    });
});

// Read file contents (for diff, log tail, etc.)
ipcMain.handle('fs:readFile', async (event, filePath, options = {}) => {
    try {
        const encoding = options.encoding || 'utf8';
        const content = fs.readFileSync(filePath, encoding);
        return { success: true, content };
    } catch (err) {
        return { success: false, error: err.message };
    }
});

// Watch file for changes (log tail)
const fileWatchers = new Map();

ipcMain.handle('fs:watchFile', async (event, filePath, watchId) => {
    try {
        // Clear existing watcher if any
        if (fileWatchers.has(watchId)) {
            fileWatchers.get(watchId).close();
        }

        const watcher = fs.watch(filePath, (eventType) => {
            if (eventType === 'change') {
                const win = BrowserWindow.fromWebContents(event.sender);
                if (win && !win.isDestroyed()) {
                    win.webContents.send('fs:fileChanged', { watchId, filePath });
                }
            }
        });

        fileWatchers.set(watchId, watcher);
        return { success: true };
    } catch (err) {
        return { success: false, error: err.message };
    }
});

ipcMain.handle('fs:unwatchFile', async (event, watchId) => {
    if (fileWatchers.has(watchId)) {
        fileWatchers.get(watchId).close();
        fileWatchers.delete(watchId);
    }
    return { success: true };
});

// Get file stats
ipcMain.handle('fs:stat', async (event, filePath) => {
    try {
        const stats = fs.statSync(filePath);
        return {
            success: true,
            size: stats.size,
            mtime: stats.mtime.toISOString(),
            isFile: stats.isFile(),
            isDirectory: stats.isDirectory()
        };
    } catch (err) {
        return { success: false, error: err.message };
    }
});

// ==========================================
// CLIPBOARD HANDLER
// ==========================================

ipcMain.handle('clipboard:readText', async () => {
    try {
        const text = clipboard.readText();
        return { success: true, text };
    } catch (err) {
        return { success: false, error: err.message };
    }
});

ipcMain.handle('clipboard:writeText', async (event, text) => {
    try {
        clipboard.writeText(text);
        return { success: true };
    } catch (err) {
        return { success: false, error: err.message };
    }
});

// ==========================================
// SCREENSHOT HANDLER
// ==========================================

ipcMain.handle('screenshot:capture', async (event, bounds) => {
    try {
        const primaryDisplay = screen.getPrimaryDisplay();
        const scaleFactor = primaryDisplay.scaleFactor || 1;
        const { width: screenWidth, height: screenHeight } = primaryDisplay.size;

        const sources = await desktopCapturer.getSources({
            types: ['screen'],
            thumbnailSize: {
                width: Math.round(screenWidth * scaleFactor),
                height: Math.round(screenHeight * scaleFactor)
            }
        });

        if (sources.length === 0) {
            return { success: false, error: 'No screen sources available' };
        }

        // Get the primary screen source
        const source = sources[0];
        const thumbnail = source.thumbnail;

        // Crop to the selected region (bounds already scaled by renderer)
        const cropped = thumbnail.crop({
            x: Math.round(bounds.x),
            y: Math.round(bounds.y),
            width: Math.round(bounds.width),
            height: Math.round(bounds.height)
        });

        const dataUrl = cropped.toDataURL();
        return { success: true, dataUrl };
    } catch (err) {
        return { success: false, error: err.message };
    }
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
