"""stonemux coordination adapter for OpenHands.

Provides an OpenHands-compatible plugin for multi-agent coordination.
MIT Licensed. Python 3.9+ compatible.
"""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from typing import Any


class StonemuxPlugin:
    """OpenHands plugin for stonemux multi-agent coordination.

    Exposes coordination capabilities as an OpenHands plugin that agents
    can use to coordinate work, exchange messages, and share state.

    Usage:
        plugin = StonemuxPlugin(
            agent_id="coder-1", role="coder",
            capabilities=["code", "review"]
        )
        # Register as OpenHands plugin
        runtime.register_plugin(plugin)
    """

    name = "stonemux"
    description = "Multi-agent coordination via stonemux"

    def __init__(
        self,
        agent_id: str = "openhands-agent",
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

    def initialize(self) -> None:
        """OpenHands plugin initialization hook."""
        self._register()

    def get_actions(self) -> dict[str, Any]:
        """Return available actions for OpenHands runtime."""
        return {
            "discover": {"description": "Discover registered agents", "handler": self.discover},
            "post_task": {"description": "Post a task for other agents", "handler": self.post_task},
            "claim_task": {"description": "Claim next available task", "handler": self.claim_task},
            "complete_task": {"description": "Complete a claimed task", "handler": self.complete_task},
            "send_msg": {"description": "Send message to agent", "handler": self.send_msg},
            "poll_msg": {"description": "Poll for messages", "handler": self.poll_msg},
            "broadcast": {"description": "Broadcast to all or group", "handler": self.broadcast},
            "get_state": {"description": "Read shared state", "handler": self.get_state},
            "set_state": {"description": "Write shared state", "handler": self.set_state},
        }

    def discover(self, role: str | None = None, group: str | None = None) -> dict[str, Any]:
        params = []
        if role:
            params.append(f"role={role}")
        if group:
            params.append(f"group={group}")
        qs = f"?{'&'.join(params)}" if params else ""
        return self._request("GET", f"/agent/discover{qs}")

    def post_task(self, description: str, required_capability: str | None = None, priority: int = 0, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
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
        """Clean shutdown — deregister from coordination."""
        return self._request("POST", "/agent/deregister", {"agent_id": self.agent_id})
