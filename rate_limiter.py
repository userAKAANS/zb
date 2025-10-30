import time
from collections import defaultdict, deque

class RateLimiter:
    def __init__(self, max_requests: int = 10, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = defaultdict(deque)
    
    def is_allowed(self, identifier: str) -> bool:
        current_time = time.time()
        user_requests = self.requests[identifier]
        
        while user_requests and current_time - user_requests[0] > self.time_window:
            user_requests.popleft()
        
        if len(user_requests) < self.max_requests:
            user_requests.append(current_time)
            return True
        
        return False
    
    def get_retry_after(self, identifier: str) -> int:
        if not self.requests[identifier]:
            return 0
        
        oldest_request = self.requests[identifier][0]
        current_time = time.time()
        elapsed = current_time - oldest_request
        
        if elapsed < self.time_window:
            return int(self.time_window - elapsed)
        
        return 0
