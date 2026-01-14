const { extractNouns } = require('../utils/nounExtractor');
const { searchMeme, getTrending } = require('../services/klipy');

class MemeEngine {
    constructor(options = {}) {
        this.responseChance = options.responseChance ?? parseFloat(process.env.RESPONSE_CHANCE) ?? 0.3;
        this.cooldownMs = options.cooldownMs ?? parseInt(process.env.COOLDOWN_MS) ?? 60000;
        this.lastResponseTime = new Map();
    }

    /**
     * Decide if we should respond to a message
     * @param {string} channelId - Channel identifier
     * @param {boolean} forcedResponse - If true, skip random chance (e.g., direct mention)
     * @returns {{ shouldRespond: boolean, reason: string }}
     */
    shouldRespond(channelId, forcedResponse = false) {
        if (forcedResponse) {
            return { shouldRespond: true, reason: 'forced' };
        }

        const now = Date.now();
        const lastTime = this.lastResponseTime.get(channelId);

        if (lastTime && now - lastTime < this.cooldownMs) {
            return { shouldRespond: false, reason: 'cooldown' };
        }

        if (Math.random() > this.responseChance) {
            return { shouldRespond: false, reason: 'random_skip' };
        }

        return { shouldRespond: true, reason: 'random_hit' };
    }

    /**
     * Record that we responded to a channel
     * @param {string} channelId
     */
    recordResponse(channelId) {
        this.lastResponseTime.set(channelId, Date.now());
    }

    /**
     * Process a message and get a meme response
     * @param {string} text - The message text
     * @returns {Promise<{ meme: object|null, searchTerm: string|null, nouns: string[] }>}
     */
    async getMemeForMessage(text) {
        const nouns = extractNouns(text);
        console.log(`[MemeEngine] Extracted nouns: ${nouns.join(', ') || 'none'}`);

        if (nouns.length === 0) {
            return { meme: null, searchTerm: null, nouns: [] };
        }

        const searchTerm = nouns[Math.floor(Math.random() * nouns.length)];
        console.log(`[MemeEngine] Searching for: "${searchTerm}"`);

        const meme = await searchMeme(searchTerm);

        if (meme) {
            console.log(`[MemeEngine] Found meme: ${meme.url}`);
        } else {
            console.log(`[MemeEngine] No meme found for "${searchTerm}"`);
        }

        return { meme, searchTerm, nouns };
    }

    /**
     * Get a trending meme
     * @returns {Promise<object|null>}
     */
    async getTrendingMeme() {
        const trending = await getTrending(10);
        if (trending.length === 0) return null;

        const item = trending[Math.floor(Math.random() * trending.length)];
        const gifUrl = item.file?.hd?.gif?.url ||
                       item.file?.md?.gif?.url ||
                       item.file?.sm?.gif?.url ||
                       item.file?.hd?.webp?.url;

        return {
            url: gifUrl,
            description: item.title || item.slug || 'Trending meme',
            sourceUrl: item.url || 'https://klipy.com'
        };
    }

    /**
     * Search for a specific meme topic
     * @param {string} query
     * @returns {Promise<object|null>}
     */
    async searchMeme(query) {
        return searchMeme(query);
    }
}

module.exports = { MemeEngine };
