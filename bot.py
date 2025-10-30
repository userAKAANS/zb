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
from typing import Optional, Dict, List, Union
from collections import defaultdict
import hashlib

from ai_service import AIService
from cache_manager import CacheManager
from rate_limiter import RateLimiter
from hwid_service import HWIDService
from user_activity import UserActivity

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
BYPASS_API_KEY = os.getenv('BYPASS_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', 0))

AUTOBYPASS_FILE = 'autobypass_channels.json'
STATS_FILE = 'bypass_stats.json'
LOG_CHANNELS_FILE = 'log_channels.json'
SERVICE_PREFERENCES_FILE = 'service_preferences.json'

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
        'service_stats': {},
        'junkie_blocked': 0
    }

def save_stats(stats):
    try:
        with open(STATS_FILE, 'w') as f:
            json.dump(stats, f, indent=2)
    except Exception as e:
        print(f"Error saving stats: {e}")

def load_service_preferences():
    try:
        if os.path.exists(SERVICE_PREFERENCES_FILE):
            with open(SERVICE_PREFERENCES_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading service preferences: {e}")
    return {service: True for service in SUPPORTED_SERVICES}

def save_service_preferences(preferences):
    try:
        with open(SERVICE_PREFERENCES_FILE, 'w') as f:
            json.dump(preferences, f, indent=2)
    except Exception as e:
        print(f"Error saving service preferences: {e}")

autobypass_channels = load_autobypass_channels()
bypass_stats = load_stats()
log_channels = load_log_channels()

ai_service = AIService(OPENAI_API_KEY) if OPENAI_API_KEY else None
cache_manager = CacheManager(ttl_minutes=30)
rate_limiter = RateLimiter(max_requests=10, time_window=60)
hwid_service = HWIDService()
user_activity = UserActivity()

SUPPORTED_SERVICES = [
    "codex", "trigon", "rekonise", "linkvertise", "paster-so", "cuttlinks",
    "boost-ink-and-bst-gg", "keyguardian", "bstshrt", "nicuse-getkey",
    "adfoc.us", "bit.do", "bit.ly", "blox-script", "boost.ink", "cl.gy",
    "cuty-cuttlinks", "getpolsec", "goo.gl", "is.gd",
    "ldnesfspublic", "link-hub.net", "link-unlock-complete", "link4m.com",
    "linkunlock", "linkunlocker.com", "lockr", "mboost", "mediafire",
    "overdrivehub", "paste-drop.com", "pastebin.com", "pastes_io", "quartyz",
    "rebrand.ly", "rekonise.com", "rentry.co", "rinku-pro", "rkns.link",
    "shorteners-and-direct", "shorter.me", "socialwolvez.com", "sub2get.com",
    "sub2unlock.net", "sub4unlock.com", "subfinal", "t.co", "t.ly", "tiny.cc",
    "tinylink.onl", "tinyurl.com", "tpi.li", "unlocknow.net", "v.gd",
    "work-ink", "ytsubme", "ace-bypass.com", "delta", "krnl", "platoboost"
]

SERVICE_EMOJIS = {
    "codex": "🔷",
    "trigon": "🔺",
    "rekonise": "🔍",
    "linkvertise": "🔗",
    "delta": "🔺",
    "krnl": "⚡",
    "platoboost": "🚀",
    "paster-so": "📋",
    "cuttlinks": "✂️",
    "boost-ink-and-bst-gg": "🚀",
    "keyguardian": "🔐",
    "bstshrt": "⚡",
    "nicuse-getkey": "🔑",
    "adfoc.us": "📢",
    "bit.do": "🔗",
    "bit.ly": "🔗",
    "blox-script": "🎮",
    "boost.ink": "🚀",
    "cl.gy": "🔗",
    "cuty-cuttlinks": "✂️",
    "getpolsec": "🔒",
    "goo.gl": "🔗",
    "is.gd": "🔗",
    "ldnesfspublic": "📁",
    "link-hub.net": "🌐",
    "link-unlock-complete": "🔓",
    "link4m.com": "🔗",
    "linkunlock": "🔓",
    "linkunlocker.com": "🔓",
    "lockr": "🔒",
    "mboost": "🚀",
    "mediafire": "📁",
    "overdrivehub": "🎮",
    "paste-drop.com": "📋",
    "pastebin.com": "📋",
    "pastes_io": "📋",
    "quartyz": "💎",
    "rebrand.ly": "🔗",
    "rekonise.com": "🔍",
    "rentry.co": "📝",
    "rinku-pro": "🔗",
    "rkns.link": "🔗",
    "shorteners-and-direct": "🔗",
    "shorter.me": "🔗",
    "socialwolvez.com": "🐺",
    "sub2get.com": "📺",
    "sub2unlock.net": "🔓",
    "sub4unlock.com": "🔓",
    "subfinal": "📺",
    "t.co": "🔗",
    "t.ly": "🔗",
    "tiny.cc": "🔗",
    "tinylink.onl": "🔗",
    "tinyurl.com": "🔗",
    "tpi.li": "🔗",
    "unlocknow.net": "🔓",
    "v.gd": "🔗",
    "work-ink": "💼",
    "ytsubme": "📺",
    "ace-bypass.com": "🎯"
}

SERVICE_STATUS_FILE = 'service_status.json'

def load_service_status():
    try:
        if os.path.exists(SERVICE_STATUS_FILE):
            with open(SERVICE_STATUS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading service status: {e}")
    return {service: "online" for service in SUPPORTED_SERVICES}

def save_service_status(status):
    try:
        with open(SERVICE_STATUS_FILE, 'w') as f:
            json.dump(status, f, indent=2)
    except Exception as e:
        print(f"Error saving service status: {e}")

service_preferences = load_service_preferences()
service_status = load_service_status()

def contains_junkie(text: str) -> bool:
    if not text:
        return False
    text_lower = text.lower()
    return 'junkie' in text_lower

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
                return service_preferences.get(service, True)
        return False
    except:
        return False

def get_service_name(url: str) -> str:
    try:
        parsed = urlparse(url.lower())
        domain = parsed.netloc.replace('www.', '')
        
        if 'platoboost' in domain or 'gateway' in domain:
            return 'platoboost'
        if 'delta' in domain:
            return 'delta'
        if 'krnl' in domain:
            return 'krnl'

        for service in SUPPORTED_SERVICES:
            if service in domain or domain in service:
                return service
        return domain
    except:
        return "unknown"

def get_service_emoji(service: str) -> str:
    return SERVICE_EMOJIS.get(service, "🔗")

async def log_bypass_to_channel(user: Union[discord.User, discord.Member], guild: discord.Guild, link: str, time_taken: float, result_type: str):
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

async def bypass_link(link: str, use_cache: bool = True) -> dict:
    start_time = time.time()

    if contains_junkie(link):
        bypass_stats['junkie_blocked'] = bypass_stats.get('junkie_blocked', 0) + 1
        save_stats(bypass_stats)
        time_taken = round(time.time() - start_time, 2)
        return {
            'success': False,
            'error': 'Junkie links are not supported anymore',
            'is_junkie': True,
            'time_taken': time_taken,
            'from_cache': False
        }

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

                    if contains_junkie(str(loadstring)) or contains_junkie(str(bypassed_url)):
                        bypass_stats['junkie_blocked'] = bypass_stats.get('junkie_blocked', 0) + 1
                        save_stats(bypass_stats)
                        return {
                            'success': False,
                            'error': 'Junkie links are not supported anymore',
                            'is_junkie': True,
                            'time_taken': time_taken,
                            'from_cache': False
                        }

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

class CopyContentButton(discord.ui.Button):
    def __init__(self, content: str, content_type: str):
        super().__init__(
            label=f"📋 Copy {content_type}",
            style=discord.ButtonStyle.primary,
            custom_id=f"copy_{content_type.lower()}"
        )
        self.content = content
        self.content_type = content_type

    async def callback(self, interaction: discord.Interaction):
        is_dm = interaction.guild is None

        if len(self.content) <= 1900:
            message_content = f"📋 **{self.content_type}**\n\n`{self.content}`"
            await interaction.response.send_message(content=message_content, ephemeral=not is_dm)
        else:
            import io
            file_ext = "lua" if "loadstring" in self.content_type.lower() else "txt"
            filename = f"{self.content_type.lower().replace(' ', '_')}.{file_ext}"

            file_content = io.BytesIO(self.content.encode('utf-8'))
            file = discord.File(file_content, filename=filename)

            download_message = f"📋 **{self.content_type} - Download File**\n\n**File Size:** {len(self.content)} characters\n\n✅ Full {self.content_type.lower()} attached!\n\nDownload the file to access the complete content.\n\n*Requested by {interaction.user.name}*"

            if is_dm:
                await interaction.response.send_message(
                    content=download_message,
                    file=file
                )
            else:
                ack_message = f"📋 **Preparing Download...**\n\nSending your {self.content_type.lower()} as a file..."
                await interaction.response.send_message(content=ack_message, ephemeral=True)

                try:
                    file_content_dm = io.BytesIO(self.content.encode('utf-8'))
                    file_dm = discord.File(file_content_dm, filename=filename)
                    await interaction.user.send(content=download_message, file=file_dm)

                    success_message = f"✅ **File Sent!**\n\nCheck your DMs for the full {self.content_type.lower()} file!"
                    await interaction.edit_original_response(content=success_message)
                except discord.Forbidden:
                    file_content2 = io.BytesIO(self.content.encode('utf-8'))
                    file2 = discord.File(file_content2, filename=filename)

                    await interaction.followup.send(
                        content=f"{interaction.user.mention} - Here's your {self.content_type.lower()} file:\n\n{download_message}",
                        file=file2
                    )

class CopyButtonView(View):
    def __init__(self, content: str, content_type: str, url: Optional[str] = None):
        super().__init__(timeout=None)
        self.add_item(CopyContentButton(content, content_type))
        if url and url.startswith(('http://', 'https://')):
            self.add_item(Button(
                label="🔗 Open Link",
                style=discord.ButtonStyle.link,
                url=url
            ))

class CopyLinkView(View):
    def __init__(self, bypassed_url: str):
        super().__init__(timeout=None)
        self.add_item(CopyContentButton(bypassed_url, "Link"))
        self.add_item(Button(
            label="🔗 Open Bypassed Link",
            style=discord.ButtonStyle.link,
            url=bypassed_url
        ))

class BypassModal(Modal):
    link_input = TextInput(
        label='Link to Bypass',
        placeholder='Enter the link you want to bypass',
        required=True,
        style=discord.TextStyle.short,
        max_length=500
    )

    def __init__(self):
        super().__init__(title='🔓 Bypass Link')

    async def on_submit(self, interaction: discord.Interaction):
        link_to_bypass = self.link_input.value.strip()
        
        service_name = get_service_name(link_to_bypass)
        service_emoji = get_service_emoji(service_name)
        
        start_time = time.time()
        
        loading_embed = discord.Embed(
            title=f"{service_emoji} Bypassing {service_name.title()}",
            description=f"⏳ **Processing your link...**\n\n`{link_to_bypass[:80]}{'...' if len(link_to_bypass) > 80 else ''}`\n\n🕐 **Elapsed:** 0.0s",
            color=discord.Color.blue()
        )
        loading_embed.set_footer(text="Bypass Bot • Hang tight!")
        
        await interaction.response.send_message(
            embed=loading_embed,
            ephemeral=True
        )

        if contains_junkie(link_to_bypass):
            await interaction.edit_original_response(
                embed=discord.Embed(
                    title="🚫 Junkie Links Not Supported",
                    description="Junkie links are not supported anymore\n\nPlease use a different link service.",
                    color=discord.Color.red()
                ).set_footer(text="Bypass Bot")
            )
            return
        
        async def update_elapsed_time():
            for i in range(30):
                await asyncio.sleep(0.5)
                elapsed = round(time.time() - start_time, 1)
                loading_embed.description = f"⏳ **Processing your link...**\n\n`{link_to_bypass[:80]}{'...' if len(link_to_bypass) > 80 else ''}`\n\n🕐 **Elapsed:** {elapsed}s"
                try:
                    await interaction.edit_original_response(embed=loading_embed)
                except:
                    break
        
        timer_task = asyncio.create_task(update_elapsed_time())
        
        try:
            result = await bypass_link(link_to_bypass)
        finally:
            timer_task.cancel()

        if result['success']:
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
                    description=f"**Original Link:**\n`{link_to_bypass[:100]}`\n\n⏱️ **Time Taken:** {result['time_taken']}s\n{cache_indicator}\n\n💡 **Click the button below to copy the full loadstring!**",
                    color=discord.Color.green()
                )

                if len(loadstring) <= 500:
                    embed.add_field(
                        name="📋 Loadstring Preview",
                        value=f"```lua\n{loadstring}\n```",
                        inline=False
                    )
                else:
                    preview = loadstring[:500]
                    embed.add_field(
                        name="📋 Loadstring Preview (Click Copy Button for Full Script)",
                        value=f"```lua\n{preview}...\n```\n*Preview only. Full script is {len(loadstring)} characters.*",
                        inline=False
                    )

                embed.set_footer(text="Bypass Bot | Only you can see this")

                view = CopyButtonView(loadstring, "Loadstring")
                await interaction.edit_original_response(embed=embed, view=view)
            elif result['type'] == 'url':
                bypassed_url = result['result']
                embed = discord.Embed(
                    title="✅ Link Bypassed Successfully",
                    description=f"**Original Link:**\n`{link_to_bypass[:100]}`\n\n**Bypassed Link:**\n`{bypassed_url}`\n\n⏱️ **Time Taken:** {result['time_taken']}s\n{cache_indicator}",
                    color=discord.Color.green()
                )
                embed.set_footer(text="Bypass Bot | Only you can see this")

                view = CopyLinkView(bypassed_url)
                await interaction.edit_original_response(embed=embed, view=view)
        else:
            if result.get('is_junkie'):
                await interaction.edit_original_response(
                    embed=discord.Embed(
                        title="🚫 Junkie Links Not Supported",
                        description="Junkie links are not supported anymore\n\nPlease use a different link service.",
                        color=discord.Color.red()
                    ).set_footer(text="Bypass Bot")
                )
                return

            error_description = f"**Error:** {result['error']}\n\n⏱️ **Time Taken:** {result.get('time_taken', 'N/A')}s"

            if ai_service:
                try:
                    ai_help = await ai_service.get_helpful_error_message(
                        result['error'],
                        link_to_bypass
                    )
                    error_description += f"\n\n💡 **Troubleshooting:**\n{ai_help}"
                except:
                    pass

            await interaction.edit_original_response(
                embed=discord.Embed(
                    title="❌ Bypass Failed",
                    description=error_description,
                    color=discord.Color.red()
                ).set_footer(text="Bypass Bot")
            )

class PanelBypassModal(Modal):
    link_input = TextInput(
        label='Link to Bypass',
        placeholder='Enter the link you want to bypass',
        required=True,
        style=discord.TextStyle.short,
        max_length=500
    )

    def __init__(self):
        super().__init__(title='🔓 Bypass Link')

    async def on_submit(self, interaction: discord.Interaction):
        link_to_bypass = self.link_input.value.strip()
        
        service_name = get_service_name(link_to_bypass)
        service_emoji = get_service_emoji(service_name)
        
        start_time = time.time()
        
        loading_embed = discord.Embed(
            title=f"{service_emoji} Bypassing {service_name.title()}",
            description=f"⏳ **Processing your link...**\n\n`{link_to_bypass[:80]}{'...' if len(link_to_bypass) > 80 else ''}`\n\n🕐 **Elapsed:** 0.0s",
            color=discord.Color.blue()
        )
        loading_embed.set_footer(text="Bypass Bot • Hang tight!")
        
        await interaction.response.send_message(
            embed=loading_embed,
            ephemeral=True
        )

        if contains_junkie(link_to_bypass):
            await interaction.edit_original_response(
                embed=discord.Embed(
                    title="🚫 Junkie Links Not Supported",
                    description="Junkie links are not supported anymore\n\nPlease use a different link service.",
                    color=discord.Color.red()
                ).set_footer(text="Bypass Bot")
            )
            return
        
        async def update_elapsed_time():
            for i in range(30):
                await asyncio.sleep(0.5)
                elapsed = round(time.time() - start_time, 1)
                loading_embed.description = f"⏳ **Processing your link...**\n\n`{link_to_bypass[:80]}{'...' if len(link_to_bypass) > 80 else ''}`\n\n🕐 **Elapsed:** {elapsed}s"
                try:
                    await interaction.edit_original_response(embed=loading_embed)
                except:
                    break
        
        timer_task = asyncio.create_task(update_elapsed_time())
        
        try:
            result = await bypass_link(link_to_bypass)
        finally:
            timer_task.cancel()

        if result['success']:
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
                    description=f"**Original Link:**\n`{link_to_bypass[:100]}`\n\n⏱️ **Time Taken:** {result['time_taken']}s\n{cache_indicator}\n\n💡 **Click the button below to copy the full loadstring!**",
                    color=discord.Color.green()
                )

                if len(loadstring) <= 500:
                    embed.add_field(
                        name="📋 Loadstring Preview",
                        value=f"```lua\n{loadstring}\n```",
                        inline=False
                    )
                else:
                    preview = loadstring[:500]
                    embed.add_field(
                        name="📋 Loadstring Preview (Click Copy Button for Full Script)",
                        value=f"```lua\n{preview}...\n```\n*Preview only. Full script is {len(loadstring)} characters.*",
                        inline=False
                    )

                embed.set_footer(text="Bypass Bot | Only you can see this")

                view = CopyButtonView(loadstring, "Loadstring")
                await interaction.edit_original_response(embed=embed, view=view)
            elif result['type'] == 'url':
                bypassed_url = result['result']
                embed = discord.Embed(
                    title="✅ Link Bypassed Successfully",
                    description=f"**Original Link:**\n`{link_to_bypass[:100]}`\n\n**Bypassed Link:**\n`{bypassed_url}`\n\n⏱️ **Time Taken:** {result['time_taken']}s\n{cache_indicator}",
                    color=discord.Color.green()
                )
                embed.set_footer(text="Bypass Bot | Only you can see this")

                view = CopyLinkView(bypassed_url)
                await interaction.edit_original_response(embed=embed, view=view)
        else:
            if result.get('is_junkie'):
                await interaction.edit_original_response(
                    embed=discord.Embed(
                        title="🚫 Junkie Links Not Supported",
                        description="Junkie links are not supported anymore\n\nPlease use a different link service.",
                        color=discord.Color.red()
                    ).set_footer(text="Bypass Bot")
                )
                return

            error_description = f"**Error:** {result['error']}\n\n⏱️ **Time Taken:** {result.get('time_taken', 'N/A')}s"

            if ai_service:
                try:
                    ai_help = await ai_service.get_helpful_error_message(
                        result['error'],
                        link_to_bypass
                    )
                    error_description += f"\n\n💡 **Troubleshooting:**\n{ai_help}"
                except:
                    pass

            await interaction.edit_original_response(
                embed=discord.Embed(
                    title="❌ Bypass Failed",
                    description=error_description,
                    color=discord.Color.red()
                ).set_footer(text="Bypass Bot")
            )

class BypassPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔓 Bypass Link", style=discord.ButtonStyle.primary, custom_id="panel_bypass_button")
    async def bypass_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(PanelBypassModal())

class SayModal(Modal):
    message_input = TextInput(
        label='Message',
        placeholder='Enter the message you want the bot to say',
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=2000
    )

    def __init__(self):
        super().__init__(title='💬 Say Message')

    async def on_submit(self, interaction: discord.Interaction):
        message_content = self.message_input.value

        await interaction.response.send_message(
            embed=discord.Embed(
                title="✅ Message Sent",
                description=f"Message sent successfully!",
                color=discord.Color.green()
            ).set_footer(text="Bypass Bot"),
            ephemeral=True
        )

        if interaction.channel and isinstance(interaction.channel, (discord.TextChannel, discord.Thread)):
            await interaction.channel.send(message_content)

class EmbedModal(Modal):
    title_input = TextInput(
        label='Embed Title',
        placeholder='Enter the title for the embed',
        required=True,
        style=discord.TextStyle.short,
        max_length=256
    )

    description_input = TextInput(
        label='Embed Description',
        placeholder='Enter the description for the embed',
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=4000
    )

    color_input = TextInput(
        label='Embed Color (hex code)',
        placeholder='Enter hex color code (e.g., #FF0000 for red)',
        required=False,
        style=discord.TextStyle.short,
        max_length=7
    )

    def __init__(self):
        super().__init__(title='📝 Create Embed')

    async def on_submit(self, interaction: discord.Interaction):
        title = self.title_input.value
        description = self.description_input.value
        color_hex = self.color_input.value.strip()

        try:
            if color_hex and color_hex.startswith('#'):
                color = discord.Color(int(color_hex[1:], 16))
            else:
                color = discord.Color.blue()
        except:
            color = discord.Color.blue()

        embed = discord.Embed(
            title=title,
            description=description,
            color=color
        )

        await interaction.response.send_message(
            embed=discord.Embed(
                title="✅ Embed Created",
                description="Custom embed has been created successfully!",
                color=discord.Color.green()
            ).set_footer(text="Bypass Bot"),
            ephemeral=True
        )

        if interaction.channel and isinstance(interaction.channel, (discord.TextChannel, discord.Thread)):
            await interaction.channel.send(embed=embed)

