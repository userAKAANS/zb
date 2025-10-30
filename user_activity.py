import json
import os
from datetime import datetime

class UserActivity:
    def __init__(self, activity_file='user_activity.json'):
        self.activity_file = activity_file
        self.data = self.load_data()
    
    def load_data(self):
        try:
            if os.path.exists(self.activity_file):
                with open(self.activity_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading user activity: {e}")
        return {
            'blacklisted_users': [],
            'blacklisted_hwids': []
        }
    
    def save_data(self):
        try:
            with open(self.activity_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Error saving user activity: {e}")
    
    def blacklist_user(self, user_id: int) -> bool:
        if user_id not in self.data.get('blacklisted_users', []):
            if 'blacklisted_users' not in self.data:
                self.data['blacklisted_users'] = []
            self.data['blacklisted_users'].append(user_id)
            self.save_data()
            return True
        return False
    
    def unblacklist_user(self, user_id: int) -> bool:
        if user_id in self.data.get('blacklisted_users', []):
            self.data['blacklisted_users'].remove(user_id)
            self.save_data()
            return True
        return False
    
    def blacklist_hwid(self, hwid: str) -> bool:
        if hwid not in self.data.get('blacklisted_hwids', []):
            if 'blacklisted_hwids' not in self.data:
                self.data['blacklisted_hwids'] = []
            self.data['blacklisted_hwids'].append(hwid)
            self.save_data()
            return True
        return False
    
    def unblacklist_hwid(self, hwid: str) -> bool:
        if hwid in self.data.get('blacklisted_hwids', []):
            self.data['blacklisted_hwids'].remove(hwid)
            self.save_data()
            return True
        return False
    
    def get_blacklist_data(self):
        return {
            'total_users': len(self.data.get('blacklisted_users', [])),
            'total_hwids': len(self.data.get('blacklisted_hwids', [])),
            'user_ids': self.data.get('blacklisted_users', []),
            'hwids': self.data.get('blacklisted_hwids', [])
        }
