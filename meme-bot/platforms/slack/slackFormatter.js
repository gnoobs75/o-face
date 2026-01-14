/**
 * Slack Block Kit message formatter for memes
 */

/**
 * Create a meme response in Slack Block Kit format
 * @param {object} meme - The meme object from Klipy
 * @param {string} searchTerm - The term that was searched
 * @param {string} userName - The user who triggered the response
 * @returns {object[]} Slack blocks array
 */
function formatMemeBlocks(meme, searchTerm, userName) {
    return [
        {
            type: 'context',
            elements: [
                {
                    type: 'mrkdwn',
                    text: `*@${userName}* - _"${searchTerm}"_`
                }
            ]
        },
        {
            type: 'image',
            image_url: meme.url,
            alt_text: meme.description || searchTerm
        },
        {
            type: 'context',
            elements: [
                {
                    type: 'mrkdwn',
                    text: `<${meme.sourceUrl}|View on Klipy> | Powered by Klipy`
                }
            ]
        }
    ];
}

/**
 * Create a welcome message for new channels
 * @returns {object[]} Slack blocks array
 */
function formatWelcomeBlocks() {
    return [
        {
            type: 'section',
            text: {
                type: 'mrkdwn',
                text: '*Hey there!* I\'m MemeBoss :sunglasses:'
            }
        },
        {
            type: 'section',
            text: {
                type: 'mrkdwn',
                text: 'I\'ll drop relevant memes from time to time based on what you\'re talking about. Mention me directly for a meme on demand!'
            }
        },
        {
            type: 'context',
            elements: [
                {
                    type: 'mrkdwn',
                    text: ':zap: `/meme [topic]` - Get a meme on a specific topic\n:fire: `/trending` - Get a trending meme'
                }
            ]
        }
    ];
}

/**
 * Create an error message
 * @param {string} message - Error message to display
 * @returns {object[]} Slack blocks array
 */
function formatErrorBlocks(message) {
    return [
        {
            type: 'section',
            text: {
                type: 'mrkdwn',
                text: `:disappointed: ${message}`
            }
        }
    ];
}

/**
 * Create a help message
 * @returns {object[]} Slack blocks array
 */
function formatHelpBlocks() {
    return [
        {
            type: 'header',
            text: {
                type: 'plain_text',
                text: 'MemeBoss Help',
                emoji: true
            }
        },
        {
            type: 'section',
            text: {
                type: 'mrkdwn',
                text: '*How I work:*\nI listen to conversations and occasionally drop relevant memes based on what you\'re talking about. The more interesting the topic, the better the meme!'
            }
        },
        {
            type: 'divider'
        },
        {
            type: 'section',
            text: {
                type: 'mrkdwn',
                text: '*Commands:*'
            }
        },
        {
            type: 'section',
            fields: [
                {
                    type: 'mrkdwn',
                    text: '`@MemeBoss [topic]`\nMention me for a meme'
                },
                {
                    type: 'mrkdwn',
                    text: '`/meme [topic]`\nSlash command for memes'
                },
                {
                    type: 'mrkdwn',
                    text: '`/trending`\nGet a trending meme'
                },
                {
                    type: 'mrkdwn',
                    text: '`/meme-help`\nShow this help'
                }
            ]
        },
        {
            type: 'context',
            elements: [
                {
                    type: 'mrkdwn',
                    text: 'Powered by Klipy | Made with :heart:'
                }
            ]
        }
    ];
}

module.exports = {
    formatMemeBlocks,
    formatWelcomeBlocks,
    formatErrorBlocks,
    formatHelpBlocks
};