class ConfigModal(Modal):
    bypass_api_key_input = TextInput(
        label='Bypass API Key',
        placeholder='Enter your Bypass API key',
        required=False,
        style=discord.TextStyle.short,
        max_length=200
    )

    openai_api_key_input = TextInput(
        label='OpenAI API Key',
        placeholder='Enter your OpenAI API key (optional)',
        required=False,
        style=discord.TextStyle.short,
        max_length=200
    )

    def __init__(self):
        super().__init__(title='⚙️ Configure API Keys')

    async def on_submit(self, interaction: discord.Interaction):
        bypass_key = self.bypass_api_key_input.value.strip()
        openai_key = self.openai_api_key_input.value.strip()

        env_file = '.env'
        updated = []

        if bypass_key:
            set_key(env_file, 'BYPASS_API_KEY', bypass_key)
            os.environ['BYPASS_API_KEY'] = bypass_key
            global BYPASS_API_KEY
            BYPASS_API_KEY = bypass_key
            updated.append('Bypass API Key')

        if openai_key:
            set_key(env_file, 'OPENAI_API_KEY', openai_key)
            os.environ['OPENAI_API_KEY'] = openai_key
            global OPENAI_API_KEY, ai_service
            OPENAI_API_KEY = openai_key
            ai_service = AIService(openai_key)
            updated.append('OpenAI API Key')

        if updated:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="✅ Configuration Updated",
                    description=f"Successfully updated: {', '.join(updated)}\n\nRestart the bot for changes to take full effect.",
                    color=discord.Color.green()
                ).set_footer(text="Bypass Bot"),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="ℹ️ No Changes",
                    description="No API keys were provided.",
                    color=discord.Color.blue()
                ).set_footer(text="Bypass Bot"),
                ephemeral=True
            )

