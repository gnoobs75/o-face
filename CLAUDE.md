# o-face Project

The Unofficial Homepage of Ronin - A retro-styled personal dashboard combining meme generation, GIF search, and multi-terminal management in an Electron app.

## Project Structure

```
memeBoss/
├── main.js           # Electron main process - window management, PTY handling
├── preload.js        # Secure IPC bridge between renderer and Node.js
├── meme.html         # Original meme/GIF page (browser-compatible)
├── terminals.html    # Multi-pane terminal interface (Electron-only)
├── package.json      # Project config and dependencies
├── start.bat         # Windows launcher
└── CLAUDE.md         # This file
```

## Running the App

```bash
# Install dependencies
npm install

# Start Electron app
npm start

# Or use the batch file (Windows)
start.bat
```

## Current Features

### Meme Generator (meme.html)
- GIF search via Klipy API (4x4 grid, paginated)
- Meme template search via Imgflip API (100 templates)
- Canvas-based text rendering with drag & resize
- Multiple text lines support
- Favorites system (localStorage) with export/import
- Lightbox with Ctrl+C copy workaround
- Retro flaming text effects

### Terminal Multiplexer (terminals.html)
- 4-pane tiled terminal layout
- Real PowerShell/bash via node-pty
- Layout switching: 1, 2H, 2V, 4 panes
- Keyboard navigation (Ctrl+1-4, Alt+Arrows)
- Attention notifications when commands complete
- Audio alerts via Web Audio API
- Visual pane flashing for inactive terminals

## Tech Stack

- **Electron** - Cross-platform desktop app framework
- **node-pty** - Native terminal emulation
- **xterm.js** - Terminal UI in browser
- **Web Audio API** - Notification sounds
- **Canvas API** - Meme text rendering
- **CSS Grid** - Terminal pane layouts

## Key APIs

- **Klipy API** - GIF/sticker search (key in meme.html)
- **Imgflip API** - Meme templates (free, no auth)

---

## Skills & Knowledge Areas

### Core Technologies
- Electron (main process, renderer, preload, IPC)
- Node.js (file system, child processes, native modules)
- HTML5/CSS3 (Grid, Flexbox, animations, custom properties)
- JavaScript ES6+ (async/await, modules, DOM manipulation)

### APIs & Integrations
- REST API consumption (fetch, error handling)
- Klipy API for GIF search
- Imgflip API for meme templates
- Web Audio API for sound synthesis
- Canvas API for image manipulation
- Clipboard API (with limitations)
- Selection API for copy workarounds

### Terminal & Shell
- PTY (pseudo-terminal) concepts
- PowerShell on Windows
- Bash/zsh on Mac/Linux
- ANSI escape codes
- xterm.js terminal emulation
- ConPTY on Windows

### Retro Web & MySpace Era
- 90s/2000s web aesthetics
- Animated GIFs and blinkies
- Marquee and scrolling text
- Visitor counters
- Guestbooks
- Custom cursors and mouse trails
- WinAmp-style interfaces
- Embedded media players

### Audio & Visualization
- Web Audio API oscillators
- Frequency analysis
- Audio visualization techniques
- Chiptune/8-bit sound synthesis

### Gaming & Emulation
- JavaScript emulators (JSNes, GameBoy.js)
- ROM handling
- Canvas-based rendering
- Game loop patterns

### Cross-Platform Development
- Platform detection (Windows/Mac/Linux)
- Path handling differences
- Keyboard shortcut conventions (Ctrl vs Cmd)
- Native module compilation

### UI/UX Patterns
- Dark theme design
- Terminal color schemes
- Grid-based layouts
- Keyboard-first navigation
- Notification systems
- Toast messages

---

## Code Conventions

- Single HTML files with embedded CSS/JS for simplicity
- CSS custom properties for theming
- Async/await for asynchronous operations
- Event delegation where appropriate
- localStorage for persistence
- No build step required for development

## Colors (Theme)

```css
--bg-dark: #18181C;      /* Main background */
--bg-card: #1f1f24;      /* Card backgrounds */
--bg-input: #2a2a30;     /* Input fields */
--border: #3F465B;       /* Borders */
--accent: #C52638;       /* Red accent */
--accent-hover: #d63344; /* Hover state */
--text-primary: #ffffff; /* Primary text */
--text-secondary: #a0a0a8; /* Secondary text */
--text-muted: #6b6b73;   /* Muted text */
```

## Known Issues

- node-pty "AttachConsole failed" warnings on Windows (non-fatal)
- Layout switching from 2H/2V to 4 may have positioning issues
- Electron cache warnings on startup (cosmetic)
