import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class UserRateLimiter:
    def __init__(self, rate_file='user_rates.json'):
        self.rate_file = rate_file
        self.user_data = self.load_data()
        self.short_term_limit = 2
        self.short_term_window = 300
        self.daily_limit = 10
    
    def load_data(self) -> Dict:
        try:
            if os.path.exists(self.rate_file):
                with open(self.rate_file, 'r') as f:
                    data = json.load(f)
                    return {int(k): v for k, v in data.items()}
        except Exception as e:
            print(f"Error loading rate limit data: {e}")
        return {}
    
    def save_data(self):
        try:
            with open(self.rate_file, 'w') as f:
                json.dump({str(k): v for k, v in self.user_data.items()}, f, indent=2)
        except Exception as e:
            print(f"Error saving rate limit data: {e}")
    
    def clean_old_timestamps(self, user_id: int):
        if user_id not in self.user_data:
            return
        
        current_time = datetime.utcnow()
        
        if 'short_term' in self.user_data[user_id]:
            self.user_data[user_id]['short_term'] = [
                ts for ts in self.user_data[user_id]['short_term']
                if (current_time - datetime.fromisoformat(ts)).total_seconds() < self.short_term_window
            ]
        
        if 'daily_reset' in self.user_data[user_id]:
            reset_time = datetime.fromisoformat(self.user_data[user_id]['daily_reset'])
            if current_time >= reset_time:
                self.user_data[user_id]['daily_count'] = 0
                next_reset = current_time.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                self.user_data[user_id]['daily_reset'] = next_reset.isoformat()
    
    def check_rate_limit(self, user_id: int) -> Dict:
        current_time = datetime.utcnow()
        
        if user_id not in self.user_data:
            next_reset = current_time.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            self.user_data[user_id] = {
                'short_term': [],
                'daily_count': 0,
                'daily_reset': next_reset.isoformat()
            }
        
        self.clean_old_timestamps(user_id)
        
        short_term_count = len(self.user_data[user_id].get('short_term', []))
        if short_term_count >= self.short_term_limit:
            oldest_timestamp = datetime.fromisoformat(self.user_data[user_id]['short_term'][0])
            retry_after = self.short_term_window - (current_time - oldest_timestamp).total_seconds()
            return {
                'allowed': False,
                'limit_type': 'short_term',
                'retry_after': max(0, retry_after)
            }
        
        daily_count = self.user_data[user_id].get('daily_count', 0)
        if daily_count >= self.daily_limit:
            reset_time = datetime.fromisoformat(self.user_data[user_id]['daily_reset'])
            retry_after = (reset_time - current_time).total_seconds()
            return {
                'allowed': False,
                'limit_type': 'daily',
                'retry_after': max(0, retry_after)
            }
        
        return {
            'allowed': True,
            'remaining_short_term': self.short_term_limit - short_term_count,
            'remaining_daily': self.daily_limit - daily_count
        }
    
    def record_bypass(self, user_id: int):
        current_time = datetime.utcnow()
        
        if user_id not in self.user_data:
            next_reset = current_time.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            self.user_data[user_id] = {
                'short_term': [],
                'daily_count': 0,
                'daily_reset': next_reset.isoformat()
            }
        
        if 'short_term' not in self.user_data[user_id]:
            self.user_data[user_id]['short_term'] = []
        
        self.user_data[user_id]['short_term'].append(current_time.isoformat())
        self.user_data[user_id]['daily_count'] = self.user_data[user_id].get('daily_count', 0) + 1
        
        self.save_data()
    
    def get_user_stats(self, user_id: int) -> Dict:
        if user_id not in self.user_data:
            return {
                'daily_count': 0,
                'daily_limit': self.daily_limit,
                'remaining': self.daily_limit
            }
        
        self.clean_old_timestamps(user_id)
        
        daily_count = self.user_data[user_id].get('daily_count', 0)
        return {
            'daily_count': daily_count,
            'daily_limit': self.daily_limit,
            'remaining': max(0, self.daily_limit - daily_count),
            'reset_time': self.user_data[user_id].get('daily_reset')
        }
