# Discord Bypass Bot

A powerful Discord bot that bypasses link shorteners and script protection services with advanced rate limiting and auto-bypass functionality.

## Features Implemented

### ✅ Auto-Bypass Channel Persistence
- Channel settings are now saved to `autobypass_channels.json`
- Settings persist across bot restarts and updates
- Automatically loads previous configuration on startup

### ✅ Message Cleanup
- Non-link messages in auto-bypass channels are automatically deleted
- Only valid links are processed
- Keeps auto-bypass channels clean and organized

### ✅ Server-Sided Message Deletion
- Server notification messages auto-delete after 10-15 seconds
- User DMs remain intact for reference
- Reduces channel clutter

### ✅ Rate Limiting System
**Short-term limit:** 2 bypasses per 5 minutes
**Daily limit:** 10 bypasses per day

Rate limits are tracked per user with persistent storage in `user_rates.json`:
- Counters survive bot restarts
- Daily limits reset at midnight UTC
- Fair usage enforcement

### ✅ Premium Upgrade Notifications
When a user exceeds the daily limit:
- **Server owner** receives a DM notification with user details
- **User** receives a warning message about premium access
- Clear messaging about limits and upgrade options

## Setup Instructions

1. **Create a `.env` file** with your credentials:
```env
DISCORD_BOT_TOKEN=your_discord_bot_token_here
BYPASS_API_KEY=your_bypass_api_key_here
OPENAI_API_KEY=your_openai_api_key_here (optional)
BOT_OWNER_ID=your_discord_user_id_here
```

2. **Install dependencies** (already done):
```bash
pip install -r requirements.txt
```

3. **Run the bot**:
```bash
python bot.py
```

## Discord Bot Commands

### User Commands
- `/bypass <link>` - Bypass a link (subject to rate limits)

### Admin Commands (Manage Channels permission required)
- `/autobypass <channel>` - Enable auto-bypass in a channel
- `/disableautobypass` - Disable auto-bypass in your server

## Rate Limit Details

### Short-term Limit (2 per 5 minutes)
- Prevents spam and abuse
- Tracked per user across all servers
- Resets 5 minutes after the first bypass

### Daily Limit (10 per day)
- Fair usage policy
- Resets at midnight UTC
- Tracked in persistent storage

### When Limits Are Hit
**Short-term limit exceeded:**
- User sees: "Please wait X seconds (2 bypasses per 5 minutes)"
- Message auto-deletes after 10 seconds

**Daily limit exceeded:**
- User sees premium upgrade prompt
- Server owner gets notification
- User can retry after midnight UTC

## File Structure

```
├── bot.py                      # Main bot logic
├── user_rate_limiter.py        # Rate limiting system
├── cache_manager.py            # Bypass result caching
├── rate_limiter.py             # General rate limiting
├── ai_service.py               # AI integration (placeholder)
├── hwid_service.py             # HWID management
├── user_activity.py            # User tracking
├── requirements.txt            # Python dependencies
├── .env                        # Configuration (create this)
└── Data files (auto-created):
    ├── autobypass_channels.json  # Auto-bypass channel settings
    ├── user_rates.json           # User rate limit tracking
    ├── bypass_stats.json         # Bot statistics
    └── log_channels.json         # Log channel settings
```

## Supported Services

The bot supports 50+ bypass services including:
- Linkvertise, Codex, Trigon, Rekonise
- Boost.ink, Sub2unlock, Work.ink
- TinyURL, Bit.ly, and many more

## Technical Implementation Details

### Auto-Bypass Channel Persistence
- Uses JSON file storage for reliability
- Automatic save on channel update
- Automatic load on bot startup
- Handles server ID → channel ID mapping

### Rate Limiting
- **Two-tier system**: Short-term (5min) and daily (24h)
- **Persistent storage**: Survives restarts
- **Automatic cleanup**: Old timestamps removed
- **Daily reset**: Midnight UTC with timezone handling

### Message Management
- Server messages use `delete_after` parameter
- User DMs preserved for history
- Non-link messages deleted immediately
- Bypass results sent privately

## Next Steps (Future Enhancements)

1. **Premium User System**
   - Database for premium users
   - Unlimited bypass access
   - Premium badge in responses

2. **Payment Integration**
   - Stripe integration for subscriptions
   - Automated premium activation

3. **Admin Dashboard**
   - View user statistics
   - Manage rate limits
   - Server-specific configurations

4. **Advanced Analytics**
   - Usage reports
   - Popular services tracking
   - User activity graphs

## Notes

- All user data is stored locally in JSON files
- Bot requires `message_content` and `members` intents
- DMs must be enabled for auto-bypass to work
- Rate limits apply per user across all servers
