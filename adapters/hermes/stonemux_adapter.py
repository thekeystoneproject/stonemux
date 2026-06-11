"""stonemux coordination adapter for Hermes.

Exposes multi-agent coordination as Hermes tool providers.
MIT Licensed. Python 3.9+ compatible.
"""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from typing import Any


class StonemuxAdapter:
    """Hermes tool provider for stonemux multi-agent coordination."""

    def __init__(
        self,
        agent_id: str = "hermes-agent",
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

    def deregister(self) -> dict[str, Any]:
        return self._request("POST", "/agent/deregister", {"agent_id": self.agent_id})

    def heartbeat(self, status: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"agent_id": self.agent_id}
        if status:
            payload["status"] = status
        return self._request("POST", "/agent/heartbeat", payload)

    def discover(self, role: str | None = None, group: str | None = None) -> dict[str, Any]:
        params = []
        if role:
            params.append(f"role={role}")
        if group:
            params.append(f"group={group}")
        qs = f"?{'&'.join(params)}" if params else ""
        return self._request("GET", f"/agent/discover{qs}")

    def post_task(
        self,
        description: str,
        required_capability: str | None = None,
        priority: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._request("POST", "/task/post", {
            "description": description,
            "posted_by": self.agent_id,
            "required_capability": required_capability,
            "priority": priority,
            "channel": self.channel,
            "metadata": metadata or {},
        })

    def claim_task(self) -> dict[str, Any]:
        return self._request("POST", "/task/claim", {
            "agent_id": self.agent_id,
            "channel": self.channel,
        })

    def complete_task(self, task_id: str, result: str, status: str = "complete") -> dict[str, Any]:
        return self._request("POST", "/task/complete", {
            "task_id": task_id,
            "agent_id": self.agent_id,
            "result": result,
            "status": status,
        })

    def send_msg(self, to: str, content: str) -> dict[str, Any]:
        return self._request("POST", "/msg/send", {
            "from": self.agent_id,
            "to": to,
            "content": content,
            "channel": self.channel,
        })

    def poll_msg(self, timeout: int = 30) -> dict[str, Any]:
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

    def health(self) -> dict[str, Any]:
        """Check stonemux service health."""
        return self._request("GET", "/health")

    def get_tools(self) -> list[dict[str, Any]]:
        """Return tool definitions for Hermes tool provider registration."""
        return [
            {"name": "stonemux_discover", "description": "Discover registered agents", "fn": self.discover},
            {"name": "stonemux_post_task", "description": "Post a task for other agents", "fn": self.post_task},
            {"name": "stonemux_claim_task", "description": "Claim next available task", "fn": self.claim_task},
            {"name": "stonemux_complete_task", "description": "Mark a task as complete", "fn": self.complete_task},
            {"name": "stonemux_send_msg", "description": "Send a message to another agent", "fn": self.send_msg},
            {"name": "stonemux_poll_msg", "description": "Poll for new messages", "fn": self.poll_msg},
            {"name": "stonemux_broadcast", "description": "Broadcast message to agents", "fn": self.broadcast},
            {"name": "stonemux_get_state", "description": "Read shared state", "fn": self.get_state},
            {"name": "stonemux_set_state", "description": "Write shared state", "fn": self.set_state},
        ]
