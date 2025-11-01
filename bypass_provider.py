import aiohttp
from urllib.parse import quote
import json
import os
from typing import Optional, Dict

class BypassProvider:
    """Abstraction layer for multiple bypass API providers"""
    
    API_CONFIG_FILE = 'api_config.json'
    
    def __init__(self):
        self.config = self.load_config()
    
    def get_api_keys(self) -> dict:
        """Get current API keys from environment variables (always fresh)"""
        return {
            'ace-bypass': os.getenv('BYPASS_API_KEY'),
            'trw-lat': os.getenv('TRW_API_KEY')
        }
    
    def load_config(self) -> dict:
        """Load API configuration from file"""
        try:
            if os.path.exists(self.API_CONFIG_FILE):
                with open(self.API_CONFIG_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading API config: {e}")
        
        return {
            "active_api": "ace-bypass",
            "apis": {
                "ace-bypass": {
                    "name": "Ace Bypass",
                    "url": "http://ace-bypass.com/api/bypass?url={url}&apikey={key}",
                    "requires_key": True,
                    "enabled": True
                },
                "trw-lat": {
                    "name": "TRW.lat",
                    "url": "https://trw.lat/api/bypass?url=url",
                    "requires_key": False,
                    "enabled": True
                }
            }
        }
    
    def save_config(self):
        """Save API configuration to file"""
        try:
            with open(self.API_CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving API config: {e}")
    
    def get_active_api(self) -> str:
        """Get the currently active API provider"""
        return self.config.get('active_api', 'ace-bypass')
    
    def set_active_api(self, api_name: str) -> bool:
        """Switch to a different API provider"""
        if api_name in self.config['apis']:
            self.config['active_api'] = api_name
            self.save_config()
            return True
        return False
    
    def get_available_apis(self) -> Dict[str, dict]:
        """Get list of all available API providers"""
        return self.config.get('apis', {})
    
    def set_api_key(self, api_name: str, key: str):
        """Set API key for a specific provider in environment"""
        env_var_map = {
            'ace-bypass': 'BYPASS_API_KEY',
            'trw-lat': 'TRW_API_KEY'
        }
        if api_name in env_var_map:
            os.environ[env_var_map[api_name]] = key
    
    def build_api_url(self, link: str, api_name: Optional[str] = None) -> Optional[str]:
        """Build the API URL for the specified or active provider"""
        if api_name is None:
            api_name = self.get_active_api()
        
        api_config = self.config['apis'].get(api_name)
        if not api_config or not api_config.get('enabled'):
            return None
        
        url_template = api_config['url']
        encoded_link = quote(link)
        api_keys = self.get_api_keys()
        
        if api_config.get('requires_key'):
            api_key = api_keys.get(api_name)
            if not api_key:
                return None
            return url_template.format(url=encoded_link, key=api_key)
        else:
            return url_template.format(url=encoded_link)
    
    async def bypass(self, link: str, session: aiohttp.ClientSession, timeout: int = 30) -> dict:
        """Perform bypass using the active API provider"""
        api_name = self.get_active_api()
        api_url = self.build_api_url(link)
        api_keys = self.get_api_keys()
        
        if not api_url:
            api_config = self.config['apis'].get(api_name, {})
            if api_config.get('requires_key') and not api_keys.get(api_name):
                return {
                    'success': False,
                    'error': f'API key not set for {api_config.get("name", api_name)}. Use /config to set it.',
                    'api_name': api_name
                }
            return {
                'success': False,
                'error': f'API {api_name} not available or disabled',
                'api_name': api_name
            }
        
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
                        'error': f'API error {response.status}: {error_text[:200]}',
                        'api_name': api_name
                    }
        except Exception as e:
            return {
                'success': False,
                'error': f'Request failed: {str(e)}',
                'api_name': api_name
            }
    
    def get_api_status(self) -> dict:
        """Get status information about all APIs"""
        status = {
            'active': self.get_active_api(),
            'providers': {}
        }
        api_keys = self.get_api_keys()
        
        for api_name, api_config in self.config['apis'].items():
            has_key = bool(api_keys.get(api_name)) if api_config.get('requires_key') else True
            status['providers'][api_name] = {
                'name': api_config.get('name', api_name),
                'enabled': api_config.get('enabled', False),
                'requires_key': api_config.get('requires_key', False),
                'has_key': has_key,
                'ready': api_config.get('enabled', False) and has_key
            }
        
        return status
