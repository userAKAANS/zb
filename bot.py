import discord
from discord import app_commands
from discord.ui import Modal, TextInput, View, Button
import aiohttp
import os
from dotenv import load_dotenv, set_key
from urllib.parse import quote, urlparse
import re
import time
from datetime import datetime, timedelta
import json
import asyncio
from typing import Optional, Dict, List
from collections import defaultdict
import hashlib

from ai_service import AIService
from cache_manager import CacheManager
from rate_limiter import RateLimiter
from hwid_service import HWIDService
from user_activity import UserActivity
from user_rate_limiter import UserRateLimiter

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
BYPASS_API_KEY = os.getenv('BYPASS_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', 0))

AUTOBYPASS_FILE = 'autobypass_channels.json'
STATS_FILE = 'bypass_stats.json'
LOG_CHANNELS_FILE = 'log_channels.json'

def load_log_channels():
    try:
        if os.path.exists(LOG_CHANNELS_FILE):
            with open(LOG_CHANNELS_FILE, 'r') as f:
                data = json.load(f)
                return {int(k): int(v) for k, v in data.items()}
    except Exception as e:
        print(f"Error loading log channels: {e}")
    return {}

def save_log_channels(channels):
    try:
        with open(LOG_CHANNELS_FILE, 'w') as f:
            json.dump({str(k): v for k, v in channels.items()}, f, indent=2)
    except Exception as e:
        print(f"Error saving log channels: {e}")

def load_autobypass_channels():
    try:
        if os.path.exists(AUTOBYPASS_FILE):
            with open(AUTOBYPASS_FILE, 'r') as f:
                data = json.load(f)
                return {int(k): int(v) for k, v in data.items()}
    except Exception as e:
        print(f"Error loading autobypass channels: {e}")
    return {}

def save_autobypass_channels(channels):
    try:
        with open(AUTOBYPASS_FILE, 'w') as f:
            json.dump({str(k): v for k, v in channels.items()}, f, indent=2)
    except Exception as e:
        print(f"Error saving autobypass channels: {e}")

def load_stats():
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading stats: {e}")
    return {
        'total_bypassed': 0,
        'loadstrings': 0,
        'urls': 0,
        'failed': 0,
        'cached_hits': 0,
        'ai_analyses': 0,
        'service_stats': {}
    }

def save_stats(stats):
    try:
        with open(STATS_FILE, 'w') as f:
            json.dump(stats, f, indent=2)
    except Exception as e:
        print(f"Error saving stats: {e}")

autobypass_channels = load_autobypass_channels()
bypass_stats = load_stats()
log_channels = load_log_channels()

ai_service = AIService(OPENAI_API_KEY) if OPENAI_API_KEY else None
cache_manager = CacheManager(ttl_minutes=30)
rate_limiter = RateLimiter(max_requests=10, time_window=60)
hwid_service = HWIDService()
user_activity = UserActivity()
user_rate_limiter = UserRateLimiter()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

SUPPORTED_SERVICES = [
    "codex", "trigon", "rekonise", "linkvertise", "paster-so", "cuttlinks",
    "boost-ink-and-bst-gg", "keyguardian", "bstshrt", "nicuse-getkey",
    "adfoc.us", "bit.do", "bit.ly", "blox-script", "boost.ink", "cl.gy",
    "cuty-cuttlinks", "getpolsec", "goo.gl", "is.gd", "junkie-development.flow",
    "ldnesfspublic", "link-hub.net", "link-unlock-complete", "link4m.com",
    "linkunlock", "linkunlocker.com", "lockr", "mboost", "mediafire",
    "overdrivehub", "paste-drop.com", "pastebin.com", "pastes_io", "quartyz",
    "rebrand.ly", "rekonise.com", "rentry.co", "rinku-pro", "rkns.link",
    "shorteners-and-direct", "shorter.me", "socialwolvez.com", "sub2get.com",
    "sub2unlock.net", "sub4unlock.com", "subfinal", "t.co", "t.ly", "tiny.cc",
    "tinylink.onl", "tinyurl.com", "tpi.li", "unlocknow.net", "v.gd",
    "work-ink", "ytsubme", "ace-bypass.com"
]

