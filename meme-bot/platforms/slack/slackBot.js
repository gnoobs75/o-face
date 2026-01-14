const { App } = require('@slack/bolt');
const { MemeEngine } = require('../../core/memeEngine');
const {
    formatMemeBlocks,
    formatWelcomeBlocks,
    formatErrorBlocks,
    formatHelpBlocks
} = require('./slackFormatter');

class SlackMemeBoss {
    constructor() {
        this.memeEngine = new MemeEngine();
        this.app = null;
    }

    /**
     * Initialize the Slack app
     */
    init() {
        this.app = new App({
            token: process.env.SLACK_BOT_TOKEN,
            signingSecret: process.env.SLACK_SIGNING_SECRET,
            socketMode: true,
            appToken: process.env.SLACK_APP_TOKEN
        });

        this.registerEventHandlers();
        this.registerCommands();

        return this;
    }

    /**
     * Register event handlers for messages
     */
    registerEventHandlers() {
        // Handle direct mentions
        this.app.event('app_mention', async ({ event, say }) => {
            console.log(`[Slack] Mentioned by ${event.user}: ${event.text}`);

            try {
                const { meme, searchTerm } = await this.memeEngine.getMemeForMessage(event.text);

                if (meme) {
                    await say({
                        blocks: formatMemeBlocks(meme, searchTerm, event.user),
                        text: `Meme for "${searchTerm}"` // Fallback text
                    });
                } else {
                    // Try trending if no relevant meme found
                    const trending = await this.memeEngine.getTrendingMeme();
                    if (trending) {
                        await say({
                            blocks: formatMemeBlocks(trending, 'trending', event.user),
                            text: 'Here\'s a trending meme!'
                        });
                    } else {
                        await say({
                            blocks: formatErrorBlocks('Couldn\'t find a meme right now. Try again later!'),
                            text: 'Couldn\'t find a meme'
                        });
                    }
                }
            } catch (error) {
                console.error('[Slack] Error handling mention:', error);
            }
        });

        // Handle channel messages (passive listening)
        this.app.message(async ({ message, say }) => {
            // Skip bot messages and threads
            if (message.subtype || message.thread_ts) return;

            const channelId = message.channel;
            const { shouldRespond, reason } = this.memeEngine.shouldRespond(channelId);

            console.log(`[Slack] Message in ${channelId} - shouldRespond: ${shouldRespond} (${reason})`);

            if (!shouldRespond) return;

            try {
                const { meme, searchTerm } = await this.memeEngine.getMemeForMessage(message.text);

                if (meme) {
                    this.memeEngine.recordResponse(channelId);
                    await say({
                        blocks: formatMemeBlocks(meme, searchTerm, message.user),
                        text: `Meme for "${searchTerm}"`
                    });
                }
            } catch (error) {
                console.error('[Slack] Error handling message:', error);
            }
        });

        // Handle bot joining a channel
        this.app.event('member_joined_channel', async ({ event, say }) => {
            // Check if it's the bot that joined
            if (event.user === this.app.client.auth?.user_id) {
                try {
                    await say({
                        blocks: formatWelcomeBlocks(),
                        text: 'Hey there! I\'m MemeBoss!'
                    });
                } catch (error) {
                    console.error('[Slack] Error sending welcome:', error);
                }
            }
        });
    }

    /**
     * Register slash commands
     */
    registerCommands() {
        // /meme command
        this.app.command('/meme', async ({ command, ack, respond }) => {
            await ack();
            console.log(`[Slack] /meme command from ${command.user_name}: ${command.text}`);

            try {
                const query = command.text.trim();
                let meme;

                if (query) {
                    meme = await this.memeEngine.searchMeme(query);
                } else {
                    meme = await this.memeEngine.getTrendingMeme();
                }

                if (meme) {
                    await respond({
                        response_type: 'in_channel',
                        blocks: formatMemeBlocks(meme, query || 'random', command.user_name),
                        text: `Meme for "${query || 'random'}"`
                    });
                } else {
                    await respond({
                        blocks: formatErrorBlocks(`Couldn't find a meme for "${query}". Try a different topic!`),
                        text: 'No meme found'
                    });
                }
            } catch (error) {
                console.error('[Slack] Error handling /meme:', error);
                await respond({
                    blocks: formatErrorBlocks('Something went wrong. Try again!'),
                    text: 'Error'
                });
            }
        });

        // /trending command
        this.app.command('/trending', async ({ command, ack, respond }) => {
            await ack();
            console.log(`[Slack] /trending command from ${command.user_name}`);

            try {
                const meme = await this.memeEngine.getTrendingMeme();

                if (meme) {
                    await respond({
                        response_type: 'in_channel',
                        blocks: formatMemeBlocks(meme, 'trending', command.user_name),
                        text: 'Trending meme'
                    });
                } else {
                    await respond({
                        blocks: formatErrorBlocks('Couldn\'t fetch trending memes right now.'),
                        text: 'No trending memes'
                    });
                }
            } catch (error) {
                console.error('[Slack] Error handling /trending:', error);
                await respond({
                    blocks: formatErrorBlocks('Something went wrong. Try again!'),
                    text: 'Error'
                });
            }
        });

        // /meme-help command
        this.app.command('/meme-help', async ({ ack, respond }) => {
            await ack();

            await respond({
                blocks: formatHelpBlocks(),
                text: 'MemeBoss Help'
            });
        });
    }

    /**
     * Start the Slack bot
     */
    async start() {
        const port = process.env.SLACK_PORT || 3000;
        await this.app.start(port);
        console.log(`\n=================================`);
        console.log(`   MEME BOSS SLACK is running!`);
        console.log(`   Socket Mode: Active`);
        console.log(`=================================\n`);
    }
}

module.exports = { SlackMemeBoss };
