// Shared Navigation JavaScript
// Include this in all pages for consistent nav behavior

const NAV_PAGES = [
    { id: 'home', label: '&#x2302; Home', href: 'splash.html', class: 'home-btn', draggable: false },
    { id: 'memes', label: 'Memes', href: 'meme.html', class: 'meme-btn', draggable: true },
    { id: 'whiteboard', label: 'Whiteboard', href: 'whiteboard.html', class: 'whiteboard-btn', draggable: true },
    { id: 'kabuki', label: 'Kabuki', href: 'kabuki.html', class: 'kabuki-btn', draggable: true },
    { id: 'arcade', label: 'Arcade', href: 'arcade.html', class: 'arcade-btn', draggable: true },
    { id: 'soundboard', label: 'Soundboard', href: 'soundboard.html', class: 'soundboard-btn', draggable: true },
    { id: 'ronin', label: '⚔️ Rōnin', href: 'ronin.html', class: 'ronin-btn', draggable: true },
    { id: 'terminal', label: '&gt;_ Terminal', action: 'openTerminal', class: 'terminal-btn', draggable: true },
    { id: 'music', label: '&#9835; ō-Amp', action: 'togglePlayer', class: 'music-btn', draggable: true }
];

// Get current page ID from filename
function getCurrentPageId() {
    const path = window.location.pathname;
    const filename = path.substring(path.lastIndexOf('/') + 1);

    if (filename === 'splash.html' || filename === '') return 'home';
    if (filename === 'meme.html') return 'memes';
    if (filename === 'whiteboard.html') return 'whiteboard';
    if (filename === 'kabuki.html') return 'kabuki';
    if (filename === 'arcade.html') return 'arcade';
    if (filename === 'soundboard.html') return 'soundboard';
    if (filename === 'ronin.html') return 'ronin';
    if (filename === 'terminals.html') return 'terminal';
    return null;
}

// Build the navigation HTML
function buildNavHTML(currentPageId) {
    const savedOrder = localStorage.getItem('nav_button_order');
    let pages = [...NAV_PAGES];

    // Reorder based on saved preferences (only draggable items)
    if (savedOrder) {
        try {
            const order = JSON.parse(savedOrder);
            const homeBtn = pages.find(p => p.id === 'home');
            const draggablePages = pages.filter(p => p.draggable);
            const reordered = [];

            // Add items in saved order
            order.forEach(id => {
                const page = draggablePages.find(p => p.id === id);
                if (page) reordered.push(page);
            });

            // Add any new items not in saved order
            draggablePages.forEach(page => {
                if (!reordered.includes(page)) reordered.push(page);
            });

            pages = [homeBtn, ...reordered];
        } catch (e) {
            console.error('Failed to load nav order:', e);
        }
    }

    let html = `
    <nav class="nav-ribbon">
        <div class="nav-left" id="navButtonContainer">
            <span class="nav-brand"><span>ō</span>-face</span>`;

    pages.forEach(page => {
        const isActive = page.id === currentPageId;
        const draggable = page.draggable ? 'draggable="true"' : '';
        const dataBtnId = page.draggable ? `data-btn-id="${page.id}"` : '';

        let onclick = '';
        if (page.href) {
            onclick = `onclick="navGoTo('${page.href}')"`;
        } else if (page.action) {
            onclick = `onclick="${page.action}()"`;
        }

        html += `<button class="nav-btn ${page.class}${isActive ? ' active' : ''}" ${draggable} ${dataBtnId} ${onclick}>${page.label}</button>`;
    });

    html += `
        </div>
        <div class="nav-right">
            <button class="window-btn" onclick="navMinimize()">&#x2212;</button>
            <button class="window-btn" onclick="navMaximize()">&#x25A1;</button>
            <button class="window-btn close" onclick="navClose()">&#x2715;</button>
        </div>
    </nav>`;

    return html;
}

