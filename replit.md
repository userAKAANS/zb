# Discord Bypass Bot

## Overview
A Discord bot that bypasses link shorteners and script protection services with advanced rate limiting and auto-bypass functionality.

## Features
- Link bypass for 50+ services
- Configurable service preferences - enable/disable individual bypass services
- Auto-bypass channels with automatic message cleanup
- Rate limiting: 2 bypasses per 5 minutes, 10 per day
- Premium upgrade notifications
- Persistent channel settings across restarts
- DM-based results for privacy
- Server-side message cleanup

## Recent Changes (November 2025)
- **Hardcoded TRW API as fallback**: TRW bypass API is now hardcoded as automatic fallback when Ace Bypass fails
- **Removed commands**: Removed `/switchapi`, `/ban`, `/dm`, and `/purge` commands
- **Simplified bypass provider**: Removed API switching UI, now uses Ace Bypass with automatic TRW fallback
- Added service preferences system with toggle UI (owner-only)
- Implemented paginated service toggle command `/services`
- Service preferences persist across bot restarts
- Added user rate limiting (2 per 5min, 10 per day)
- Implemented auto-bypass channel persistence
- Auto-delete non-link messages in auto-bypass channels
- Delete server-sided bypass result messages (keep DMs)
- Premium upgrade notifications to server owner
- User warnings when hitting rate limits

## Architecture
- `bot.py` - Main bot logic with commands and event handlers
- `bypass_provider.py` - Hardcoded bypass API provider with automatic fallback (Ace → TRW)
- `user_rate_limiter.py` - User rate limiting with JSON persistence
- `cache_manager.py` - Cache management for bypass results
- `rate_limiter.py` - General rate limiting utilities
- `ai_service.py` - AI service integration placeholder
- `hwid_service.py` - HWID management
- `user_activity.py` - User activity tracking and blacklisting

## Configuration
Required secrets (add via Replit Secrets):
- `DISCORD_BOT_TOKEN` - Your Discord bot token (required)
- `BYPASS_API_KEY` - API key for Ace Bypass service (optional, TRW is fallback)
- `OPENAI_API_KEY` - OpenAI API key for AI features (optional)
- `BOT_OWNER_ID` - Your Discord user ID for owner notifications (required)

**Note**: TRW API is hardcoded as a fallback and does not require a separate API key.

## Commands
- `/bypass <link>` - Bypass a link
- `/autobypass <channel>` - Enable auto-bypass in a channel
- `/disableautobypass` - Disable auto-bypass
- `/services` - [OWNER ONLY] Toggle individual bypass services on/off
- `/config` - [OWNER ONLY] Configure bot API keys

## Rate Limits
- Short-term: 2 bypasses per 5 minutes
- Daily: 10 bypasses per day
- Resets at midnight UTC
