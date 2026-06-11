"""stonemux coordination adapter for Microsoft Agent Framework.

Provides an extension for the MS Agent Framework enabling multi-agent coordination.
MIT Licensed. Python 3.9+ compatible.
"""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from typing import Any


class StonemuxExtension:
    """MS Agent Framework extension for stonemux coordination.

    Integrates with Microsoft's Agent Framework as an extension that
    provides coordination tools to agents.

    Usage:
        ext = StonemuxExtension(
            agent_id="analyst-1", role="analyst",
            capabilities=["analyze", "report"]
        )
        agent.add_extension(ext)
    """

    def __init__(
        self,
        agent_id: str = "msagent-agent",
        role: str = "assistant",
        capabilities: list[str] | None = None,
        group: str | None = None,
        channel: str = "default",
        base_url: str = "http://127.0.0.1:3392",
    ) -> None:
        self.agent_id = agent_id
        self.role = role
        self.capabilities = capabilities or []
        self.group = group
        self.channel = channel
        self.base_url = base_url.rstrip("/")
        self._register()

    def _request(self, method: str, path: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else "{}"
            try:
                return json.loads(error_body)
            except json.JSONDecodeError:
                return {"error": str(e), "status": e.code}

    def _register(self) -> dict[str, Any]:
        return self._request("POST", "/agent/register", {
            "agent_id": self.agent_id,
            "role": self.role,
            "capabilities": self.capabilities,
            "group": self.group,
            "channel": self.channel,
        })

    def get_functions(self) -> list[dict[str, Any]]:
        """Return function definitions for MS Agent Framework tool registration."""
        return [
            {
                "name": "stonemux_discover",
                "description": "Discover other agents in the coordination bus",
                "parameters": {"role": {"type": "string", "required": False}, "group": {"type": "string", "required": False}},
                "handler": self.discover,
            },
            {
                "name": "stonemux_post_task",
                "description": "Post a task for other agents to claim",
                "parameters": {"description": {"type": "string", "required": True}, "required_capability": {"type": "string", "required": False}, "priority": {"type": "integer", "required": False}},
                "handler": self.post_task,
            },
            {
                "name": "stonemux_claim_task",
                "description": "Claim the next available task matching capabilities",
                "parameters": {},
                "handler": self.claim_task,
            },
            {
                "name": "stonemux_complete_task",
                "description": "Mark a claimed task as complete",
                "parameters": {"task_id": {"type": "string", "required": True}, "result": {"type": "string", "required": True}},
                "handler": self.complete_task,
            },
            {
                "name": "stonemux_send_msg",
                "description": "Send a direct message to another agent",
                "parameters": {"to": {"type": "string", "required": True}, "content": {"type": "string", "required": True}},
                "handler": self.send_msg,
            },
            {
                "name": "stonemux_poll_msg",
                "description": "Poll for new messages",
                "parameters": {"timeout": {"type": "integer", "required": False}},
                "handler": self.poll_msg,
            },
            {
                "name": "stonemux_get_state",
                "description": "Read shared coordination state",
                "parameters": {"key": {"type": "string", "required": True}},
                "handler": self.get_state,
            },
            {
                "name": "stonemux_set_state",
                "description": "Write shared coordination state",
                "parameters": {"key": {"type": "string", "required": True}, "value": {"type": "string", "required": True}},
                "handler": self.set_state,
            },
        ]

    def discover(self, role: str | None = None, group: str | None = None) -> dict[str, Any]:
        params = []
        if role:
            params.append(f"role={role}")
        if group:
            params.append(f"group={group}")
        qs = f"?{'&'.join(params)}" if params else ""
        return self._request("GET", f"/agent/discover{qs}")

    def post_task(self, description: str, required_capability: str | None = None, priority: int = 0) -> dict[str, Any]:
        return self._request("POST", "/task/post", {
            "description": description,
            "posted_by": self.agent_id,
            "required_capability": required_capability,
            "priority": priority,
            "channel": self.channel,
        })

    def claim_task(self) -> dict[str, Any]:
        return self._request("POST", "/task/claim", {
            "agent_id": self.agent_id,
            "channel": self.channel,
        })

    def complete_task(self, task_id: str, result: str) -> dict[str, Any]:
        return self._request("POST", "/task/complete", {
            "task_id": task_id,
            "agent_id": self.agent_id,
            "result": result,
            "status": "complete",
        })

    def send_msg(self, to: str, content: str) -> dict[str, Any]:
        return self._request("POST", "/msg/send", {
            "from": self.agent_id,
            "to": to,
            "content": content,
            "channel": self.channel,
        })

    def poll_msg(self, timeout: int = 5) -> dict[str, Any]:
        return self._request("GET", f"/msg/poll?agent_id={self.agent_id}&timeout={timeout}")

    def broadcast(self, content: str, group: str | None = None) -> dict[str, Any]:
        return self._request("POST", "/msg/broadcast", {
            "from": self.agent_id,
            "group": group,
            "content": content,
            "channel": self.channel,
        })

    def get_state(self, key: str) -> dict[str, Any]:
        return self._request("GET", f"/state/get?key={key}&channel={self.channel}")

    def set_state(self, key: str, value: str, expected_version: int | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "channel": self.channel,
            "key": key,
            "value": value,
            "updated_by": self.agent_id,
        }
        if expected_version is not None:
            payload["expected_version"] = expected_version
        return self._request("POST", "/state/set", payload)

    def shutdown(self) -> dict[str, Any]:
        return self._request("POST", "/agent/deregister", {"agent_id": self.agent_id})
