const TENOR_API_KEY = process.env.TENOR_API_KEY;
const CLIENT_KEY = 'memeboss-teams-bot';

async function searchMeme(query) {
    if (!TENOR_API_KEY) {
        console.error('[Tenor] No API key configured!');
        return null;
    }

    try {
        const url = new URL('https://tenor.googleapis.com/v2/search');
        url.searchParams.set('q', query);
        url.searchParams.set('key', TENOR_API_KEY);
        url.searchParams.set('client_key', CLIENT_KEY);
        url.searchParams.set('limit', '20');
        url.searchParams.set('media_filter', 'gif,tinygif');
        url.searchParams.set('contentfilter', 'medium'); // Safe for work

        const response = await fetch(url.toString());
        const data = await response.json();

        if (data.error) {
            console.error('[Tenor] API Error:', data.error);
            return null;
        }

        const results = data.results || [];

        if (results.length === 0) {
            return null;
        }

        // Pick a random result from top 20
        const gif = results[Math.floor(Math.random() * results.length)];

        // Get the best format available
        const formats = gif.media_formats;
        const gifUrl = formats.gif?.url || formats.tinygif?.url || formats.mediumgif?.url;

        return {
            url: gifUrl,
            description: gif.content_description || query,
            tenorUrl: gif.itemurl || `https://tenor.com/search/${encodeURIComponent(query)}-gifs`
        };

    } catch (error) {
        console.error('[Tenor] Fetch error:', error);
        return null;
    }
}

async function getTrending(limit = 10) {
    if (!TENOR_API_KEY) {
        return [];
    }

    try {
        const url = new URL('https://tenor.googleapis.com/v2/featured');
        url.searchParams.set('key', TENOR_API_KEY);
        url.searchParams.set('client_key', CLIENT_KEY);
        url.searchParams.set('limit', limit.toString());
        url.searchParams.set('media_filter', 'gif,tinygif');

        const response = await fetch(url.toString());
        const data = await response.json();

        return data.results || [];

    } catch (error) {
        console.error('[Tenor] Trending fetch error:', error);
        return [];
    }
}

module.exports = { searchMeme, getTrending };