// Navigation functions
function navGoTo(href) {
    // Check if we're in an iframe inside the dashboard
    const isInIframe = window.parent !== window;

    if (isInIframe) {
        // Tell parent dashboard to navigate
        window.parent.postMessage({
            type: 'navigate',
            href: href,
            pageId: getPageIdFromHref(href)
        }, '*');
    } else {
        // Direct navigation (standalone mode)
        window.location.href = href;
    }
}

// Get page ID from href for navigation
function getPageIdFromHref(href) {
    if (href === 'meme.html') return 'memes';
    if (href === 'whiteboard.html') return 'whiteboard';
    if (href === 'kabuki.html') return 'kabuki';
    if (href === 'arcade.html') return 'arcade';
    if (href === 'soundboard.html') return 'soundboard';
    if (href === 'ronin.html') return 'ronin';
    if (href === 'splash.html' || href === 'dashboard.html') return 'home';
    return null;
}

function navMinimize() {
    if (window.electronAPI) window.electronAPI.window.minimize();
}

function navMaximize() {
    if (window.electronAPI) window.electronAPI.window.maximize();
}

function navClose() {
    if (window.electronAPI) window.electronAPI.window.close();
}

// Default implementations (can be overridden by page)
function openTerminal() {
    if (window.electronAPI) {
        window.electronAPI.window.openTerminal();
    }
}

function togglePlayer() {
    // Override in pages that have the music player
    console.log('Music player not available on this page');
}

// Initialize drag-and-drop for nav buttons
function initNavDragDrop() {
    const container = document.getElementById('navButtonContainer');
    if (!container) return;

    const buttons = container.querySelectorAll('.nav-btn[draggable="true"]');
    let draggedBtn = null;

    buttons.forEach(btn => {
        btn.addEventListener('dragstart', (e) => {
            draggedBtn = btn;
            btn.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/plain', btn.dataset.btnId);
        });

        btn.addEventListener('dragend', () => {
            btn.classList.remove('dragging');
            draggedBtn = null;
            buttons.forEach(b => b.classList.remove('drag-over'));
            saveNavOrder();
        });

        btn.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            if (draggedBtn && draggedBtn !== btn) {
                btn.classList.add('drag-over');
            }
        });

        btn.addEventListener('dragleave', () => {
            btn.classList.remove('drag-over');
        });

        btn.addEventListener('drop', (e) => {
            e.preventDefault();
            btn.classList.remove('drag-over');
            if (draggedBtn && draggedBtn !== btn) {
                const allBtns = [...container.querySelectorAll('.nav-btn[draggable="true"]')];
                const draggedIndex = allBtns.indexOf(draggedBtn);
                const dropIndex = allBtns.indexOf(btn);

                if (draggedIndex < dropIndex) {
                    btn.parentNode.insertBefore(draggedBtn, btn.nextSibling);
                } else {
                    btn.parentNode.insertBefore(draggedBtn, btn);
                }
            }
        });
    });
}

// Save nav button order to localStorage
function saveNavOrder() {
    const container = document.getElementById('navButtonContainer');
    if (!container) return;

    const buttons = container.querySelectorAll('.nav-btn[draggable="true"]');
    const order = [...buttons].map(btn => btn.dataset.btnId);
    localStorage.setItem('nav_button_order', JSON.stringify(order));
}

// Terminal fire effect
function initTerminalFireEffect() {
    const terminalBtn = document.querySelector('.nav-btn.terminal-btn');
    if (!terminalBtn) return;

    function ignite() {
        terminalBtn.classList.add('on-fire');
        setTimeout(() => {
            terminalBtn.classList.remove('on-fire');
        }, 3000);
    }

    setInterval(ignite, 30000);
    setTimeout(ignite, 2000);
}

// Initialize navigation
function initNav() {
    // Hide window controls if not in Electron
    if (typeof window.electronAPI === 'undefined') {
        const navRight = document.querySelector('.nav-right');
        if (navRight) navRight.style.display = 'none';
    }

    initNavDragDrop();
    initTerminalFireEffect();
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initNav);