class BotInfoView(View):
    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(Button(label="🔗 Join Our Discord Server", url="https://discord.gg/fUzxqhjWZ", style=discord.ButtonStyle.link))

class SupportedServicesView(View):
    def __init__(self, services_per_page: int = 15):
        super().__init__(timeout=180)
        self.services_per_page = services_per_page
        self.current_page = 0
        self.total_pages = (len(SUPPORTED_SERVICES) + services_per_page - 1) // services_per_page

        self.first_button = Button(label="⏮️", style=discord.ButtonStyle.gray, disabled=True)
        self.prev_button = Button(label="◀️", style=discord.ButtonStyle.primary, disabled=True)
        self.next_button = Button(label="▶️", style=discord.ButtonStyle.primary, disabled=self.total_pages <= 1)
        self.last_button = Button(label="⏭️", style=discord.ButtonStyle.gray, disabled=self.total_pages <= 1)

        self.first_button.callback = self.first_page
        self.prev_button.callback = self.previous_page
        self.next_button.callback = self.next_page
        self.last_button.callback = self.last_page

        self.add_item(self.first_button)
        self.add_item(self.prev_button)
        self.add_item(self.next_button)
        self.add_item(self.last_button)

    def create_embed(self) -> discord.Embed:
        start_idx = self.current_page * self.services_per_page
        end_idx = min(start_idx + self.services_per_page, len(SUPPORTED_SERVICES))

        services_on_page = SUPPORTED_SERVICES[start_idx:end_idx]

        embed = discord.Embed(
            title="🌐 Supported Bypass Services",
            description=f"Here are all the bypass services supported by Bypass Bot.\n\n**Total Services:** {len(SUPPORTED_SERVICES)}",
            color=discord.Color.blue()
        )

        services_text = "\n".join([f"• `{service}`" for service in services_on_page])
        embed.add_field(
            name=f"Services (Page {self.current_page + 1}/{self.total_pages})",
            value=services_text,
            inline=False
        )

        embed.set_footer(text=f"Page {self.current_page + 1} of {self.total_pages}")
        return embed

    def update_buttons(self):
        self.first_button.disabled = self.current_page == 0
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page >= self.total_pages - 1
        self.last_button.disabled = self.current_page >= self.total_pages - 1

    async def first_page(self, interaction: discord.Interaction):
        self.current_page = 0
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    async def previous_page(self, interaction: discord.Interaction):
        self.current_page = max(0, self.current_page - 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    async def next_page(self, interaction: discord.Interaction):
        self.current_page = min(self.total_pages - 1, self.current_page + 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    async def last_page(self, interaction: discord.Interaction):
        self.current_page = self.total_pages - 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

class ServiceToggleView(View):
    def __init__(self, services_per_page: int = 5):
        super().__init__(timeout=180)
        self.services_per_page = services_per_page
        self.current_page = 0
        self.total_services = len(SUPPORTED_SERVICES)
        self.total_pages = (self.total_services + services_per_page - 1) // services_per_page

        self.first_button = Button(label="⏮️", style=discord.ButtonStyle.gray, row=4)
        self.prev_button = Button(label="◀️", style=discord.ButtonStyle.primary, row=4)
        self.next_button = Button(label="▶️", style=discord.ButtonStyle.primary, row=4)
        self.last_button = Button(label="⏭️", style=discord.ButtonStyle.gray, row=4)

        self.first_button.callback = self.first_page
        self.prev_button.callback = self.previous_page
        self.next_button.callback = self.next_page
        self.last_button.callback = self.last_page

        self.refresh_buttons()
        self.update_buttons()

    def refresh_buttons(self):
        self.clear_items()

        start_idx = self.current_page * self.services_per_page
        end_idx = min(start_idx + self.services_per_page, self.total_services)

        for idx in range(start_idx, end_idx):
            service = SUPPORTED_SERVICES[idx]
            is_enabled = service_preferences.get(service, True)
            label = f"{'✅' if is_enabled else '❌'} {service[:20]}"
            style = discord.ButtonStyle.green if is_enabled else discord.ButtonStyle.red
            button = Button(label=label, style=style, row=idx - start_idx)
            button.callback = self.create_toggle_callback(service)
            self.add_item(button)

        self.add_item(self.first_button)
        self.add_item(self.prev_button)
        self.add_item(self.next_button)
        self.add_item(self.last_button)

    def create_toggle_callback(self, service: str):
        async def callback(interaction: discord.Interaction):
            global service_preferences
            service_preferences[service] = not service_preferences.get(service, True)
            save_service_preferences(service_preferences)
            self.refresh_buttons()
            await interaction.response.edit_message(embed=self.create_embed(), view=self)
        return callback

    def create_embed(self) -> discord.Embed:
        start_idx = self.current_page * self.services_per_page
        end_idx = min(start_idx + self.services_per_page, self.total_services)
        enabled_count = sum(1 for s in SUPPORTED_SERVICES if service_preferences.get(s, True))

        embed = discord.Embed(
            title="🔧 Service Preferences",
            description=f"Toggle individual bypass services on/off.\n\n**Enabled:** {enabled_count}/{self.total_services} services\n\nClick a service to toggle it.",
            color=discord.Color.blue()
        )

        embed.set_footer(text=f"Page {self.current_page + 1} of {self.total_pages} | Services {start_idx + 1}-{end_idx}")
        return embed

    def update_buttons(self):
        self.first_button.disabled = self.current_page == 0
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page >= self.total_pages - 1
        self.last_button.disabled = self.current_page >= self.total_pages - 1

    async def first_page(self, interaction: discord.Interaction):
        self.current_page = 0
        self.update_buttons()
        self.refresh_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    async def previous_page(self, interaction: discord.Interaction):
        self.current_page = max(0, self.current_page - 1)
        self.update_buttons()
        self.refresh_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    async def next_page(self, interaction: discord.Interaction):
        self.current_page = min(self.total_pages - 1, self.current_page + 1)
        self.update_buttons()
        self.refresh_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    async def last_page(self, interaction: discord.Interaction):
        self.current_page = self.total_pages - 1
        self.update_buttons()
        self.refresh_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

class BypassBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"✅ Synced commands for {self.user}")

bot = BypassBot()

@bot.event
async def on_ready():
    if bot.user:
        activity = discord.Streaming(
            name=f"/bypass | {len(bot.guilds)} servers",
            url="https://www.twitch.tv/bypass"
        )
        await bot.change_presence(activity=activity, status=discord.Status.online)
        print(f"✅ {bot.user.name} is online!")
        print(f"🌐 Connected to {len(bot.guilds)} servers")
        print(f"👥 Serving {sum(g.member_count for g in bot.guilds if g.member_count)} users")

@bot.tree.command(name="bypass", description="Open the link bypass modal")
async def bypass_command(interaction: discord.Interaction):
    await interaction.response.send_modal(BypassModal())

@bot.tree.command(name="say", description="[ADMIN] Make the bot say a message")
async def say_command(interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Permission Denied",
                description="You need **Administrator** permissions to use this command.",
                color=discord.Color.red()
            ).set_footer(text="Bypass Bot"),
            ephemeral=True
        )
        return

    await interaction.response.send_modal(SayModal())