def detect_url(text: str) -> Optional[str]:
    def extract_markdown_links(text):
        i = 0
        while i < len(text):
            if text[i:i+2] == '][':
                i += 1
                continue
            if text[i] == '[':
                bracket_start = i
                i += 1
                while i < len(text) and text[i] != ']':
                    i += 1
                if i < len(text) and i + 1 < len(text) and text[i+1] == '(':
                    i += 2
                    paren_count = 1
                    url_start = i
                    while i < len(text) and paren_count > 0:
                        if text[i] == '(':
                            paren_count += 1
                        elif text[i] == ')':
                            paren_count -= 1
                        i += 1
                    if paren_count == 0:
                        return text[url_start:i-1]
            i += 1
        return None
    
    markdown_url = extract_markdown_links(text)
    if markdown_url:
        text = markdown_url
    
    tokens = text.split()
    
    for token in tokens:
        token = token.strip(' \t\n\r')
        token = re.sub(r'[.,;:!?]+$', '', token)
        
        while token and len(token) > 1:
            opener = token[0]
            closer = token[-1]
            if (opener == '<' and closer == '>') or \
               (opener == '(' and closer == ')') or \
               (opener == '[' and closer == ']') or \
               (opener == '{' and closer == '}') or \
               (opener in '"\'' and closer in '"\'') or \
               (opener in '*_~`' and closer in '*_~`'):
                token = token[1:-1].strip()
                token = re.sub(r'[.,;:!?]+$', '', token)
            else:
                break
        
        if not token:
            continue
        
        candidate = token if token.lower().startswith(('http://', 'https://')) else f'https://{token}'
        
        try:
            parsed = urlparse(candidate)
            if parsed.netloc and '.' in parsed.netloc:
                return candidate
        except:
            continue
    
    return None

def is_supported_service(url: str) -> bool:
    try:
        parsed = urlparse(url.lower())
        domain = parsed.netloc.replace('www.', '')
        
        for service in SUPPORTED_SERVICES:
            if service in domain or domain in service:
                return True
        return False
    except:
        return False

def get_service_name(url: str) -> str:
    try:
        parsed = urlparse(url.lower())
        domain = parsed.netloc.replace('www.', '')
        
        for service in SUPPORTED_SERVICES:
            if service in domain or domain in service:
                return service
        return domain
    except:
        return "unknown"

