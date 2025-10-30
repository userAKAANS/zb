class AIService:
    def __init__(self, api_key):
        self.api_key = api_key
    
    async def get_helpful_error_message(self, error, link):
        return "Please check if the link is valid and try again."
