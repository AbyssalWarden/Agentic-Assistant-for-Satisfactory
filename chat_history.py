import json
import os
from datetime import datetime
from typing import List, Dict

class ChatHistory:
    def __init__(self, agent_name: str = "default"):
        self.agent_name = agent_name
        self.history_file = f"{agent_name}.json"
        self.conversations: List[Dict] = []
        self.load_history()
        
    def load_history(self):
        """Load chat history from file if it exists."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    self.conversations = json.load(f)
            except json.JSONDecodeError:
                self.conversations = []
    
    def save_history(self):
        """Save chat history to file."""
        with open(self.history_file, 'w') as f:
            json.dump(self.conversations, f, indent=2)
    
    def add_message(self, user_message: str, bot_response: str):
        """Add a new message pair to the history."""
        timestamp = datetime.now().isoformat()
        self.conversations.append({
            "timestamp": timestamp,
            "user_message": user_message,
            "bot_response": bot_response
        })
        self.save_history()
    
    def get_recent_conversations(self, limit: int = 5) -> List[Dict]:
        """Get the most recent conversations."""
        return self.conversations[-limit:]
    
    def analyze_patterns(self) -> Dict:
        """Analyze conversation patterns for response adaptation."""
        if not self.conversations:
            return {}
        
        patterns = {
            "common_topics": {},
            "user_style": {},
            "response_frequency": {}
        }
        
        # Simple keyword tracking
        for conv in self.conversations:
            # Track user message keywords
            words = conv["user_message"].lower().split()
            for word in words:
                if len(word) > 3:  # Ignore short words
                    patterns["common_topics"][word] = patterns["common_topics"].get(word, 0) + 1
        
        return patterns 