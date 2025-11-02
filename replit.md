# Discord Bypass Bot

## Overview
A Discord bot that bypasses link shorteners and script protection services with advanced rate limiting and auto-bypass functionality.

## Features
- Link bypass for 60+ services including ZEN API support
- Configurable service preferences - enable/disable individual bypass services
- Auto-bypass channels with automatic message cleanup
- Rate limiting: 1 bypass per 15 seconds, 5 per day
- Premium upgrade notifications
- Persistent channel settings across restarts
- DM-based results for privacy
- Server-side message cleanup
- Multi-API fallback system (Ace → TRW → ZEN)

## Recent Changes (November 2025)
- **NEW: Added ZEN API support**: ZEN bypass API added as third fallback option
- **NEW: Updated rate limits**: Changed to 1 bypass per 15 seconds and 5 bypasses per day
- **NEW: Added new services**: Linkify, Pastefy, Scriptpastebins, Admaven, LootLabs, Link-unlock
- **Multi-API fallback**: System now tries Ace → TRW → ZEN automatically until one succeeds
- **Removed commands**: Removed `/switchapi`, `/ban`, `/dm`, and `/purge` commands
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
- `bypass_provider.py` - Multi-API bypass provider with automatic fallback (Ace → TRW → ZEN)
- `user_rate_limiter.py` - User rate limiting with JSON persistence (1 per 15s, 5 per day)
- `cache_manager.py` - Cache management for bypass results
- `rate_limiter.py` - General rate limiting utilities
- `ai_service.py` - AI service integration placeholder
- `hwid_service.py` - HWID management
- `user_activity.py` - User activity tracking and blacklisting

## Configuration
Required secrets (add via Replit Secrets):
- `DISCORD_BOT_TOKEN` - Your Discord bot token (required)
- `BOT_OWNER_ID` - Your Discord user ID for owner notifications (required)

Optional API keys for bypass services (at least one recommended):
- `BYPASS_API_KEY` - API key for Ace Bypass service (optional)
- `TRW_API_KEY` - API key for TRW bypass service (optional)
- `ZEN_API_KEY` - API key for ZEN bypass service (optional)
- `OPENAI_API_KEY` - OpenAI API key for AI features (optional)

**Note**: The bot tries all available APIs in order (Ace → TRW → ZEN) until one succeeds. You can also set API keys using the `/config` command.

## Commands
- `/bypass <link>` - Bypass a link
- `/autobypass <channel>` - Enable auto-bypass in a channel
- `/disableautobypass` - Disable auto-bypass
- `/services` - [OWNER ONLY] Toggle individual bypass services on/off
- `/config` - [OWNER ONLY] Configure bot API keys

## Rate Limits
- Short-term: 1 bypass per 15 seconds
- Daily: 5 bypasses per day
- Daily resets at midnight UTC

## Supported Services (60+)
All services from Ace, TRW, and ZEN APIs including:
- Linkvertise, LootLabs, Admaven, Work.ink, CodeX, Cuty.io, ouo.io, Lockr, Rekonise, MBoost.me
- KRNL, Platoboost, Blox-script, Overdrivehub, Socialwolvez, Linkify
- Pastebin, Paste-Drop, Pastefy, Scriptpastebins
- Sub2Unlock, Sub4Unlock, and many more

Use `/supported` command to view all services.
