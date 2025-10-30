# Setup Guide - Discord Bypass Bot

## Quick Start

### Step 1: Get Your Discord Bot Token

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" tab
4. Click "Reset Token" and copy the token
5. **Enable these Privileged Gateway Intents:**
   - ✅ Message Content Intent
   - ✅ Server Members Intent

### Step 2: Get Your Bypass API Key

Contact the bypass API provider (ace-bypass.com) to obtain an API key.

### Step 3: Get Your Discord User ID

1. Enable Developer Mode in Discord (Settings → Advanced → Developer Mode)
2. Right-click your username and select "Copy ID"

### Step 4: Configure Environment Variables

Create a `.env` file in the project root with the following content:

```env
DISCORD_BOT_TOKEN=your_discord_bot_token_here
BYPASS_API_KEY=your_bypass_api_key_here
BOT_OWNER_ID=your_discord_user_id_here
OPENAI_API_KEY=optional_openai_key_here
```

Replace the placeholder values with your actual credentials.

### Step 5: Invite Bot to Your Server

1. In the Discord Developer Portal, go to "OAuth2" → "URL Generator"
2. Select these scopes:
   - ✅ `bot`
   - ✅ `applications.commands`
3. Select these bot permissions:
   - ✅ Send Messages
   - ✅ Manage Messages
   - ✅ Embed Links
   - ✅ Read Message History
   - ✅ Use Slash Commands
4. Copy the generated URL and open it in your browser
5. Select your server and authorize the bot

### Step 6: Run the Bot

The bot is already configured to run automatically. Just make sure you've set up the `.env` file!

The workflow "Discord Bot" will start automatically when you have the environment variables set.

## Testing the Bot

### Test Basic Bypass
```
/bypass https://example-link.com
```

### Set Up Auto-Bypass Channel
```
/autobypass #channel-name
```
Now post any link in that channel to test automatic bypass!

### Test Rate Limits
Try bypassing more than 2 links within 5 minutes to see the short-term limit.
Try bypassing more than 10 links in a day to see the daily limit and premium notification.

## Features Overview

### ✅ All Requested Features Implemented

1. **Auto-Bypass Channel Persistence**
   - Settings saved in `autobypass_channels.json`
   - Survives bot restarts and updates
   - Automatically loads on startup

2. **Message Cleanup**
   - Non-link messages automatically deleted
   - Clean notification sent (auto-deletes in 10 seconds)
   - Only valid links are processed

3. **Server Message Deletion**
   - All server notifications use `delete_after=10` or `delete_after=15`
   - User DMs remain intact
   - Reduces server clutter

4. **Rate Limiting**
   - **Short-term:** 2 bypasses per 5 minutes
   - **Daily:** 10 bypasses per 24 hours
   - Persistent storage in `user_rates.json`
   - Automatic reset at midnight UTC

5. **Premium Notifications**
   - Server owner gets DM when user hits daily limit
   - User receives premium upgrade prompt
   - Clear messaging about limits

## File Structure

```
Discord Bypass Bot/
│
├── bot.py                      # Main bot logic
├── user_rate_limiter.py        # Rate limiting (2/5min, 10/day)
├── cache_manager.py            # Result caching
├── rate_limiter.py             # General rate limiter
├── ai_service.py               # AI service placeholder
├── hwid_service.py             # HWID management
├── user_activity.py            # User tracking
│
├── .env                        # Your secrets (CREATE THIS!)
├── .env.example                # Template for .env
├── requirements.txt            # Python dependencies
├── .gitignore                  # Excludes secrets and data
│
├── README.md                   # Feature documentation
├── SETUP_GUIDE.md             # This file
│
└── Data Files (auto-created):
    ├── autobypass_channels.json   # Channel settings ✅ PERSISTS
    ├── user_rates.json            # Rate limit tracking ✅ PERSISTS
    ├── bypass_stats.json          # Statistics
    └── log_channels.json          # Log channels
```

## Commands Reference

### User Commands
| Command | Description |
|---------|-------------|
| `/bypass <link>` | Bypass a link (rate limited) |

### Admin Commands (Requires: Manage Channels)
| Command | Description |
|---------|-------------|
| `/autobypass <channel>` | Enable auto-bypass in a channel |
| `/disableautobypass` | Disable auto-bypass |

## Rate Limit Behavior

### When User Hits Short-Term Limit (2 per 5min)
```
⏰ @User - Please wait 245 seconds (2 bypasses per 5 minutes)
```
Message auto-deletes after 10 seconds.

### When User Hits Daily Limit (10 per day)
**In Server:**
```
🚫 @User - Daily limit reached (10/day). Check DMs for premium info.
```
Message auto-deletes after 15 seconds.

**In User DM:**
```
🚫 Daily Bypass Limit Reached

You've used all 10 bypasses for today.

⏰ Resets in: 43200 seconds

💎 Want Unlimited Access?
Upgrade to Premium for unlimited bypasses!
Contact the server owner for more information.
```

**To Bot Owner (Your DM):**
```
⚠️ Rate Limit Exceeded

User has exceeded daily bypass limit.

User: @Username (123456789)
Server: Server Name (987654321)
Daily Limit: 10 bypasses
Recommendation: User may need premium access for unlimited bypasses.
```

## Auto-Bypass Channel Behavior

When auto-bypass is enabled in a channel:

1. **User posts a link** → Link is deleted, bypass starts
2. **User posts text without link** → Message deleted, error shown
3. **Bypass succeeds** → DM sent to user, server notification (deletes in 10s)
4. **User hits rate limit** → Message deleted, rate limit notice (deletes in 10-15s)
5. **User DMs disabled** → Error message (deletes in 15s)

## Troubleshooting

### Bot doesn't respond
- Check if `.env` file exists and has valid tokens
- Verify bot has required permissions in your server
- Check the workflow logs for errors

### Auto-bypass not working
- Use `/autobypass #channel` to enable it
- Make sure bot can delete messages in that channel
- Verify you're posting valid URLs

### Rate limit not working
- Check if `user_rates.json` is being created
- Verify system clock is correct
- Try deleting `user_rates.json` to reset

### Premium notifications not sent
- Verify `BOT_OWNER_ID` is set in `.env`
- Make sure bot can send DMs to server owner
- Check owner hasn't blocked the bot

## Security Notes

✅ `.env` file is in `.gitignore` - secrets won't be committed
✅ All data files are in `.gitignore` - user data protected
✅ API keys are loaded from environment variables only
✅ No secrets are ever logged or exposed in messages

## Support

If you encounter issues:
1. Check the workflow logs in Replit
2. Verify all environment variables are set correctly
3. Make sure bot has the required permissions
4. Check that Discord intents are enabled
