// Iframe Bridge - Provides electronAPI proxy when running inside dashboard iframe
// This allows content pages to call Electron APIs via postMessage to the parent dashboard

(function() {
    'use strict';

    const isInIframe = window.parent !== window;

    // If not in iframe, or already have electronAPI, do nothing
    if (!isInIframe) return;

    // Hide nav ribbon when in iframe (dashboard has its own)
    document.addEventListener('DOMContentLoaded', () => {
        const nav = document.querySelector('.nav-ribbon');
        if (nav) {
            nav.style.display = 'none';
        }
        // Remove body padding that was for the nav
        document.body.style.paddingTop = '0';
    });

    // If we already have electronAPI from preload, keep using it
    if (window.electronAPI) return;

    // Pending promise resolvers for async API calls
    const pendingCalls = new Map();

    // Listen for responses from parent
    window.addEventListener('message', (event) => {
        if (event.data && event.data.type === 'electronAPI-response') {
            const { id, result, error } = event.data;
            const pending = pendingCalls.get(id);
            if (pending) {
                pendingCalls.delete(id);
                if (error) {
                    pending.reject(new Error(error));
                } else {
                    pending.resolve(result);
                }
            }
        }
    });

    // Helper to send API call to parent and wait for response
    function callParentAPI(method, args = []) {
        return new Promise((resolve, reject) => {
            const id = Math.random().toString(36).substring(2) + Date.now();
            pendingCalls.set(id, { resolve, reject });
            window.parent.postMessage({
                type: 'electronAPI',
                id,
                method,
                args
            }, '*');

            // Timeout after 30 seconds
            setTimeout(() => {
                if (pendingCalls.has(id)) {
                    pendingCalls.delete(id);
                    reject(new Error('API call timeout: ' + method));
                }
            }, 30000);
        });
    }

    // Create proxy electronAPI
    window.electronAPI = {
        window: {
            minimize: () => callParentAPI('window.minimize'),
            maximize: () => callParentAPI('window.maximize'),
            close: () => callParentAPI('window.close'),
            openTerminal: () => callParentAPI('window.openTerminal'),
            openDevTools: () => callParentAPI('window.openDevTools')
        },
        dialog: {
            openAudioFiles: () => callParentAPI('dialog.openAudioFiles')
        },
        sound: {
            onPlayDone: (callback) => {
                // Listen for sound:playDone events forwarded from parent
                window.addEventListener('message', (event) => {
                    if (event.data && event.data.type === 'sound:playDone') {
                        callback();
                    }
                });
            }
        },
        log: {
            write: (level, source, message, data) => callParentAPI('log.write', [level, source, message, data]),
            error: (source, message, data) => callParentAPI('log.error', [source, message, data]),
            warn: (source, message, data) => callParentAPI('log.warn', [source, message, data]),
            info: (source, message, data) => callParentAPI('log.info', [source, message, data]),
            debug: (source, message, data) => callParentAPI('log.debug', [source, message, data]),
            clear: () => callParentAPI('log.clear'),
            read: () => callParentAPI('log.read')
        },
        platform: 'win32', // Will be updated by parent
        isElectron: true
    };

    // Request platform info from parent
    window.parent.postMessage({ type: 'getPlatform' }, '*');
    window.addEventListener('message', (event) => {
        if (event.data && event.data.type === 'platform') {
            window.electronAPI.platform = event.data.platform;
        }
    });
})();
