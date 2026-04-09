"""
WebSocket-enabled Agent Callbacks
"""
import json
import time
from typing import Any, Dict, Optional
from langchain_core.callbacks import BaseCallbackHandler

from api.core.websocket import manager
import asyncio

# Since Langchain callbacks can be synchronous, we need a way to run async broadcasts safely
def sync_broadcast(channel_id: str, message: dict):
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(manager.broadcast(message, channel_id))
    except RuntimeError:
        # If no loop is running, run it (usually doesn't happen in fastAPI async workers)
        asyncio.run(manager.broadcast(message, channel_id))


class WebSockectStreamingCallback(BaseCallbackHandler):
    """
    Callback handler to stream agent thoughts and tool executions 
    to the Bidding Hall frontend via WebSocket.
    """
    def __init__(self, channel_id: str, agent_name: str = "Assistant"):
        super().__init__()
        self.channel_id = channel_id
        self.agent_name = agent_name
        self.start_time = time.time()

    def _push(self, log: str, status: str = "thinking", final_text: str = None):
        msg = {
            "type": "agent_stream",
            "agentName": self.agent_name,
            "status": status,
            "log": log,
            "timestamp": time.time(),
            "elapsed": round(time.time() - self.start_time, 2)
        }
        if final_text:
            msg["finalText"] = final_text
            
        sync_broadcast(self.channel_id, msg)

    def on_chain_start(self, serialized: Dict[str, Any], prompts: list, **kwargs: Any) -> None:
        self._push("正在启动思考引擎并分析任务需求...")

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> None:
        tool_name = serialized.get("name", "tool")
        self._push(f"调用外部工具: {tool_name} (参数: {input_str})", status="searching")

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        # truncating output for safety
        self._push(f"工具返回结果 (长度: {len(output)} 字节)", status="thinking")

    def on_llm_start(self, serialized: Dict[str, Any], prompts: list, **kwargs: Any) -> None:
        self._push("正在推演文本结构和内容...")

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """
        核心修复：实现 Token 级的增量推送
        """
        if token:
            self._push(log="⏳ 内容生成中...", status="writing", final_text=token)

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        # If this is the final output of the crew/agent chain
        text_output = str(outputs)
        self._push("生成完成", status="idle", final_text=text_output)
