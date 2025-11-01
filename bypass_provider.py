import aiohttp
from urllib.parse import quote
import os
from typing import Optional, Dict

class BypassProvider:
    def __init__(self):
        pass
    
    async def bypass(self, link: str, session: aiohttp.ClientSession, timeout: int = 30) -> dict:
        encoded_link = quote(link)
        ace_api_key = os.getenv('BYPASS_API_KEY')
        
        if ace_api_key:
            ace_url = f"http://ace-bypass.com/api/bypass?url={encoded_link}&apikey={ace_api_key}"
            result = await self._try_api(ace_url, session, timeout, 'Ace Bypass')
            if result['success']:
                return result
        
        trw_url = f"https://trw.lat/api/bypass?url={encoded_link}&apikey=4b726d90-ebeb-4b89-9832-c4532eba994"
        result = await self._try_api(trw_url, session, timeout, 'TRW Bypass')
        return result
    
    async def _try_api(self, api_url: str, session: aiohttp.ClientSession, timeout: int, api_name: str) -> dict:
        try:
            async with session.get(
                api_url,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    loadstring = data.get('loadstring') or data.get('script') or data.get('code')
                    bypassed_url = data.get('destination') or data.get('result') or data.get('bypassed_url') or data.get('url')
                    
                    return {
                        'success': True,
                        'loadstring': loadstring,
                        'bypassed_url': bypassed_url,
                        'raw_data': data,
                        'api_name': api_name
                    }
                else:
                    error_text = await response.text()
                    return {
                        'success': False,
                        'error': f'{api_name} error {response.status}: {error_text[:200]}',
                        'api_name': api_name
                    }
        except Exception as e:
            return {
                'success': False,
                'error': f'{api_name} failed: {str(e)}',
                'api_name': api_name
            }
    
    def get_api_status(self) -> dict:
        ace_api_key = os.getenv('BYPASS_API_KEY')
        
        status = {
            'active': 'Ace Bypass (with TRW fallback)',
            'providers': {
                'ace-bypass': {
                    'name': 'Ace Bypass',
                    'enabled': True,
                    'requires_key': True,
                    'has_key': bool(ace_api_key),
                    'ready': bool(ace_api_key)
                },
                'trw-bypass': {
                    'name': 'TRW Bypass',
                    'enabled': True,
                    'requires_key': False,
                    'has_key': True,
                    'ready': True
                }
            }
        }
        
        return status
