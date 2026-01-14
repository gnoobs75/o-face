require('dotenv').config();

const enableTeams = process.env.ENABLE_TEAMS !== 'false';
const enableSlack = process.env.ENABLE_SLACK !== 'false';

console.log('\n========================================');
console.log('          MEME BOSS STARTING');
console.log('========================================');
console.log(`  Teams: ${enableTeams ? 'ENABLED' : 'DISABLED'}`);
console.log(`  Slack: ${enableSlack ? 'ENABLED' : 'DISABLED'}`);
console.log('========================================\n');

// Validate required config
if (!process.env.KLIPY_API_KEY) {
    console.error('[ERROR] KLIPY_API_KEY is required! Get one from https://klipy.com/developers');
    process.exit(1);
}

async function startTeams() {
    const restify = require('restify');
    const { CloudAdapter, ConfigurationBotFrameworkAuthentication } = require('botbuilder');
    const { TeamsMemeBoss } = require('./platforms/teams/teamsBot');

    // Validate Teams config
    if (!process.env.MICROSOFT_APP_ID || !process.env.MICROSOFT_APP_PASSWORD) {
        console.error('[Teams] Missing MICROSOFT_APP_ID or MICROSOFT_APP_PASSWORD');
        console.error('[Teams] Skipping Teams initialization...');
        return;
    }

    const botFrameworkAuth = new ConfigurationBotFrameworkAuthentication({
        MicrosoftAppId: process.env.MICROSOFT_APP_ID,
        MicrosoftAppPassword: process.env.MICROSOFT_APP_PASSWORD,
        MicrosoftAppTenantId: process.env.MICROSOFT_APP_TENANT_ID,
        MicrosoftAppType: process.env.MICROSOFT_APP_TYPE || 'MultiTenant'
    });

    const adapter = new CloudAdapter(botFrameworkAuth);

    adapter.onTurnError = async (context, error) => {
        console.error(`[Teams Error] ${error}`);
        await context.sendActivity('Oops! Something went wrong.');
    };

    const bot = new TeamsMemeBoss();

    const server = restify.createServer();
    server.use(restify.plugins.bodyParser());

    server.post('/api/messages', async (req, res) => {
        await adapter.process(req, res, (context) => bot.run(context));
    });

    const port = process.env.PORT || 3978;
    server.listen(port, () => {
        console.log(`[Teams] Listening on http://localhost:${port}/api/messages`);
    });
}

async function startSlack() {
    const { SlackMemeBoss } = require('./platforms/slack/slackBot');

    // Validate Slack config
    if (!process.env.SLACK_BOT_TOKEN || !process.env.SLACK_SIGNING_SECRET || !process.env.SLACK_APP_TOKEN) {
        console.error('[Slack] Missing SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET, or SLACK_APP_TOKEN');
        console.error('[Slack] Skipping Slack initialization...');
        return;
    }

    try {
        const slackBot = new SlackMemeBoss();
        slackBot.init();
        await slackBot.start();
    } catch (error) {
        console.error('[Slack] Failed to start:', error);
    }
}

async function main() {
    const startups = [];

    if (enableTeams) {
        startups.push(startTeams());
    }

    if (enableSlack) {
        startups.push(startSlack());
    }

    if (startups.length === 0) {
        console.error('[ERROR] No platforms enabled! Set ENABLE_TEAMS=true or ENABLE_SLACK=true');
        process.exit(1);
    }

    await Promise.all(startups);

    console.log('\n[MemeBoss] All platforms started successfully!');
}

main().catch(err => {
    console.error('[FATAL]', err);
    process.exit(1);
});
