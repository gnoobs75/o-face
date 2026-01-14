const KLIPY_API_KEY = process.env.KLIPY_API_KEY;

async function searchMeme(query, format = 'gifs') {
    if (!KLIPY_API_KEY) {
        console.error('[Klipy] No API key configured!');
        return null;
    }

    try {
        const params = new URLSearchParams({
            q: query,
            per_page: 20,
            rating: 'pg-13'
        });

        const url = `https://api.klipy.com/api/v1/${KLIPY_API_KEY}/${format}/search?${params}`;
        const response = await fetch(url);
        const data = await response.json();

        if (!data.result || !data.data?.data?.length) {
            console.log(`[Klipy] No results for "${query}" in ${format}`);
            return null;
        }

        const results = data.data.data;
        const item = results[Math.floor(Math.random() * results.length)];

        // Extract URL based on format (clips have flat structure, gifs/stickers have nested)
        let gifUrl;
        if (format === 'clips') {
            gifUrl = item.file?.gif || item.file?.webp || item.file?.mp4;
        } else {
            gifUrl = item.file?.hd?.gif?.url ||
                     item.file?.md?.gif?.url ||
                     item.file?.sm?.gif?.url ||
                     item.file?.hd?.webp?.url ||
                     item.file?.md?.webp?.url;
        }

        return {
            url: gifUrl,
            description: item.title || item.slug || query,
            sourceUrl: item.url || `https://klipy.com/search/${encodeURIComponent(query)}`
        };

    } catch (error) {
        console.error('[Klipy] Fetch error:', error);
        return null;
    }
}

async function getTrending(limit = 10, format = 'gifs') {
    if (!KLIPY_API_KEY) {
        return [];
    }

    try {
        const params = new URLSearchParams({
            per_page: limit,
            rating: 'pg-13'
        });

        const url = `https://api.klipy.com/api/v1/${KLIPY_API_KEY}/${format}/trending?${params}`;
        const response = await fetch(url);
        const data = await response.json();

        if (!data.result || !data.data?.data?.length) {
            return [];
        }

        return data.data.data;

    } catch (error) {
        console.error('[Klipy] Trending fetch error:', error);
        return [];
    }
}

module.exports = { searchMeme, getTrending };
