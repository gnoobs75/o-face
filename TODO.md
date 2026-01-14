# o-face Feature Roadmap

## Priority: High

### Terminal Improvements
- [ ] Fix layout switching bug (2H/2V to 4 panes positioning)
- [ ] Add terminal tabs within each pane
- [ ] Terminal history/scrollback buffer
- [ ] Copy/paste keyboard shortcuts (Ctrl+Shift+C/V)
- [ ] Split pane within pane (nested splits)
- [ ] Save/restore terminal sessions
- [ ] Custom shell commands/aliases

### Audio Notifications
- [ ] Configurable notification sounds
- [ ] Volume control
- [ ] Mute toggle
- [ ] Different sounds for different events
- [ ] Custom sound upload

---

## Priority: Medium

### WinAmp-Style Music Player
- [ ] Classic WinAmp skin aesthetic
- [ ] Playlist support (local files or URLs)
- [ ] EQ visualizer bars
- [ ] Oscilloscope visualization
- [ ] Spectrum analyzer
- [ ] Drag-and-drop music files
- [ ] Mini mode / full mode toggle
- [ ] Skinnable interface

### Retro Game Emulator
- [ ] NES emulator (JSNes)
- [ ] GameBoy emulator
- [ ] SNES emulator
- [ ] ROM file browser
- [ ] Save states
- [ ] Controller mapping
- [ ] Fullscreen mode

### Claude Integration
- [ ] Embedded Claude chat widget
- [ ] API key management (secure storage)
- [ ] Chat history persistence
- [ ] Quick prompts/templates
- [ ] Integration with terminal (run commands from chat)

---

## Priority: Fun (MySpace Vibes)

### Visual Effects
- [ ] Custom cursor themes
- [ ] Mouse sparkle/glitter trail
- [ ] Matrix falling code background
- [ ] Starfield background
- [ ] Snow/confetti effects
- [ ] Animated background patterns

### Social Features
- [ ] Visitor counter ("You are visitor #12345")
- [ ] Guestbook (localStorage or simple backend)
- [ ] Top 8 Friends grid
- [ ] Mood status indicator
- [ ] Away message / status
- [ ] Profile song (auto-play audio)

### Decorative Elements
- [ ] Blinkies / animated badges
- [ ] Under construction GIF
- [ ] Marquee scrolling announcements
- [ ] Glitter text generator
- [ ] ASCII art section
- [ ] "Now Playing" widget

---

## Technical Improvements

### Performance
- [ ] Lazy load terminals (only create when needed)
- [ ] Reduce xterm.js bundle size
- [ ] Optimize canvas rendering
- [ ] Memory management for long sessions

### Cross-Platform
- [ ] Mac keyboard shortcuts (Cmd vs Ctrl)
- [ ] Mac traffic light window buttons
- [ ] Linux testing and fixes
- [ ] Platform-specific theming

### Build & Distribution
- [ ] Electron Builder setup
- [ ] Windows installer (NSIS/MSI)
- [ ] Mac DMG builder
- [ ] Auto-updater
- [ ] Code signing

### Settings & Configuration
- [ ] Settings panel UI
- [ ] Theme customization
- [ ] Font selection
- [ ] Terminal preferences
- [ ] Startup behavior options
- [ ] Export/import all settings

---

## API Integrations to Explore

- [ ] Giphy API (alternative GIF source)
- [ ] Tenor API (more GIFs)
- [ ] Spotify API (music integration)
- [ ] Last.fm API (scrobbling)
- [ ] Weather API (retro weather widget)
- [ ] RSS feed reader
- [ ] Discord presence integration
- [ ] Twitch stream status

---

## Crazy Ideas

- [ ] Built-in IRC client
- [ ] BBS-style bulletin board
- [ ] Peer-to-peer chat (WebRTC)
- [ ] Screen sharing between panes
- [ ] Voice commands
- [ ] AI-generated retro graphics
- [ ] Virtual pet (Tamagotchi style)
- [ ] Achievement system
- [ ] Easter eggs and secrets

---

## Completed

- [x] GIF search with Klipy API
- [x] Meme generator with Imgflip templates
- [x] Favorites system with export/import
- [x] Lightbox with copy functionality
- [x] Retro flaming text
- [x] Electron app wrapper
- [x] Multi-pane terminal (1/2H/2V/4)
- [x] Terminal attention notifications
- [x] Keyboard navigation between panes
- [x] Cross-platform shell detection
