import aiohttp
from urllib.parse import quote
import os
from typing import Optional, Dict

class BypassProvider:
    def __init__(self, bypass_api_key: Optional[str] = None, trw_api_key: Optional[str] = None, zen_api_key: Optional[str] = None, eas_api_key: Optional[str] = None):
        self.bypass_api_key = bypass_api_key or os.getenv('BYPASS_API_KEY')
        self.trw_api_key = trw_api_key or os.getenv('TRW_API_KEY')
        self.zen_api_key = zen_api_key or os.getenv('ZEN_API_KEY')
        self.eas_api_key = eas_api_key or os.getenv('EAS_API_KEY')
    
    async def bypass(self, link: str, session: aiohttp.ClientSession, timeout: int = 30) -> dict:
        encoded_link = quote(link)
        errors = []
        
        # Try Ace Bypass first if API key is available
        if self.bypass_api_key:
            ace_url = f"http://ace-bypass.com/api/bypass?url={encoded_link}&apikey={self.bypass_api_key}"
            result = await self._try_api_get(ace_url, session, timeout, 'Ace Bypass')
            if result['success']:
                return result
            else:
                errors.append(f"Ace Bypass: {result.get('error', 'Unknown error')}")
        
        # Fallback to TRW Bypass if Ace failed or wasn't available
        if self.trw_api_key:
            trw_url = f"https://trw.lat/api/bypass?url={encoded_link}"
            result = await self._try_api_get(trw_url, session, timeout, 'TRW Bypass', headers={'x-api-key': self.trw_api_key})
            if result['success']:
                return result
            else:
                errors.append(f"TRW Bypass: {result.get('error', 'Unknown error')}")
        
        # Fallback to ZEN API if TRW failed or wasn't available
        if self.zen_api_key:
            zen_url = f"https://zen.gbrl.org/v1/bypass?url={encoded_link}"
            result = await self._try_api_get(zen_url, session, timeout, 'ZEN Bypass', headers={'x-api-key': self.zen_api_key})
            if result['success']:
                return result
            else:
                errors.append(f"ZEN Bypass: {result.get('error', 'Unknown error')}")
        
        # Fallback to EAS-X API if ZEN failed or wasn't available
        if self.eas_api_key:
            eas_url = "https://api.eas-x.com/v3/bypass"
            result = await self._try_api_post(eas_url, session, timeout, 'EAS-X Bypass', 
                                             headers={'eas-api-key': self.eas_api_key},
                                             json_data={'url': link})
            if result['success']:
                return result
            else:
                errors.append(f"EAS-X Bypass: {result.get('error', 'Unknown error')}")
        
        # If we get here, all failed or no keys configured
        error_msg = ' | '.join(errors) if errors else 'No API keys configured for bypass services'
        return {
            'success': False,
            'error': error_msg,
            'api_name': 'All providers failed'
        }
    
    async def _try_api_get(self, api_url: str, session: aiohttp.ClientSession, timeout: int, api_name: str, headers: Optional[Dict] = None) -> dict:
        try:
            async with session.get(
                api_url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_response(data, api_name)
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
    
    async def _try_api_post(self, api_url: str, session: aiohttp.ClientSession, timeout: int, api_name: str, headers: Optional[Dict] = None, json_data: Optional[Dict] = None) -> dict:
        try:
            async with session.post(
                api_url,
                headers=headers,
                json=json_data,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_response(data, api_name)
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
    
    def _parse_response(self, data: dict, api_name: str) -> dict:
        # Try to extract loadstring and bypassed_url from various response formats
        loadstring = None
        bypassed_url = None
        
        # Check for ZEN/EAS-X API format: {"status": "success", "result": "..."}
        if data.get('status') == 'success':
            result_data = data.get('result')
            if isinstance(result_data, list) and len(result_data) > 0:
                loadstring = result_data[0] if isinstance(result_data[0], str) else None
                bypassed_url = result_data[1] if len(result_data) > 1 else None
            else:
                loadstring = result_data if isinstance(result_data, str) else None
        elif data.get('status') == 'error' or data.get('status') == 'fail':
            error_msg = data.get('message') or data.get('error') or 'Unknown error'
            if 'not supported' in error_msg.lower() or 'unsupported' in error_msg.lower():
                return {
                    'success': False,
                    'error': f'{api_name}: Link not supported by this service',
                    'api_name': api_name,
                    'unsupported': True
                }
            return {
                'success': False,
                'error': f'{api_name}: {error_msg}',
                'api_name': api_name
            }
        else:
            # Standard format for Ace/TRW
            loadstring = data.get('loadstring') or data.get('script') or data.get('code')
            bypassed_url = data.get('destination') or data.get('result') or data.get('bypassed_url') or data.get('url')
        
        # Check if we actually got content
        if not loadstring and not bypassed_url:
            error_msg = data.get('message') or data.get('error') or 'No content returned'
            if 'not supported' in error_msg.lower() or 'unsupported' in error_msg.lower():
                return {
                    'success': False,
                    'error': f'{api_name}: Link not supported by this service',
                    'api_name': api_name,
                    'unsupported': True
                }
            return {
                'success': False,
                'error': f'{api_name}: {error_msg}',
                'api_name': api_name
            }
        
        return {
            'success': True,
            'loadstring': loadstring,
            'bypassed_url': bypassed_url,
            'raw_data': data,
            'api_name': api_name
        }
    
    def set_api_key(self, provider: str, api_key: str):
        """Update API key for a specific provider"""
        if provider == 'ace-bypass':
            self.bypass_api_key = api_key
        elif provider == 'trw-bypass':
            self.trw_api_key = api_key
        elif provider == 'zen-bypass':
            self.zen_api_key = api_key
        elif provider == 'eas-bypass':
            self.eas_api_key = api_key
    
    def get_api_status(self) -> dict:
        status = {
            'active': 'Multi-API (Ace → TRW → ZEN → EAS-X fallback)',
            'providers': {
                'ace-bypass': {
                    'name': 'Ace Bypass',
                    'enabled': True,
                    'requires_key': True,
                    'has_key': bool(self.bypass_api_key),
                    'ready': bool(self.bypass_api_key)
                },
                'trw-bypass': {
                    'name': 'TRW Bypass',
                    'enabled': True,
                    'requires_key': True,
                    'has_key': bool(self.trw_api_key),
                    'ready': bool(self.trw_api_key)
                },
                'zen-bypass': {
                    'name': 'ZEN Bypass',
                    'enabled': True,
                    'requires_key': True,
                    'has_key': bool(self.zen_api_key),
                    'ready': bool(self.zen_api_key)
                },
                'eas-bypass': {
                    'name': 'EAS-X Bypass',
                    'enabled': True,
                    'requires_key': True,
                    'has_key': bool(self.eas_api_key),
                    'ready': bool(self.eas_api_key)
                }
            }
        }
        
        return status
