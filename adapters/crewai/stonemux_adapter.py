"""stonemux coordination adapter for CrewAI.

Wraps stonemux REST API as CrewAI-compatible tools.
MIT Licensed. Python 3.9+ compatible.
"""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from typing import Any


class StonemuxClient:
    """HTTP client for stonemux coordination server."""

    def __init__(self, base_url: str = "http://127.0.0.1:3392") -> None:
        self.base_url = base_url.rstrip("/")

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


class StonemuxTools:
    """CrewAI tool wrapper for stonemux multi-agent coordination.

    Usage with CrewAI:
        tools = StonemuxTools(agent_id="researcher-1", role="researcher",
                              capabilities=["search", "summarize"])
        agent = Agent(role="Researcher", tools=tools.as_tools())
    """

    def __init__(
        self,
        agent_id: str = "crewai-agent",
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
        self.client = StonemuxClient(base_url)
        self._register()

    def _register(self) -> dict[str, Any]:
        return self.client._request("POST", "/agent/register", {
            "agent_id": self.agent_id,
            "role": self.role,
            "capabilities": self.capabilities,
            "group": self.group,
            "channel": self.channel,
        })

    def discover_agents(self, role: str | None = None, group: str | None = None) -> str:
        """Discover other registered agents. Filter by role or group."""
        params = []
        if role:
            params.append(f"role={role}")
        if group:
            params.append(f"group={group}")
        qs = f"?{'&'.join(params)}" if params else ""
        result = self.client._request("GET", f"/agent/discover{qs}")
        return json.dumps(result, indent=2)

    def post_task(self, description: str, required_capability: str | None = None, priority: int = 0) -> str:
        """Post a task for other agents to claim."""
        result = self.client._request("POST", "/task/post", {
            "description": description,
            "posted_by": self.agent_id,
            "required_capability": required_capability,
            "priority": priority,
            "channel": self.channel,
        })
        return json.dumps(result, indent=2)

    def claim_task(self) -> str:
        """Claim the next available task matching your capabilities."""
        result = self.client._request("POST", "/task/claim", {
            "agent_id": self.agent_id,
            "channel": self.channel,
        })
        return json.dumps(result, indent=2)

    def complete_task(self, task_id: str, result: str) -> str:
        """Mark a claimed task as complete with a result."""
        resp = self.client._request("POST", "/task/complete", {
            "task_id": task_id,
            "agent_id": self.agent_id,
            "result": result,
            "status": "complete",
        })
        return json.dumps(resp, indent=2)

    def send_message(self, to: str, content: str) -> str:
        """Send a direct message to another agent."""
        result = self.client._request("POST", "/msg/send", {
            "from": self.agent_id,
            "to": to,
            "content": content,
            "channel": self.channel,
        })
        return json.dumps(result, indent=2)

    def poll_messages(self, timeout: int = 5) -> str:
        """Check for new messages."""
        result = self.client._request("GET", f"/msg/poll?agent_id={self.agent_id}&timeout={timeout}")
        return json.dumps(result, indent=2)

    def broadcast_message(self, content: str, group: str | None = None) -> str:
        """Broadcast a message to all agents or a specific group."""
        result = self.client._request("POST", "/msg/broadcast", {
            "from": self.agent_id,
            "group": group,
            "content": content,
            "channel": self.channel,
        })
        return json.dumps(result, indent=2)

    def get_shared_state(self, key: str) -> str:
        """Read a shared state value."""
        result = self.client._request("GET", f"/state/get?key={key}&channel={self.channel}")
        return json.dumps(result, indent=2)

    def set_shared_state(self, key: str, value: str, expected_version: int | None = None) -> str:
        """Write a shared state value with optional CAS."""
        payload: dict[str, Any] = {
            "channel": self.channel,
            "key": key,
            "value": value,
            "updated_by": self.agent_id,
        }
        if expected_version is not None:
            payload["expected_version"] = expected_version
        result = self.client._request("POST", "/state/set", payload)
        return json.dumps(result, indent=2)

    def shutdown(self) -> str:
        """Deregister this agent from coordination."""
        result = self.client._request("POST", "/agent/deregister", {"agent_id": self.agent_id})
        return json.dumps(result, indent=2)

    def as_tools(self) -> list[Any]:
        """Return list of tool callables for CrewAI Agent(tools=[...])."""
        return [
            self.discover_agents,
            self.post_task,
            self.claim_task,
            self.complete_task,
            self.send_message,
            self.poll_messages,
            self.broadcast_message,
            self.get_shared_state,
            self.set_shared_state,
        ]
