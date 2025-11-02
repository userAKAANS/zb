# Discord Bypass Bot

## Overview
A Discord bot that bypasses link shorteners and script protection services with advanced rate limiting and auto-bypass functionality.

## Features
- Link bypass for 60+ services including ZEN and EAS-X API support
- Configurable service preferences - enable/disable individual bypass services
- Auto-bypass channels with automatic message cleanup
- Rate limiting: 1 bypass per 15 seconds, 5 per day
- Premium upgrade notifications
- Persistent channel settings across restarts
- DM-based results for privacy
- Server-side message cleanup
- Multi-API fallback system (Ace → TRW → ZEN → EAS-X)

## Recent Changes (November 2025)
- **NEW: Added EAS-X API support**: EAS-X bypass API added as fourth fallback option
- **NEW: Fixed API authentication**: All APIs now use correct authentication methods (headers vs query params)
- **NEW: Updated ZEN API**: Now uses x-api-key header instead of Bearer token
- **NEW: Updated TRW API**: Now uses x-api-key header authentication
- **Multi-API fallback**: System now tries Ace → TRW → ZEN → EAS-X automatically until one succeeds
- **Fixed API response validation**: APIs only return success if actual content is received
- **Fixed "No result from API" error**: Improved response parsing for all providers
- Added EAS-X API key configuration in `/config` command
- Updated rate limits: Changed to 1 bypass per 15 seconds and 5 bypasses per day
- Added new services: Linkify, Pastefy, Scriptpastebins, Admaven, LootLabs, Link-unlock
- Service preferences system with toggle UI (owner-only)
- Implemented paginated service toggle command `/services`
- Service preferences persist across bot restarts
- Auto-delete non-link messages in auto-bypass channels
- Delete server-sided bypass result messages (keep DMs)
- Premium upgrade notifications to server owner

## Architecture
- `bot.py` - Main bot logic with commands and event handlers
- `bypass_provider.py` - Multi-API bypass provider with automatic fallback (Ace → TRW → ZEN → EAS-X)
  - Supports both GET and POST requests with proper header authentication
  - Validates API responses to ensure actual content is received
  - Handles "unsupported link" errors gracefully
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
- `BYPASS_API_KEY` - API key for Ace Bypass service (uses query parameter auth)
- `TRW_API_KEY` - API key for TRW bypass service (uses x-api-key header)
- `ZEN_API_KEY` - API key for ZEN bypass service (uses x-api-key header)
- `EAS_API_KEY` - API key for EAS-X bypass service (uses eas-api-key header)
- `OPENAI_API_KEY` - OpenAI API key for AI features (optional)

**Note**: The bot tries all available APIs in order (Ace → TRW → ZEN → EAS-X) until one succeeds. You can also set API keys using the `/config` command.

### API Authentication Methods
- **Ace**: HTTP GET with `?apikey=` query parameter
- **TRW**: HTTP GET with `x-api-key` header
- **ZEN**: HTTP GET with `x-api-key` header
- **EAS-X**: HTTP POST with `eas-api-key` header and JSON body

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
