import json
import time
from datetime import datetime
from google.adk.plugins import base_plugin

class AuditLogPlugin(base_plugin.BasePlugin):
    """Plugin to record all user inputs and agent outputs to an audit log."""

    def __init__(self):
        super().__init__(name="audit_log")
        self.logs = []
        self._start_times = {}

    def _extract_text(self, content) -> str:
        text = ""
        if hasattr(content, "parts") and content.parts:
            for part in content.parts:
                if hasattr(part, "text") and part.text:
                    text += part.text
        return text

    async def on_user_message_callback(self, *, invocation_context, user_message):
        request_id = id(user_message)
        self._start_times[request_id] = time.time()
        
        user_id = invocation_context.user_id if invocation_context and hasattr(invocation_context, "user_id") else "anonymous"
        text = self._extract_text(user_message)
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "request_id": request_id,
            "input": text,
        }
        self.logs.append(log_entry)
        return None

    async def after_model_callback(self, *, callback_context, llm_response):
        # We try to match with the most recent log block
        if not self.logs:
            return llm_response
            
        last_log = self.logs[-1]
        request_id = last_log.get("request_id")
        
        latency = 0.0
        if request_id in self._start_times:
            latency = time.time() - self._start_times[request_id]
            del self._start_times[request_id]
            
        output = self._extract_text(llm_response)
        last_log["output"] = output
        last_log["latency_seconds"] = round(latency, 3)
        return llm_response

    def export_json(self, filepath="audit_log.json"):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.logs, f, indent=2, default=str, ensure_ascii=False)
