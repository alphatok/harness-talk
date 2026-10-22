# Moltbot Quick Start

Get your private AI sales agent running in 15 minutes.

## Prerequisites

- Docker installed
- Anthropic API key ([get one](https://console.anthropic.com))
- Telegram account (for easiest setup)

## 1. Clone & Configure

```bash
git clone https://github.com/Prospeda/moltbot-pro.git
cd moltbot-pro
cp .env.example .env
```

Edit `.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
```

## 2. Get Telegram Bot Token

1. Open Telegram, search `@BotFather`
2. Send `/newbot`
3. Name your bot
4. Copy token to `.env`

## 3. Deploy

```bash
docker-compose up -d
```

## 4. Connect

1. Message your bot on Telegram
2. Copy the pairing code it gives you
3. Approve:
```bash
docker exec moltbot npx clawdbot pairing approve telegram YOUR_CODE
```

## 5. Test

Send your bot: `hello`

It should respond. You're live.

## What's Next

- Add your sales playbooks to `workspace/playbooks/`
- Connect more channels (Slack, WhatsApp)
- Invite your team
- Read the [full onboarding guide](./PROSPEDA_PRO_ONBOARDING.md)

## Commands

| Command | Description |
|---------|-------------|
| `cop this linkedin` | Transform screenshot to LinkedIn post |
| `/research [company]` | Get account research |
| `/prompts [industry] [role]` | Get relevant prompts |
| `/tonality hormozi` | Switch to Hormozi voice |

## Support

- Docs: [gtm-skills.com/free-tools/moltbot](https://gtm-skills.com/free-tools/moltbot)
- Issues: [github.com/Prospeda/moltbot-pro/issues](https://github.com/Prospeda/moltbot-pro/issues)