async def log_bypass_to_channel(user: discord.User, guild: discord.Guild, link: str, time_taken: float, result_type: str):
    global log_channels
    try:
        if guild.id in log_channels:
            log_channel_id = log_channels[guild.id]
            log_channel = guild.get_channel(log_channel_id)
            
            if log_channel and isinstance(log_channel, discord.TextChannel):
                embed = discord.Embed(
                    title="📝 Bypass Log",
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                
                embed.add_field(
                    name="👤 User",
                    value=user.mention,
                    inline=True
                )
                
                embed.add_field(
                    name="⏱️ Time Taken",
                    value=f"{time_taken}s",
                    inline=True
                )
                
                embed.add_field(
                    name="📊 Total Bypasses",
                    value=f"{bypass_stats['total_bypassed']:,}",
                    inline=True
                )
                
                embed.add_field(
                    name="🔗 Link",
                    value=f"`{link[:100]}{'...' if len(link) > 100 else ''}`",
                    inline=False
                )
                
                embed.add_field(
                    name="📋 Result Type",
                    value=result_type.title(),
                    inline=True
                )
                
                embed.set_footer(text="Bypass Bot Logger")
                
                await log_channel.send(embed=embed)
    except Exception as e:
        print(f"Error logging bypass to channel: {e}")

async def notify_owner_rate_limit_exceeded(bot_instance, guild: discord.Guild, user: discord.User):
    try:
        if BOT_OWNER_ID:
            owner = await bot_instance.fetch_user(BOT_OWNER_ID)
            if owner:
                embed = discord.Embed(
                    title="⚠️ Rate Limit Exceeded",
                    description=f"User has exceeded daily bypass limit.",
                    color=discord.Color.orange(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="User", value=f"{user.mention} ({user.id})", inline=True)
                embed.add_field(name="Server", value=f"{guild.name} ({guild.id})", inline=True)
                embed.add_field(name="Daily Limit", value="10 bypasses", inline=True)
                embed.add_field(name="Recommendation", value="User may need premium access for unlimited bypasses.", inline=False)
                embed.set_footer(text="Bypass Bot | Rate Limit Monitor")
                
                await owner.send(embed=embed)
    except Exception as e:
        print(f"Error notifying owner about rate limit: {e}")

async def bypass_link(link: str, use_cache: bool = True) -> dict:
    start_time = time.time()
    
    if use_cache:
        cached_result = cache_manager.get(link)
        if cached_result:
            bypass_stats['cached_hits'] += 1
            save_stats(bypass_stats)
            cached_result['from_cache'] = True
            cached_result['time_taken'] = round(time.time() - start_time, 2)
            return cached_result
    
    try:
        async with aiohttp.ClientSession() as session:
            api_url = f'http://ace-bypass.com/api/bypass?url={quote(link)}&apikey={BYPASS_API_KEY}'
            
            async with session.get(
                api_url,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                time_taken = round(time.time() - start_time, 2)
                
                if response.status == 200:
                    data = await response.json()
                    
                    loadstring = data.get('loadstring') or data.get('script') or data.get('code')
                    bypassed_url = data.get('destination') or data.get('result') or data.get('bypassed_url') or data.get('url')
                    
                    result = None
                    if loadstring:
                        bypass_stats['total_bypassed'] += 1
                        bypass_stats['loadstrings'] += 1
                        service = get_service_name(link)
                        bypass_stats['service_stats'][service] = bypass_stats['service_stats'].get(service, 0) + 1
                        save_stats(bypass_stats)
                        
                        result = {
                            'success': True,
                            'type': 'loadstring',
                            'result': loadstring,
                            'original_link': link,
                            'time_taken': time_taken,
                            'from_cache': False
                        }
                    elif bypassed_url:
                        if bypassed_url.lower().startswith(('loadstring(', 'game:', 'local ', 'function ', 'return ')):
                            bypass_stats['total_bypassed'] += 1
                            bypass_stats['loadstrings'] += 1
                            service = get_service_name(link)
                            bypass_stats['service_stats'][service] = bypass_stats['service_stats'].get(service, 0) + 1
                            save_stats(bypass_stats)
                            
                            result = {
                                'success': True,
                                'type': 'loadstring',
                                'result': bypassed_url,
                                'original_link': link,
                                'time_taken': time_taken,
                                'from_cache': False
                            }
                        else:
                            bypass_stats['total_bypassed'] += 1
                            bypass_stats['urls'] += 1
                            service = get_service_name(link)
                            bypass_stats['service_stats'][service] = bypass_stats['service_stats'].get(service, 0) + 1
                            save_stats(bypass_stats)
                            
                            result = {
                                'success': True,
                                'type': 'url',
                                'result': bypassed_url,
                                'original_link': link,
                                'time_taken': time_taken,
                                'from_cache': False
                            }
                    
                    if result and use_cache:
                        cache_manager.set(link, result)
                    
                    if result:
                        return result
                    else:
                        bypass_stats['failed'] += 1
                        save_stats(bypass_stats)
                        return {
                            'success': False,
                            'error': f'No result from API: {str(data)[:200]}',
                            'time_taken': time_taken,
                            'from_cache': False
                        }
                else:
                    bypass_stats['failed'] += 1
                    save_stats(bypass_stats)
                    error_text = await response.text()
                    return {
                        'success': False,
                        'error': f'API error {response.status}: {error_text[:200]}',
                        'time_taken': time_taken,
                        'from_cache': False
                    }
    except Exception as e:
        bypass_stats['failed'] += 1
        save_stats(bypass_stats)
        time_taken = round(time.time() - start_time, 2)
        return {
            'success': False,
            'error': f'Exception: {str(e)[:200]}',
            'time_taken': time_taken,
            'from_cache': False
        }

class CopyButtonView(View):
    def __init__(self, content: str, content_type: str = "Content"):
        super().__init__(timeout=None)
        self.content = content
        self.content_type = content_type

class CopyLinkView(View):
    def __init__(self, link: str):
        super().__init__(timeout=None)
        self.link = link

@bot.event
async def on_ready():
    await tree.sync()
    print(f'✅ Logged in as {bot.user}')
    print(f'📊 Connected to {len(bot.guilds)} servers')
    print(f'🔧 Auto-bypass enabled in {len(autobypass_channels)} channels')
    print(f'🚀 Bot is ready!')

@tree.command(name="bypass", description="Bypass a link")
async def bypass_command(interaction: discord.Interaction, link: str):
    link_to_bypass = link.strip()
    
    rate_limit_result = user_rate_limiter.check_rate_limit(interaction.user.id)
    
    if not rate_limit_result['allowed']:
        if rate_limit_result['limit_type'] == 'short_term':
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="⏰ Rate Limit",
                    description=f"You're doing that too fast! Please wait {rate_limit_result['retry_after']:.0f} seconds.\n\n**Limit:** 2 bypasses per 5 minutes",
                    color=discord.Color.orange()
                ).set_footer(text="Bypass Bot | Rate Limited"),
                ephemeral=True
            )
        elif rate_limit_result['limit_type'] == 'daily':
            if interaction.guild:
                await notify_owner_rate_limit_exceeded(bot, interaction.guild, interaction.user)
            
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="🚫 Daily Limit Reached",
                    description=f"You've reached your daily limit of 10 bypasses.\n\n⏰ Resets in: {rate_limit_result['retry_after']:.0f} seconds\n\n💎 **Want More?**\nUpgrade to **Premium Access** for unlimited bypasses!\nContact the server owner for premium options.",
                    color=discord.Color.red()
                ).set_footer(text="Bypass Bot | Premium Available"),
                ephemeral=True
            )
        return
    
    await interaction.response.send_message(
        embed=discord.Embed(
            title="⏳ Processing...",
            description=f"Bypassing link...\n`{link_to_bypass[:100]}`",
            color=discord.Color.blue()
        ).set_footer(text="Bypass Bot"),
        ephemeral=True
    )
    
    if not is_supported_service(link_to_bypass):
        await interaction.edit_original_response(
            embed=discord.Embed(
                title="⚠️ Unsupported Service",
                description=f"This link may not be from a supported service.\n\n🔍 Attempting bypass anyway...",
                color=discord.Color.orange()
            ).set_footer(text="Bypass Bot")
        )
        await asyncio.sleep(2)
    
    result = await bypass_link(link_to_bypass)
    
    if result['success']:
        user_rate_limiter.record_bypass(interaction.user.id)
        
        if interaction.guild:
            await log_bypass_to_channel(
                interaction.user,
                interaction.guild,
                link_to_bypass,
                result['time_taken'],
                result['type']
            )
        
        cache_indicator = "⚡ From Cache" if result.get('from_cache') else "✨ Fresh Result"
        
        if result['type'] == 'loadstring':
            loadstring = result['result']
            embed = discord.Embed(
                title="✅ Loadstring Retrieved Successfully",
                description=f"**Original Link:**\n`{link_to_bypass[:100]}`\n\n⏱️ **Time Taken:** {result['time_taken']}s\n{cache_indicator}",
                color=discord.Color.green()
            )
            
            if len(loadstring) <= 500:
                embed.add_field(
                    name="📋 Loadstring",
                    value=f"```lua\n{loadstring}\n```",
                    inline=False
                )
            else:
                preview = loadstring[:500]
                embed.add_field(
                    name="📋 Loadstring Preview",
                    value=f"```lua\n{preview}...\n```\n*Full script is {len(loadstring)} characters.*",
                    inline=False
                )
            
            embed.set_footer(text="Bypass Bot | Only you can see this")
            await interaction.edit_original_response(embed=embed)
        elif result['type'] == 'url':
            bypassed_url = result['result']
            embed = discord.Embed(
                title="✅ Link Bypassed Successfully",
                description=f"**Original Link:**\n`{link_to_bypass[:100]}`\n\n**Bypassed Link:**\n`{bypassed_url}`\n\n⏱️ **Time Taken:** {result['time_taken']}s\n{cache_indicator}",
                color=discord.Color.green()
            )
            embed.set_footer(text="Bypass Bot | Only you can see this")
            await interaction.edit_original_response(embed=embed)
    else:
        error_description = f"**Error:** {result['error']}\n\n⏱️ **Time Taken:** {result.get('time_taken', 'N/A')}s"
        
        await interaction.edit_original_response(
            embed=discord.Embed(
                title="❌ Bypass Failed",
                description=error_description,
                color=discord.Color.red()
            ).set_footer(text="Bypass Bot")
        )

