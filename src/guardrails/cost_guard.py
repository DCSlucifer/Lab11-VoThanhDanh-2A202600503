from collections import defaultdict
from google.adk.plugins import base_plugin
from google.genai import types

class CostGuardPlugin(base_plugin.BasePlugin):
    """
    Bonus Feature: A 6th safety layer that tracks the token/character size of prompts
    and blocks requests if a user exceeds a given character limit in a session.
    """

    def __init__(self, max_chars_per_session=5000):
        super().__init__(name="cost_guard")
        self.max_chars_per_session = max_chars_per_session
        self.user_usage = defaultdict(int)

    def _extract_text(self, content) -> str:
        text = ""
        if hasattr(content, "parts") and content.parts:
            for part in content.parts:
                if hasattr(part, "text") and part.text:
                    text += part.text
        return text

    async def on_user_message_callback(self, *, invocation_context, user_message):
        user_id = invocation_context.user_id if invocation_context and hasattr(invocation_context, "user_id") else "anonymous"
        text = self._extract_text(user_message)
        
        char_count = len(text)
        current_usage = self.user_usage[user_id]
        
        if current_usage + char_count > self.max_chars_per_session:
            msg = f"Cost Guard blocked request: Character limit exceeded for session (Max: {self.max_chars_per_session})."
            return types.Content(
                role="model",
                parts=[types.Part.from_text(text=msg)],
            )
            
        self.user_usage[user_id] += char_count
        return None
