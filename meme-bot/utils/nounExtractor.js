const nlp = require('compromise');

// Words to skip (common/boring nouns, pronouns, etc.)
const SKIP_WORDS = new Set([
    'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
    'this', 'that', 'these', 'those', 'what', 'which', 'who', 'whom',
    'thing', 'things', 'stuff', 'way', 'ways', 'time', 'times',
    'people', 'person', 'man', 'woman', 'guy', 'guys', 'one', 'ones',
    'something', 'anything', 'nothing', 'everything',
    'someone', 'anyone', 'everyone', 'nobody',
    'lot', 'lots', 'bit', 'kind', 'type', 'sort',
    'day', 'days', 'week', 'month', 'year',
    'today', 'tomorrow', 'yesterday',
    'place', 'places', 'part', 'parts',
    'fact', 'point', 'case', 'example',
    'question', 'answer', 'problem', 'issue',
    'idea', 'thought', 'opinion',
    'thanks', 'thank', 'please', 'sorry',
    'yes', 'no', 'ok', 'okay', 'yeah', 'yep', 'nope',
    'hey', 'hi', 'hello', 'bye', 'goodbye',
    'lol', 'lmao', 'haha', 'hehe', 'omg', 'wtf', 'brb'
]);

// Good meme-worthy noun categories
const MEME_WORTHY = new Set([
    'animal', 'animals', 'cat', 'cats', 'dog', 'dogs', 'bird', 'birds',
    'food', 'pizza', 'coffee', 'beer', 'wine', 'cake', 'burger',
    'monday', 'friday', 'weekend',
    'boss', 'meeting', 'work', 'job', 'office', 'deadline',
    'party', 'dance', 'music', 'movie', 'game',
    'money', 'cash', 'success', 'fail', 'failure', 'win', 'winner', 'loser',
    'sleep', 'nap', 'bed', 'morning', 'night',
    'rain', 'snow', 'sun', 'weather',
    'baby', 'kid', 'kids', 'children',
    'love', 'hate', 'happy', 'sad', 'angry', 'excited', 'bored',
    'computer', 'phone', 'internet', 'wifi',
    'car', 'traffic', 'drive', 'driving'
]);

function extractNouns(text) {
    if (!text || typeof text !== 'string') {
        return [];
    }

    // Clean up Teams mentions and special chars
    const cleanText = text
        .replace(/<at>.*?<\/at>/gi, '') // Remove Teams mentions
        .replace(/@\w+/g, '')           // Remove @mentions
        .replace(/https?:\/\/\S+/g, '') // Remove URLs
        .replace(/[^\w\s'-]/g, ' ')     // Remove special chars
        .trim();

    if (!cleanText) {
        return [];
    }

    // Use compromise NLP to extract nouns
    const doc = nlp(cleanText);

    // Get all nouns
    const nouns = doc.nouns().out('array');

    // Also get topics/entities which can be good meme material
    const topics = doc.topics().out('array');

    // Combine and process
    const allNouns = [...new Set([...nouns, ...topics])];

    const filtered = allNouns
        .map(n => n.toLowerCase().trim())
        .filter(n => n.length >= 3)                    // At least 3 chars
        .filter(n => n.length <= 20)                   // Not too long
        .filter(n => !SKIP_WORDS.has(n))              // Not boring
        .filter(n => !/^\d+$/.test(n));               // Not just numbers

    // Prioritize meme-worthy nouns
    const memeWorthy = filtered.filter(n => MEME_WORTHY.has(n));
    const others = filtered.filter(n => !MEME_WORTHY.has(n));

    // Return meme-worthy first, then others
    return [...memeWorthy, ...others];
}

module.exports = { extractNouns };
