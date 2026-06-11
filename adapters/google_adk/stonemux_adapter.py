"""stonemux coordination adapter for Google ADK (Agent Development Kit).

Provides Google ADK-compatible tool declarations for multi-agent coordination.
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

    def request(self, method: str, path: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
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


class StonemuxADKTools:
    """Google ADK tool integration for stonemux coordination.

    Provides function declarations and handlers compatible with Google's
    Agent Development Kit tool registration.

    Usage:
        tools = StonemuxADKTools(
            agent_id="searcher-1", role="searcher",
            capabilities=["web_search"]
        )
        agent = Agent(tools=tools.get_function_declarations())
    """

    def __init__(
        self,
        agent_id: str = "adk-agent",
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
        return self.client.request("POST", "/agent/register", {
            "agent_id": self.agent_id,
            "role": self.role,
            "capabilities": self.capabilities,
            "group": self.group,
            "channel": self.channel,
        })

    def get_function_declarations(self) -> list[dict[str, Any]]:
        """Return ADK-compatible function declarations."""
        return [
            {
                "name": "stonemux_discover_agents",
                "description": "Discover other agents registered in the coordination bus",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string", "description": "Filter agents by role"},
                        "group": {"type": "string", "description": "Filter agents by group"},
                    },
                },
            },
            {
                "name": "stonemux_post_task",
                "description": "Post a task for other agents to claim and complete",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string", "description": "Task description"},
                        "required_capability": {"type": "string", "description": "Capability needed to claim"},
                        "priority": {"type": "integer", "description": "Task priority (higher = more urgent)"},
                    },
                    "required": ["description"],
                },
            },
            {
                "name": "stonemux_claim_task",
                "description": "Claim the next available task matching your capabilities",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "stonemux_complete_task",
                "description": "Mark a claimed task as complete with a result",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "ID of the task to complete"},
                        "result": {"type": "string", "description": "Task result or output"},
                    },
                    "required": ["task_id", "result"],
                },
            },
            {
                "name": "stonemux_send_message",
                "description": "Send a direct message to another agent",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "to": {"type": "string", "description": "Target agent ID"},
                        "content": {"type": "string", "description": "Message content"},
                    },
                    "required": ["to", "content"],
                },
            },
            {
                "name": "stonemux_poll_messages",
                "description": "Check for new messages sent to this agent",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "timeout": {"type": "integer", "description": "Poll timeout in seconds"},
                    },
                },
            },
            {
                "name": "stonemux_get_state",
                "description": "Read a shared coordination state value",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string", "description": "State key to read"},
                    },
                    "required": ["key"],
                },
            },
            {
                "name": "stonemux_set_state",
                "description": "Write a shared coordination state value",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string", "description": "State key to write"},
                        "value": {"type": "string", "description": "State value"},
                        "expected_version": {"type": "integer", "description": "Expected version for CAS"},
                    },
                    "required": ["key", "value"],
                },
            },
            {
                "name": "stonemux_broadcast",
                "description": "Broadcast a message to all agents or a specific group",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Message content to broadcast"},
                        "group": {"type": "string", "description": "Target group (omit for all agents)"},
                    },
                    "required": ["content"],
                },
            },
        ]

    def handle_function_call(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Route an ADK function call to the appropriate handler."""
        handlers = {
            "stonemux_discover_agents": self._discover,
            "stonemux_post_task": self._post_task,
            "stonemux_claim_task": self._claim_task,
            "stonemux_complete_task": self._complete_task,
            "stonemux_send_message": self._send_message,
            "stonemux_poll_messages": self._poll_messages,
            "stonemux_get_state": self._get_state,
            "stonemux_set_state": self._set_state,
            "stonemux_broadcast": self._broadcast,
        }
        handler = handlers.get(name)
        if not handler:
            return {"error": f"Unknown function: {name}"}
        return handler(**args)

    def _discover(self, role: str | None = None, group: str | None = None) -> dict[str, Any]:
        params = []
        if role:
            params.append(f"role={role}")
        if group:
            params.append(f"group={group}")
        qs = f"?{'&'.join(params)}" if params else ""
        return self.client.request("GET", f"/agent/discover{qs}")

    def _post_task(self, description: str, required_capability: str | None = None, priority: int = 0) -> dict[str, Any]:
        return self.client.request("POST", "/task/post", {
            "description": description,
            "posted_by": self.agent_id,
            "required_capability": required_capability,
            "priority": priority,
            "channel": self.channel,
        })

    def _claim_task(self) -> dict[str, Any]:
        return self.client.request("POST", "/task/claim", {
            "agent_id": self.agent_id,
            "channel": self.channel,
        })

    def _complete_task(self, task_id: str, result: str) -> dict[str, Any]:
        return self.client.request("POST", "/task/complete", {
            "task_id": task_id,
            "agent_id": self.agent_id,
            "result": result,
            "status": "complete",
        })

    def _send_message(self, to: str, content: str) -> dict[str, Any]:
        return self.client.request("POST", "/msg/send", {
            "from": self.agent_id,
            "to": to,
            "content": content,
            "channel": self.channel,
        })

    def _poll_messages(self, timeout: int = 5) -> dict[str, Any]:
        return self.client.request("GET", f"/msg/poll?agent_id={self.agent_id}&timeout={timeout}")

    def _get_state(self, key: str) -> dict[str, Any]:
        return self.client.request("GET", f"/state/get?key={key}&channel={self.channel}")

    def _set_state(self, key: str, value: str, expected_version: int | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "channel": self.channel,
            "key": key,
            "value": value,
            "updated_by": self.agent_id,
        }
        if expected_version is not None:
            payload["expected_version"] = expected_version
        return self.client.request("POST", "/state/set", payload)

    def _broadcast(self, content: str, group: str | None = None) -> dict[str, Any]:
        return self.client.request("POST", "/msg/broadcast", {
            "from": self.agent_id,
            "group": group,
            "content": content,
            "channel": self.channel,
        })

    def shutdown(self) -> dict[str, Any]:
        return self.client.request("POST", "/agent/deregister", {"agent_id": self.agent_id})
