# Discord Bypass Bot

## Overview
A Discord bot that bypasses link shorteners and script protection services with advanced rate limiting and auto-bypass functionality.

## Features
- Link bypass for 50+ services
- Auto-bypass channels with automatic message cleanup
- Rate limiting: 2 bypasses per 5 minutes, 10 per day
- Premium upgrade notifications
- Persistent channel settings across restarts
- DM-based results for privacy
- Server-side message cleanup

## Recent Changes
- Added user rate limiting (2 per 5min, 10 per day)
- Implemented auto-bypass channel persistence
- Auto-delete non-link messages in auto-bypass channels
- Delete server-sided bypass result messages (keep DMs)
- Premium upgrade notifications to server owner
- User warnings when hitting rate limits

## Architecture
- `bot.py` - Main bot logic with commands and event handlers
- `user_rate_limiter.py` - User rate limiting with JSON persistence
- `cache_manager.py` - Cache management for bypass results
- `rate_limiter.py` - General rate limiting utilities
- `ai_service.py` - AI service integration placeholder
- `hwid_service.py` - HWID management
- `user_activity.py` - User activity tracking and blacklisting

## Configuration
Create a `.env` file with:
- `DISCORD_BOT_TOKEN` - Your Discord bot token
- `BYPASS_API_KEY` - API key for bypass service
- `OPENAI_API_KEY` - (Optional) OpenAI API key
- `BOT_OWNER_ID` - Your Discord user ID for owner notifications

## Commands
- `/bypass <link>` - Bypass a link
- `/autobypass <channel>` - Enable auto-bypass in a channel
- `/disableautobypass` - Disable auto-bypass

## Rate Limits
- Short-term: 2 bypasses per 5 minutes
- Daily: 10 bypasses per day
- Resets at midnight UTC
