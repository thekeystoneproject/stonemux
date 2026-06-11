"""stonemux coordination adapter for LangGraph.

Provides LangGraph-compatible tool nodes for multi-agent coordination.
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


def create_coordination_tools(
    agent_id: str = "langgraph-agent",
    role: str = "assistant",
    capabilities: list[str] | None = None,
    group: str | None = None,
    channel: str = "default",
    base_url: str = "http://127.0.0.1:3392",
) -> dict[str, Any]:
    """Create stonemux coordination tools for LangGraph.

    Returns a dict of tool functions suitable for use as LangGraph tool nodes.
    Auto-registers the agent on creation.

    Usage:
        tools = create_coordination_tools("researcher-1", "researcher", ["search"])
        graph.add_node("discover", tools["discover"])
        graph.add_node("post_task", tools["post_task"])
    """
    client = StonemuxClient(base_url)
    caps = capabilities or []

    client.request("POST", "/agent/register", {
        "agent_id": agent_id,
        "role": role,
        "capabilities": caps,
        "group": group,
        "channel": channel,
    })

    def discover(state: dict[str, Any] | None = None, role_filter: str | None = None, group_filter: str | None = None) -> dict[str, Any]:
        """Discover registered agents."""
        params = []
        if role_filter:
            params.append(f"role={role_filter}")
        if group_filter:
            params.append(f"group={group_filter}")
        qs = f"?{'&'.join(params)}" if params else ""
        return client.request("GET", f"/agent/discover{qs}")

    def post_task(description: str, required_capability: str | None = None, priority: int = 0, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        """Post a task for other agents."""
        return client.request("POST", "/task/post", {
            "description": description,
            "posted_by": agent_id,
            "required_capability": required_capability,
            "priority": priority,
            "channel": channel,
            "metadata": metadata or {},
        })

    def claim_task() -> dict[str, Any]:
        """Claim the next available task matching capabilities."""
        return client.request("POST", "/task/claim", {
            "agent_id": agent_id,
            "channel": channel,
        })

    def complete_task(task_id: str, result: str, status: str = "complete") -> dict[str, Any]:
        """Mark a task as complete."""
        return client.request("POST", "/task/complete", {
            "task_id": task_id,
            "agent_id": agent_id,
            "result": result,
            "status": status,
        })

    def send_msg(to: str, content: str) -> dict[str, Any]:
        """Send a message to another agent."""
        return client.request("POST", "/msg/send", {
            "from": agent_id,
            "to": to,
            "content": content,
            "channel": channel,
        })

    def poll_msg(timeout: int = 5) -> dict[str, Any]:
        """Poll for new messages."""
        return client.request("GET", f"/msg/poll?agent_id={agent_id}&timeout={timeout}")

    def broadcast(content: str, target_group: str | None = None) -> dict[str, Any]:
        """Broadcast a message to all agents or a group."""
        return client.request("POST", "/msg/broadcast", {
            "from": agent_id,
            "group": target_group,
            "content": content,
            "channel": channel,
        })

    def get_state(key: str) -> dict[str, Any]:
        """Read shared state."""
        return client.request("GET", f"/state/get?key={key}&channel={channel}")

    def set_state(key: str, value: str, expected_version: int | None = None) -> dict[str, Any]:
        """Write shared state with optional CAS."""
        payload: dict[str, Any] = {
            "channel": channel,
            "key": key,
            "value": value,
            "updated_by": agent_id,
        }
        if expected_version is not None:
            payload["expected_version"] = expected_version
        return client.request("POST", "/state/set", payload)

    def deregister() -> dict[str, Any]:
        """Deregister this agent from coordination."""
        return client.request("POST", "/agent/deregister", {"agent_id": agent_id})

    return {
        "discover": discover,
        "post_task": post_task,
        "claim_task": claim_task,
        "complete_task": complete_task,
        "send_msg": send_msg,
        "poll_msg": poll_msg,
        "broadcast": broadcast,
        "get_state": get_state,
        "set_state": set_state,
        "deregister": deregister,
    }
