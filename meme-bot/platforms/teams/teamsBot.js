const { ActivityHandler, CardFactory } = require('botbuilder');
const { MemeEngine } = require('../../core/memeEngine');

class TeamsMemeBoss extends ActivityHandler {
    constructor() {
        super();
        this.memeEngine = new MemeEngine();

        // Handle incoming messages
        this.onMessage(async (context, next) => {
            const text = context.activity.text || '';
            const channelId = context.activity.conversation.id;
            const userName = context.activity.from.name || 'friend';

            console.log(`[Teams] ${userName}: ${text}`);

            // Check for commands
            const cleanText = this.stripMentions(text);
            const command = this.parseCommand(cleanText);

            if (command) {
                await this.handleCommand(context, command, userName);
                return await next();
            }

            // Check if bot is mentioned directly
            const isMentioned = context.activity.entities?.some(
                e => e.type === 'mention' && e.mentioned?.id === context.activity.recipient.id
            );

            if (isMentioned) {
                await this.respondWithMeme(context, cleanText, userName, true);
                return await next();
            }

            // Passive listening with random response
            const { shouldRespond, reason } = this.memeEngine.shouldRespond(channelId);
            console.log(`[Teams] shouldRespond: ${shouldRespond} (${reason})`);

            if (shouldRespond) {
                await this.respondWithMeme(context, text, userName, false);
                this.memeEngine.recordResponse(channelId);
            }

            await next();
        });

        // Handle new members
        this.onMembersAdded(async (context, next) => {
            for (const member of context.activity.membersAdded) {
                if (member.id !== context.activity.recipient.id) {
                    const card = this.createWelcomeCard(member.name || 'there');
                    await context.sendActivity({ attachments: [card] });
                }
            }
            await next();
        });
    }

    /**
     * Strip Teams mentions from text
     */
    stripMentions(text) {
        return text
            .replace(/<at>.*?<\/at>/gi, '')
            .replace(/@\w+/g, '')
            .trim();
    }

    /**
     * Parse command from text
     */
    parseCommand(text) {
        const lower = text.toLowerCase().trim();

        if (lower.startsWith('meme ')) {
            return { type: 'meme', query: text.slice(5).trim() };
        }
        if (lower === 'meme') {
            return { type: 'meme', query: '' };
        }
        if (lower === 'trending') {
            return { type: 'trending' };
        }
        if (lower === 'help') {
            return { type: 'help' };
        }

        return null;
    }

    /**
     * Handle bot commands
     */
    async handleCommand(context, command, userName) {
        switch (command.type) {
            case 'meme': {
                let meme;
                if (command.query) {
                    meme = await this.memeEngine.searchMeme(command.query);
                } else {
                    meme = await this.memeEngine.getTrendingMeme();
                }

                if (meme) {
                    const card = this.createMemeCard(meme, command.query || 'random', userName);
                    await context.sendActivity({ attachments: [card] });
                } else {
                    await context.sendActivity(`Couldn't find a meme for "${command.query}". Try something else!`);
                }
                break;
            }

            case 'trending': {
                const meme = await this.memeEngine.getTrendingMeme();
                if (meme) {
                    const card = this.createMemeCard(meme, 'trending', userName);
                    await context.sendActivity({ attachments: [card] });
                } else {
                    await context.sendActivity('Couldn\'t fetch trending memes right now.');
                }
                break;
            }

            case 'help': {
                const card = this.createHelpCard();
                await context.sendActivity({ attachments: [card] });
                break;
            }
        }
    }

    /**
     * Respond with a meme based on message content
     */
    async respondWithMeme(context, text, userName, forced) {
        try {
            const { meme, searchTerm } = await this.memeEngine.getMemeForMessage(text);

            if (meme) {
                const card = this.createMemeCard(meme, searchTerm, userName);
                await context.sendActivity({ attachments: [card] });
            } else if (forced) {
                // If forced (mentioned) but no nouns found, try trending
                const trending = await this.memeEngine.getTrendingMeme();
                if (trending) {
                    const card = this.createMemeCard(trending, 'trending', userName);
                    await context.sendActivity({ attachments: [card] });
                }
            }
        } catch (error) {
            console.error('[Teams] Error responding with meme:', error);
        }
    }

    /**
     * Create an Adaptive Card for a meme
     */
    createMemeCard(meme, searchTerm, userName) {
        return CardFactory.adaptiveCard({
            type: 'AdaptiveCard',
            $schema: 'http://adaptivecards.io/schemas/adaptive-card.json',
            version: '1.4',
            body: [
                {
                    type: 'TextBlock',
                    text: `@${userName} - "${searchTerm}"`,
                    size: 'small',
                    color: 'accent'
                },
                {
                    type: 'Image',
                    url: meme.url,
                    size: 'auto',
                    altText: meme.description || searchTerm
                }
            ],
            actions: [
                {
                    type: 'Action.OpenUrl',
                    title: 'View on Klipy',
                    url: meme.sourceUrl
                }
            ]
        });
    }

    /**
     * Create a welcome card
     */
    createWelcomeCard(userName) {
        return CardFactory.adaptiveCard({
            type: 'AdaptiveCard',
            $schema: 'http://adaptivecards.io/schemas/adaptive-card.json',
            version: '1.4',
            body: [
                {
                    type: 'TextBlock',
                    text: 'MemeBoss',
                    size: 'large',
                    weight: 'bolder',
                    color: 'accent'
                },
                {
                    type: 'TextBlock',
                    text: `Hey ${userName}! I'm MemeBoss. I'll drop relevant memes from time to time based on your conversations. Mention me directly for a meme on demand!`,
                    wrap: true
                },
                {
                    type: 'FactSet',
                    facts: [
                        { title: '@MemeBoss [topic]', value: 'Get a meme' },
                        { title: '@MemeBoss trending', value: 'Get trending meme' },
                        { title: '@MemeBoss help', value: 'Show help' }
                    ]
                }
            ]
        });
    }

    /**
     * Create a help card
     */
    createHelpCard() {
        return CardFactory.adaptiveCard({
            type: 'AdaptiveCard',
            $schema: 'http://adaptivecards.io/schemas/adaptive-card.json',
            version: '1.4',
            body: [
                {
                    type: 'TextBlock',
                    text: 'MemeBoss Help',
                    size: 'large',
                    weight: 'bolder',
                    color: 'accent'
                },
                {
                    type: 'TextBlock',
                    text: 'I listen to conversations and occasionally drop relevant memes based on what you\'re talking about!',
                    wrap: true
                },
                {
                    type: 'TextBlock',
                    text: 'Commands:',
                    weight: 'bolder',
                    spacing: 'medium'
                },
                {
                    type: 'FactSet',
                    facts: [
                        { title: '@MemeBoss meme [topic]', value: 'Search for a specific meme' },
                        { title: '@MemeBoss trending', value: 'Get a trending meme' },
                        { title: '@MemeBoss help', value: 'Show this help' }
                    ]
                },
                {
                    type: 'TextBlock',
                    text: 'Powered by Klipy',
                    size: 'small',
                    isSubtle: true,
                    spacing: 'medium'
                }
            ]
        });
    }
}

module.exports = { TeamsMemeBoss };