@bot.tree.command(name="embed", description="[ADMIN] Create a custom embed message")
async def embed_command(interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Permission Denied",
                description="You need **Administrator** permissions to use this command.",
                color=discord.Color.red()
            ).set_footer(text="Bypass Bot"),
            ephemeral=True
        )
        return

    await interaction.response.send_modal(EmbedModal())

@bot.tree.command(name="config", description="[ADMIN] Configure bot API keys")
async def config_command(interaction: discord.Interaction):
    if interaction.user.id != BOT_OWNER_ID:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Access Denied",
                description="This command is only available to the bot owner.",
                color=discord.Color.red()
            ),
            ephemeral=True
        )
        return

    await interaction.response.send_modal(ConfigModal())

@bot.tree.command(name="services", description="[ADMIN] Toggle bypass services on/off")
async def services_command(interaction: discord.Interaction):
    if interaction.user.id != BOT_OWNER_ID:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Access Denied",
                description="This command is only available to the bot owner.",
                color=discord.Color.red()
            ),
            ephemeral=True
        )
        return

    view = ServiceToggleView()
    await interaction.response.send_message(
        embed=view.create_embed(),
        view=view,
        ephemeral=True
    )

@bot.tree.command(name="info", description="Get information about Bypass Bot")
async def info_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="ℹ️ Bypass Bot Information",
        description="Welcome to **Bypass Bot**! 🚀\n\nA powerful link bypass bot that supports dozens of link shortener and script protection services.",
        color=discord.Color.blue()
    )

    junkie_blocked = bypass_stats.get('junkie_blocked', 0)
    embed.add_field(
        name="📊 Statistics",
        value=f"**Total Bypassed:** {bypass_stats['total_bypassed']:,}\n**Loadstrings:** {bypass_stats['loadstrings']:,}\n**URLs:** {bypass_stats['urls']:,}\n**Failed:** {bypass_stats['failed']:,}\n**Cache Hits:** {bypass_stats['cached_hits']:,}\n**Junkie Blocked:** {junkie_blocked:,}",
        inline=True
    )

    embed.add_field(
        name="🎯 Features",
        value="• Fast bypass processing\n• Smart caching system\n• Auto-bypass in channels\n• Rate limiting protection\n• 50+ supported services\n• Mobile-friendly copy buttons",
        inline=True
    )

    embed.add_field(
        name="🔧 User Commands",
        value="`/bypass` - Bypass a link\n`/info` - Bot information\n`/supported` - View supported services\n`/stats` - View bot statistics",
        inline=False
    )

    embed.add_field(
        name="⚙️ Admin Commands",
        value="`/say` - Make bot say a message\n`/embed` - Create custom embeds\n`/panel` - Create bypass panel\n`/autobypass` - Enable auto-bypass\n`/disableautobypass` - Disable auto-bypass",
        inline=False
    )

    embed.set_footer(text="Bypass Bot | Fast & Reliable")
    embed.set_thumbnail(url=bot.user.display_avatar.url if bot.user else None)

    view = BotInfoView()
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="supported", description="View all supported bypass services")
async def supported_command(interaction: discord.Interaction):
    view = SupportedServicesView(services_per_page=15)
    await interaction.response.send_message(embed=view.create_embed(), view=view)

@bot.tree.command(name="stats", description="View detailed bot statistics")
async def stats_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📊 Bypass Bot Statistics",
        description="Here are the detailed statistics for Bypass Bot",
        color=discord.Color.blue()
    )

    junkie_blocked = bypass_stats.get('junkie_blocked', 0)
    embed.add_field(
        name="🔢 Total Statistics",
        value=f"**Total Bypassed:** {bypass_stats['total_bypassed']:,}\n**Loadstrings:** {bypass_stats['loadstrings']:,}\n**URLs:** {bypass_stats['urls']:,}\n**Failed Attempts:** {bypass_stats['failed']:,}\n**Cache Hits:** {bypass_stats['cached_hits']:,}\n**Junkie Blocked:** {junkie_blocked:,}",
        inline=True
    )

    if bypass_stats['total_bypassed'] > 0:
        success_rate = ((bypass_stats['total_bypassed'] / (bypass_stats['total_bypassed'] + bypass_stats['failed'])) * 100)
        cache_rate = ((bypass_stats['cached_hits'] / bypass_stats['total_bypassed']) * 100) if bypass_stats['total_bypassed'] > 0 else 0

        embed.add_field(
            name="📈 Performance",
            value=f"**Success Rate:** {success_rate:.1f}%\n**Cache Hit Rate:** {cache_rate:.1f}%\n**Total Requests:** {bypass_stats['total_bypassed'] + bypass_stats['failed']:,}",
            inline=True
        )

    if bypass_stats.get('service_stats'):
        top_services = sorted(bypass_stats['service_stats'].items(), key=lambda x: x[1], reverse=True)[:5]
        services_text = "\n".join([f"**{service}:** {count:,}" for service, count in top_services])
        embed.add_field(
            name="🏆 Top Services",
            value=services_text,
            inline=False
        )

    embed.set_footer(text="Bypass Bot | Statistics")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="status", description="View service status for all supported games/services")
async def status_command(interaction: discord.Interaction):
    online_services = []
    offline_services = []
    
    for service in SUPPORTED_SERVICES:
        status = service_status.get(service, "online")
        emoji = get_service_emoji(service)
        status_indicator = "🟢" if status == "online" else "🔴"
        
        if status == "online":
            online_services.append(f"{status_indicator} {emoji} `{service}`")
        else:
            offline_services.append(f"{status_indicator} {emoji} `{service}`")
    
    online_count = len(online_services)
    offline_count = len(offline_services)
    total_count = len(SUPPORTED_SERVICES)
    uptime_percentage = (online_count / total_count * 100) if total_count > 0 else 0
    
    online_text = ""
    if online_services:
        chunks = []
        for i in range(0, len(online_services), 3):
            chunk = online_services[i:i+3]
            chunks.append(" • ".join(chunk))
        online_text = "\n".join(chunks)
    else:
        online_text = "*No services online*"
    
    offline_text = ""
    if offline_services:
        chunks = []
        for i in range(0, len(offline_services), 3):
            chunk = offline_services[i:i+3]
            chunks.append(" • ".join(chunk))
        offline_text = "\n\n**⚠️ Offline Services:**\n" + "\n".join(chunks)
    
    description = f"**📊 Overall Status:** {uptime_percentage:.1f}% Uptime ({online_count}/{total_count} services)\n**🕒 Last Updated:** <t:{int(time.time())}:R>\n\n**✅ Online Services:**\n{online_text}{offline_text}"
    
    if len(description) > 4096:
        description = f"**📊 Overall Status:** {uptime_percentage:.1f}% Uptime ({online_count}/{total_count} services)\n**🕒 Last Updated:** <t:{int(time.time())}:R>\n\n**✅ Online:** {online_count} services\n**⚠️ Offline:** {offline_count} services\n\n*Use `/supported` to view all service names.*"
    
    embed = discord.Embed(
        title="🎮 Service Status Dashboard",
        description=description,
        color=discord.Color.green() if uptime_percentage >= 90 else discord.Color.orange() if uptime_percentage >= 50 else discord.Color.red()
    )
    
    embed.set_footer(text="Bypass Bot • Service Status")
    embed.timestamp = datetime.utcnow()
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="setstatus", description="[OWNER] Change service status")
@app_commands.describe(
    service="Service name to update",
    status="New status (online/offline)"
)
async def setstatus_command(interaction: discord.Interaction, service: str, status: str):
    if interaction.user.id != BOT_OWNER_ID:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Access Denied",
                description="This command is only available to the bot owner.",
                color=discord.Color.red()
            ),
            ephemeral=True
        )
        return
    
    service = service.lower()
    status = status.lower()
    
    if service not in SUPPORTED_SERVICES:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Invalid Service",
                description=f"Service `{service}` not found in supported services list.\n\nUse `/supported` to view all services.",
                color=discord.Color.red()
            ),
            ephemeral=True
        )
        return
    
    if status not in ["online", "offline"]:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Invalid Status",
                description="Status must be either `online` or `offline`.",
                color=discord.Color.red()
            ),
            ephemeral=True
        )
        return
    
    global service_status
    service_status[service] = status
    save_service_status(service_status)
    
    emoji = get_service_emoji(service)
    status_indicator = "🟢" if status == "online" else "🔴"
    
    await interaction.response.send_message(
        embed=discord.Embed(
            title="✅ Status Updated",
            description=f"{status_indicator} {emoji} **{service}** is now marked as **{status}**",
            color=discord.Color.green()
        ),
        ephemeral=True
    )

