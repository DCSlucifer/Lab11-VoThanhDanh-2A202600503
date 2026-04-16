import time
from collections import defaultdict, deque
from google.adk.plugins import base_plugin
from google.genai import types

class RateLimitPlugin(base_plugin.BasePlugin):
    """Plugin to limit the number of requests per user in a time window."""

    def __init__(self, max_requests=10, window_seconds=60):
        super().__init__(name="rate_limiter")
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.user_windows = defaultdict(deque)

    async def on_user_message_callback(self, *, invocation_context, user_message):
        user_id = invocation_context.user_id if invocation_context and hasattr(invocation_context, "user_id") else "anonymous"
        now = time.time()
        window = self.user_windows[user_id]

        # Remove expired timestamps
        while window and window[0] <= now - self.window_seconds:
            window.popleft()

        # Check if rate limit exceeded
        if len(window) >= self.max_requests:
            oldest = window[0]
            wait_time = int(self.window_seconds - (now - oldest))
            msg = f"Rate limit exceeded. Please wait {wait_time} seconds before trying again."
            return types.Content(
                role="model",
                parts=[types.Part.from_text(text=msg)],
            )

        # Allow request
        window.append(now)
        return None
