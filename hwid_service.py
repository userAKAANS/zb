import hashlib
import json
import os

class HWIDService:
    def __init__(self, hwid_file='hwids.json'):
        self.hwid_file = hwid_file
        self.hwids = self.load_hwids()
    
    def load_hwids(self):
        try:
            if os.path.exists(self.hwid_file):
                with open(self.hwid_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading HWIDs: {e}")
        return {}
    
    def save_hwids(self):
        try:
            with open(self.hwid_file, 'w') as f:
                json.dump(self.hwids, f, indent=2)
        except Exception as e:
            print(f"Error saving HWIDs: {e}")
    
    def generate_hwid(self, user_id: int) -> str:
        return hashlib.sha256(str(user_id).encode()).hexdigest()[:16].upper()
    
    def is_blacklisted(self, hwid: str) -> bool:
        return hwid in self.hwids.get('blacklist', [])