@bot.tree.command(name="panel", description="[ADMIN] Create a bypass panel with a button")
async def panel_command(interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Permission Denied",
                description="You need **Administrator** permissions to use this command.",
                color=discord.Color.red()
            ).set_footer(text="Bypass Bot"),
            ephemeral=True
        )
        return

    panel_embed = discord.Embed(
        title="🔓 Bypass Panel",
        description="Click the button below to bypass a link!\n\n**Features:**\n• Fast bypass processing\n• Smart caching system\n• 50+ supported services\n• AI-powered safety analysis\n• Private results (only you can see)\n\nYour bypass results will be sent as a private message that only you can see.",
        color=discord.Color.blue()
    )
    panel_embed.set_footer(text="Bypass Bot | Click the button to get started")

    if bot.user and bot.user.display_avatar:
        panel_embed.set_thumbnail(url=bot.user.display_avatar.url)

    view = BypassPanelView()

    await interaction.response.send_message(
        embed=discord.Embed(
            title="✅ Panel Created",
            description="Bypass panel has been created successfully!",
            color=discord.Color.green()
        ).set_footer(text="Bypass Bot"),
        ephemeral=True
    )

    if interaction.channel and isinstance(interaction.channel, (discord.TextChannel, discord.Thread)):
        await interaction.channel.send(embed=panel_embed, view=view)

@bot.tree.command(name="autobypass", description="Enable auto-bypass in a channel")
@app_commands.describe(channel="The channel to enable autobypass in")
async def autobypass_command(interaction: discord.Interaction, channel: discord.TextChannel):
    if not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Permission Denied",
                description="You need the **Manage Channels** permission to use this command.",
                color=discord.Color.red()
            ).set_footer(text="Bypass Bot"),
            ephemeral=True
        )
        return

    if not interaction.guild:
        return
    
    global autobypass_channels
    autobypass_channels[interaction.guild.id] = channel.id
    save_autobypass_channels(autobypass_channels)

    await interaction.response.send_message(
        embed=discord.Embed(
            title="✅ Auto-Bypass Enabled",
            description=f"Auto-bypass has been enabled in {channel.mention}!\n\nAny links posted in that channel will automatically be bypassed and sent to the user via DM.",
            color=discord.Color.green()
        ).set_footer(text="Bypass Bot"),
        ephemeral=True
    )

@bot.tree.command(name="disableautobypass", description="Disable auto-bypass in your server")
async def disableautobypass_command(interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Permission Denied",
                description="You need the **Manage Channels** permission to use this command.",
                color=discord.Color.red()
            ).set_footer(text="Bypass Bot"),
            ephemeral=True
        )
        return

    if not interaction.guild:
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

@bot.tree.command(name="setlogs", description="[ADMIN] Set bypass logs channel")
@app_commands.describe(channel="The channel where bypass logs will be sent")
async def setlogs_command(interaction: discord.Interaction, channel: discord.TextChannel):
    if interaction.user.id != BOT_OWNER_ID:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Access Denied",
                description="This command is only available to the bot owner.",
                color=discord.Color.red()
            ),
            ephemeral=True
        )
        return

    if not interaction.guild:
        return

    global log_channels
    log_channels[interaction.guild.id] = channel.id
    save_log_channels(log_channels)

    await interaction.response.send_message(
        embed=discord.Embed(
            title="✅ Bypass Logs Channel Set",
            description=f"Bypass logs will now be sent to {channel.mention}!",
            color=discord.Color.green()
        ).set_footer(text="Bypass Bot Logger"),
        ephemeral=True
    )

@bot.tree.command(name="blacklist", description="[ADMIN] Manage user blacklist")
@app_commands.describe(
    action="Action to perform: add, remove, or list",
    user="User to blacklist/unblacklist",
    hwid="HWID to blacklist/unblacklist"
)
async def blacklist_command(
    interaction: discord.Interaction,
    action: str,
    user: Optional[discord.User] = None,
    hwid: Optional[str] = None
):
    if interaction.user.id != BOT_OWNER_ID:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Access Denied",
                description="This command is only available to the bot owner.",
                color=discord.Color.red()
            ),
            ephemeral=True
        )
        return

    action = action.lower()

    if action == "list":
        blacklist_data = user_activity.get_blacklist_data()
        embed = discord.Embed(
            title="🚫 Blacklist",
            description=f"**Total Blacklisted Users:** {blacklist_data['total_users']}\n**Total Blacklisted HWIDs:** {blacklist_data['total_hwids']}",
            color=discord.Color.red()
        )

        if blacklist_data['user_ids']:
            users_text = "\n".join([f"<@{uid}> (`{uid}`)" for uid in blacklist_data['user_ids'][:10]])
            embed.add_field(
                name="🔒 Blacklisted Users",
                value=users_text,
                inline=False
            )

        if blacklist_data['hwids']:
            hwids_text = "\n".join([f"`{hwid}`" for hwid in blacklist_data['hwids'][:10]])
            embed.add_field(
                name="🔑 Blacklisted HWIDs",
                value=hwids_text,
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if action == "add":
        if user:
            if user_activity.blacklist_user(user.id):
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="✅ User Blacklisted",
                        description=f"Successfully blacklisted {user.mention} (`{user.id}`).",
                        color=discord.Color.green()
                    ),
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="ℹ️ Already Blacklisted",
                        description=f"{user.mention} is already blacklisted.",
                        color=discord.Color.blue()
                    ),
                    ephemeral=True
                )
        elif hwid:
            if user_activity.blacklist_hwid(hwid.upper()):
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="✅ HWID Blacklisted",
                        description=f"Successfully blacklisted HWID `{hwid.upper()}`.",
                        color=discord.Color.green()
                    ),
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="ℹ️ Already Blacklisted",
                        description=f"HWID `{hwid.upper()}` is already blacklisted.",
                        color=discord.Color.blue()
                    ),
                    ephemeral=True
                )
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Missing Parameter",
                    description="Please provide either a user or HWID to blacklist.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
    elif action == "remove":
        if user:
            if user_activity.unblacklist_user(user.id):
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="✅ User Unblacklisted",
                        description=f"Successfully removed {user.mention} from the blacklist.",
                        color=discord.Color.green()
                    ),
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="ℹ️ Not Blacklisted",
                        description=f"{user.mention} is not in the blacklist.",
                        color=discord.Color.blue()
                    ),
                    ephemeral=True
                )
        elif hwid:
            if user_activity.unblacklist_hwid(hwid.upper()):
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="✅ HWID Unblacklisted",
                        description=f"Successfully removed HWID `{hwid.upper()}` from the blacklist.",
                        color=discord.Color.green()
                    ),
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="ℹ️ Not Blacklisted",
                        description=f"HWID `{hwid.upper()}` is not in the blacklist.",
                        color=discord.Color.blue()
                    ),
                    ephemeral=True
                )
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Missing Parameter",
                    description="Please provide either a user or HWID to unblacklist.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