@tree.command(name="autobypass", description="Enable auto-bypass in a channel")
@app_commands.describe(channel="The channel to enable autobypass in")
async def autobypass_command(interaction: discord.Interaction, channel: discord.TextChannel):
    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Permission Denied",
                description="You need the **Manage Channels** permission to use this command.",
                color=discord.Color.red()
            ).set_footer(text="Bypass Bot"),
            ephemeral=True
        )
        return
    
    global autobypass_channels
    autobypass_channels[interaction.guild.id] = channel.id
    save_autobypass_channels(autobypass_channels)
    
    await interaction.response.send_message(
        embed=discord.Embed(
            title="✅ Auto-Bypass Enabled",
            description=f"Auto-bypass has been enabled in {channel.mention}!\n\n**Features:**\n• Links will be automatically bypassed\n• Non-link messages will be deleted\n• Results sent via DM\n• Rate limits: 2 per 5min, 10 per day",
            color=discord.Color.green()
        ).set_footer(text="Bypass Bot"),
        ephemeral=True
    )

@tree.command(name="disableautobypass", description="Disable auto-bypass in your server")
async def disableautobypass_command(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Permission Denied",
                description="You need the **Manage Channels** permission to use this command.",
                color=discord.Color.red()
            ).set_footer(text="Bypass Bot"),
            ephemeral=True
        )
        return
    
    global autobypass_channels
    if interaction.guild.id in autobypass_channels:
        del autobypass_channels[interaction.guild.id]
        save_autobypass_channels(autobypass_channels)
        
        await interaction.response.send_message(
            embed=discord.Embed(
                title="✅ Auto-Bypass Disabled",
                description="Auto-bypass has been disabled in this server.",
                color=discord.Color.green()
            ).set_footer(text="Bypass Bot"),
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="ℹ️ Auto-Bypass Not Enabled",
                description="Auto-bypass is not currently enabled in this server.",
                color=discord.Color.blue()
            ).set_footer(text="Bypass Bot"),
            ephemeral=True
        )

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if message.guild and message.guild.id in autobypass_channels:
        if message.channel.id == autobypass_channels[message.guild.id]:
            detected_link = detect_url(message.content)
            
            if detected_link:
                rate_limit_result = user_rate_limiter.check_rate_limit(message.author.id)
                
                if not rate_limit_result['allowed']:
                    try:
                        await message.delete()
                    except:
                        pass
                    
                    if rate_limit_result['limit_type'] == 'short_term':
                        notification = await message.channel.send(
                            embed=discord.Embed(
                                description=f"⏰ {message.author.mention} - Please wait {rate_limit_result['retry_after']:.0f} seconds (2 bypasses per 5 minutes)",
                                color=discord.Color.orange()
                            ).set_footer(text="Bypass Bot"),
                            delete_after=10
                        )
                    elif rate_limit_result['limit_type'] == 'daily':
                        await notify_owner_rate_limit_exceeded(bot, message.guild, message.author)
                        
                        notification = await message.channel.send(
                            embed=discord.Embed(
                                description=f"🚫 {message.author.mention} - Daily limit reached (10/day). Check DMs for premium info.",
                                color=discord.Color.red()
                            ).set_footer(text="Bypass Bot"),
                            delete_after=15
                        )
                        
                        try:
                            await message.author.send(
                                embed=discord.Embed(
                                    title="🚫 Daily Bypass Limit Reached",
                                    description=f"You've used all 10 bypasses for today.\n\n⏰ **Resets in:** {rate_limit_result['retry_after']:.0f} seconds\n\n💎 **Want Unlimited Access?**\nUpgrade to Premium for unlimited bypasses!\nContact the server owner for more information.",
                                    color=discord.Color.red()
                                ).set_footer(text="Bypass Bot | Premium Available")
                            )
                        except:
                            pass
                    return
                
                try:
                    await message.delete()
                except:
                    pass
                
                result = await bypass_link(detected_link)
                
                if result['success']:
                    user_rate_limiter.record_bypass(message.author.id)
                    
                    dm_embed = discord.Embed(
                        title="✅ Auto-Bypass Result",
                        description=f"**Original Link:**\n`{detected_link[:100]}`\n\n⏱️ **Time Taken:** {result['time_taken']}s",
                        color=discord.Color.green()
                    )
                    
                    if result['type'] == 'loadstring':
                        loadstring = result['result']
                        if len(loadstring) <= 500:
                            dm_embed.add_field(
                                name="📋 Loadstring",
                                value=f"```lua\n{loadstring}\n```",
                                inline=False
                            )
                        else:
                            dm_embed.add_field(
                                name="📋 Loadstring Preview",
                                value=f"```lua\n{loadstring[:500]}...\n```\n*Full script is {len(loadstring)} characters.*",
                                inline=False
                            )
                    elif result['type'] == 'url':
                        dm_embed.add_field(
                            name="🔗 Bypassed Link",
                            value=f"`{result['result']}`",
                            inline=False
                        )
                    
                    dm_embed.set_footer(text=f"From {message.guild.name} | Bypass Bot")
                    
                    try:
                        await message.author.send(embed=dm_embed)
                        notification = await message.channel.send(
                            embed=discord.Embed(
                                description=f"✅ {message.author.mention} - Check your DMs!",
                                color=discord.Color.green()
                            ).set_footer(text="Bypass Bot"),
                            delete_after=10
                        )
                    except discord.Forbidden:
                        notification = await message.channel.send(
                            embed=discord.Embed(
                                description=f"❌ {message.author.mention} - I couldn't send you a DM. Please enable DMs from server members.",
                                color=discord.Color.red()
                            ).set_footer(text="Bypass Bot"),
                            delete_after=15
                        )
                else:
                    try:
                        await message.author.send(
                            embed=discord.Embed(
                                title="❌ Auto-Bypass Failed",
                                description=f"Failed to bypass your link.\n\n**Error:** {result['error'][:200]}",
                                color=discord.Color.red()
                            ).set_footer(text="Bypass Bot")
                        )
                    except:
                        pass
            else:
                try:
                    await message.delete()
                    await message.channel.send(
                        embed=discord.Embed(
                            description=f"❌ {message.author.mention} - Only links are allowed in this channel.",
                            color=discord.Color.red()
                        ).set_footer(text="Bypass Bot"),
                        delete_after=10
                    )
                except:
                    pass

if __name__ == "__main__":
    print("🚀 Starting Bypass Bot...")
    print(f"📦 Loading configurations...")
    print(f"⚡ Enhanced Features: Rate Limiting Active")
    print(f"🔑 Bypass API Key: {'Set' if BYPASS_API_KEY else 'Not Set'}")
    
    if not DISCORD_BOT_TOKEN:
        print("❌ ERROR: DISCORD_BOT_TOKEN not found in environment variables!")
        print("Please set DISCORD_BOT_TOKEN in your .env file")
        exit(1)
    
    bot.run(DISCORD_BOT_TOKEN)