class DMModal(Modal):
    message_input = TextInput(
        label='Message',
        placeholder='Enter your message',
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=2000
    )

    def __init__(self, target_user: Optional[discord.User] = None, broadcast: bool = False, guild: Optional[discord.Guild] = None):
        self.target_user = target_user
        self.broadcast = broadcast
        self.guild = guild
        title = "📢 Broadcast Message" if broadcast else f"💬 DM to {target_user.name if target_user else 'User'}"
        super().__init__(title=title)

    async def on_submit(self, interaction: discord.Interaction):
        message_content = self.message_input.value

        if self.broadcast and self.guild:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="⏳ Broadcasting...",
                    description=f"Sending message to all {self.guild.member_count} members...",
                    color=discord.Color.blue()
                ).set_footer(text="This may take a while"),
                ephemeral=True
            )

            success_count = 0
            failed_count = 0

            for member in self.guild.members:
                if member.bot:
                    continue

                try:
                    dm_embed = discord.Embed(
                        title="📢 Broadcast Message",
                        description=message_content,
                        color=discord.Color.blue()
                    )
                    dm_embed.set_footer(text=f"From {self.guild.name} | Sent by Bot Owner")
                    await member.send(embed=dm_embed)
                    success_count += 1
                    await asyncio.sleep(1)
                except discord.Forbidden:
                    failed_count += 1
                except Exception as e:
                    failed_count += 1

            await interaction.edit_original_response(
                embed=discord.Embed(
                    title="✅ Broadcast Complete",
                    description=f"**Successfully sent:** {success_count}\n**Failed:** {failed_count}\n\n**Message:**\n{message_content[:200]}",
                    color=discord.Color.green()
                ).set_footer(text="Bypass Bot")
            )

        elif self.target_user:
            try:
                dm_embed = discord.Embed(
                    title="💬 Direct Message",
                    description=message_content,
                    color=discord.Color.blue()
                )
                dm_embed.set_footer(text="From Bot Owner")
                await self.target_user.send(embed=dm_embed)

                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="✅ DM Sent",
                        description=f"Message successfully sent to {self.target_user.mention}!\n\n**Message:**\n{message_content[:200]}",
                        color=discord.Color.green()
                    ).set_footer(text="Bypass Bot"),
                    ephemeral=True
                )
            except discord.Forbidden:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="❌ DM Failed",
                        description=f"Could not send DM to {self.target_user.mention}. They may have DMs disabled.",
                        color=discord.Color.red()
                    ).set_footer(text="Bypass Bot"),
                    ephemeral=True
                )
            except Exception as e:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="❌ Error",
                        description=f"An error occurred: {str(e)[:200]}",
                        color=discord.Color.red()
                    ).set_footer(text="Bypass Bot"),
                    ephemeral=True
                )

@bot.tree.command(name="purge", description="[ADMIN] Delete a specified number of messages")
@app_commands.describe(amount="Number of messages to delete (1-100)")
async def purge_command(interaction: discord.Interaction, amount: int):
    if not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Permission Denied",
                description="You need **Manage Messages** permission to use this command.",
                color=discord.Color.red()
            ).set_footer(text="Bypass Bot"),
            ephemeral=True
        )
        return

    if amount < 1 or amount > 100:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Invalid Amount",
                description="Please specify a number between 1 and 100.",
                color=discord.Color.red()
            ).set_footer(text="Bypass Bot"),
            ephemeral=True
        )
        return

    if not interaction.channel or not isinstance(interaction.channel, discord.TextChannel):
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Invalid Channel",
                description="This command can only be used in text channels.",
                color=discord.Color.red()
            ).set_footer(text="Bypass Bot"),
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    try:
        deleted = await interaction.channel.purge(limit=amount)

        await interaction.followup.send(
            embed=discord.Embed(
                title="✅ Messages Purged",
                description=f"Successfully deleted **{len(deleted)}** message(s)!",
                color=discord.Color.green()
            ).set_footer(text="Bypass Bot"),
            ephemeral=True
        )
    except discord.Forbidden:
        await interaction.followup.send(
            embed=discord.Embed(
                title="❌ Permission Error",
                description="I don't have permission to delete messages in this channel.",
                color=discord.Color.red()
            ).set_footer(text="Bypass Bot"),
            ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(
            embed=discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {str(e)[:200]}",
                color=discord.Color.red()
            ).set_footer(text="Bypass Bot"),
            ephemeral=True
        )

@bot.tree.command(name="ban", description="[ADMIN] Ban a user from the server")
@app_commands.describe(
    user="The user to ban",
    reason="Reason for the ban (optional)"
)
async def ban_command(interaction: discord.Interaction, user: discord.Member, reason: Optional[str] = None):
    if not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Permission Denied",
                description="You need **Ban Members** permission to use this command.",
                color=discord.Color.red()
            ).set_footer(text="Bypass Bot"),
            ephemeral=True
        )
        return

    if user.id == interaction.user.id:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Invalid Action",
                description="You cannot ban yourself!",
                color=discord.Color.red()
            ).set_footer(text="Bypass Bot"),
            ephemeral=True
        )
        return

    if user.top_role >= interaction.user.top_role:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Permission Denied",
                description="You cannot ban this user as they have an equal or higher role than you.",
                color=discord.Color.red()
            ).set_footer(text="Bypass Bot"),
            ephemeral=True
        )
        return

    ban_reason = reason or "No reason provided"

    if not interaction.guild:
        return

    try:
        await user.ban(reason=f"Banned by {interaction.user.name if interaction.user else 'Unknown'} - {ban_reason}")

        await interaction.response.send_message(
            embed=discord.Embed(
                title="✅ User Banned",
                description=f"**User:** {user.mention} ({user.name})\n**Reason:** {ban_reason}\n**Banned by:** {interaction.user.mention}",
                color=discord.Color.red()
            ).set_footer(text="Bypass Bot"),
            ephemeral=True
        )

        try:
            await user.send(
                embed=discord.Embed(
                    title="🚫 You Have Been Banned",
                    description=f"You have been banned from **{interaction.guild.name}**.\n\n**Reason:** {ban_reason}",
                    color=discord.Color.red()
                ).set_footer(text="Bypass Bot")
            )
        except:
            pass

    except discord.Forbidden:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Permission Error",
                description="I don't have permission to ban this user.",
                color=discord.Color.red()
            ).set_footer(text="Bypass Bot"),
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {str(e)[:200]}",
                color=discord.Color.red()
            ).set_footer(text="Bypass Bot"),
            ephemeral=True
        )

@bot.tree.command(name="timeout", description="[ADMIN] Timeout a user for a specified duration")
@app_commands.describe(
    user="The user to timeout",
    duration="Duration in minutes (1-40320, max 28 days)",
    reason="Reason for the timeout (optional)"
)
async def timeout_command(interaction: discord.Interaction, user: discord.Member, duration: int, reason: Optional[str] = None):
    if not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Permission Denied",
                description="You need **Moderate Members** permission to use this command.",
                color=discord.Color.red()
            ).set_footer(text="Bypass Bot"),
            ephemeral=True
        )
        return

    if user.id == interaction.user.id:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Invalid Action",
                description="You cannot timeout yourself!",
                color=discord.Color.red()
            ).set_footer(text="Bypass Bot"),
            ephemeral=True
        )
        return

    if user.top_role >= interaction.user.top_role:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Permission Denied",
                description="You cannot timeout this user as they have an equal or higher role than you.",
                color=discord.Color.red()
            ).set_footer(text="Bypass Bot"),
            ephemeral=True
        )
        return

    if duration < 1 or duration > 40320:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Invalid Duration",
                description="Duration must be between 1 minute and 40,320 minutes (28 days).",
                color=discord.Color.red()
            ).set_footer(text="Bypass Bot"),
            ephemeral=True
        )
        return

    timeout_reason = reason or "No reason provided"
    timeout_duration = timedelta(minutes=duration)

    if not interaction.guild:
        return

    try:
        await user.timeout(timeout_duration, reason=f"Timed out by {interaction.user.name if interaction.user else 'Unknown'} - {timeout_reason}")

        duration_text = f"{duration} minute(s)"
        if duration >= 1440:
            days = duration // 1440
            remaining_mins = duration % 1440
            duration_text = f"{days} day(s)" + (f" {remaining_mins} minute(s)" if remaining_mins > 0 else "")
        elif duration >= 60:
            hours = duration // 60
            remaining_mins = duration % 60
            duration_text = f"{hours} hour(s)" + (f" {remaining_mins} minute(s)" if remaining_mins > 0 else "")

        await interaction.response.send_message(
            embed=discord.Embed(
                title="✅ User Timed Out",
                description=f"**User:** {user.mention} ({user.name})\n**Duration:** {duration_text}\n**Reason:** {timeout_reason}\n**By:** {interaction.user.mention}",
                color=discord.Color.orange()
            ).set_footer(text="Bypass Bot"),
            ephemeral=True
        )

        try:
            await user.send(
                embed=discord.Embed(
                    title="⏸️ You Have Been Timed Out",
                    description=f"You have been timed out in **{interaction.guild.name}**.\n\n**Duration:** {duration_text}\n**Reason:** {timeout_reason}",
                    color=discord.Color.orange()
                ).set_footer(text="Bypass Bot")
            )
        except:
            pass

    except discord.Forbidden:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Permission Error",
                description="I don't have permission to timeout this user.",
                color=discord.Color.red()
            ).set_footer(text="Bypass Bot"),
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {str(e)[:200]}",
                color=discord.Color.red()
            ).set_footer(text="Bypass Bot"),
            ephemeral=True
        )

@bot.tree.command(name="dm", description="[OWNER] Send a DM to a user or broadcast to everyone")
@app_commands.describe(
    mode="Choose 'user' to DM one person or 'broadcast' to DM everyone",
    user="The user to send a DM to (only for 'user' mode)"
)
async def dm_command(
    interaction: discord.Interaction,
    mode: str,
    user: Optional[discord.User] = None
):
    if interaction.user.id != BOT_OWNER_ID:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Access Denied",
                description="This command is only available to the bot owner.",
                color=discord.Color.red()
            ),
            ephemeral=True
        )
        return

    mode = mode.lower()

    if mode == "user":
        if not user:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Missing User",
                    description="Please specify a user to send a DM to.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
            return

        await interaction.response.send_modal(DMModal(target_user=user))

    elif mode == "broadcast":
        if not interaction.guild:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Server Only",
                    description="Broadcast mode can only be used in a server.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
            return

        await interaction.response.send_modal(DMModal(broadcast=True, guild=interaction.guild))

    else:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Invalid Mode",
                description="Please choose either 'user' or 'broadcast' mode.",
                color=discord.Color.red()
            ),
            ephemeral=True
        )

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.guild and message.guild.id in autobypass_channels:
        if message.channel.id == autobypass_channels[message.guild.id]:
            detected_link = detect_url(message.content)

            if detected_link:
                service_name = get_service_name(detected_link)
                service_emoji = get_service_emoji(service_name)
                
                if contains_junkie(detected_link):
                    try:
                        await message.delete()
                        await message.channel.send(
                            embed=discord.Embed(
                                description=f"🚫 {message.author.mention} - Junkie links are not supported anymore",
                                color=discord.Color.red()
                            ).set_footer(text="Bypass Bot"),
                            delete_after=15
                        )
                    except:
                        pass
                    return

                result = await bypass_link(detected_link)

                if result['success']:
                    if message.guild:
                        await log_bypass_to_channel(
                            message.author,
                            message.guild,
                            detected_link,
                            result['time_taken'],
                            result['type']
                        )
                    
                    try:
                        await message.delete()
                        await message.channel.send(
                            embed=discord.Embed(
                                description=f"{service_emoji} {message.author.mention} - **{service_name.title()}** link bypassed! Check your DMs!",
                                color=discord.Color.green()
                            ).set_footer(text="Bypass Bot • Auto-Bypass"),
                            delete_after=10
                        )

                        cache_indicator = "⚡ From Cache" if result.get('from_cache') else "✨ Fresh Result"

                        if result['type'] == 'loadstring':
                            loadstring = result['result']
                            embed = discord.Embed(
                                title=f"{service_emoji} Auto-Bypass: {service_name.title()} Loadstring",
                                description=f"**Original Link:**\n`{detected_link[:100]}`\n\n⏱️ **Time Taken:** {result['time_taken']}s\n{cache_indicator}",
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

                            embed.set_footer(text="Bypass Bot | Auto-Bypass")
                            await message.author.send(embed=embed)

                            if len(loadstring) > 500:
                                await message.author.send(f"```lua\n{loadstring}\n```")

                        elif result['type'] == 'url':
                            bypassed_url = result['result']
                            embed = discord.Embed(
                                title=f"{service_emoji} Auto-Bypass: {service_name.title()} Link",
                                description=f"**Original Link:**\n`{detected_link[:100]}`\n\n**Bypassed Link:**\n`{bypassed_url}`\n\n⏱️ **Time Taken:** {result['time_taken']}s\n{cache_indicator}",
                                color=discord.Color.green()
                            )
                            embed.set_footer(text="Bypass Bot | Auto-Bypass")
                            await message.author.send(embed=embed)
                    except:
                        await message.channel.send(
                            embed=discord.Embed(
                                description=f"❌ {message.author.mention} - I couldn't DM you. Please enable DMs from server members.",
                                color=discord.Color.red()
                            ).set_footer(text="Bypass Bot"),
                            delete_after=15
                        )
                else:
                    if result.get('is_junkie'):
                        try:
                            await message.delete()
                            await message.channel.send(
                                embed=discord.Embed(
                                    description=f"🚫 {message.author.mention} - Junkie links are not supported anymore",
                                    color=discord.Color.red()
                                ).set_footer(text="Bypass Bot"),
                                delete_after=15
                            )
                        except:
                            pass
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

if __name__ == "__main__":
    print("🚀 Starting Bypass Bot...")
    print(f"📦 Loading configurations...")
    print(f"⚡ Enhanced Features: Loaded")
    print(f"🔑 Bypass API Key: {'Set' if BYPASS_API_KEY else 'Not Set - Use /config to set'}")

    if not DISCORD_BOT_TOKEN:
        print("❌ ERROR: DISCORD_BOT_TOKEN not found in environment variables!")
        print("Please set DISCORD_BOT_TOKEN in your .env file")
        exit(1)

    bot.run(DISCORD_BOT_TOKEN)
