"""stonemux coordination adapter for Haystack.

Provides a Haystack-compatible component for multi-agent coordination.
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


class StonemuxCoordinator:
    """Haystack component for stonemux multi-agent coordination.

    Integrates with Haystack pipelines as a component that enables
    agents to coordinate via stonemux.

    Usage:
        coordinator = StonemuxCoordinator(
            agent_id="indexer-1", role="indexer",
            capabilities=["index", "search"]
        )
        # In a Haystack pipeline:
        pipeline.add_component("coordinator", coordinator)
    """

    def __init__(
        self,
        agent_id: str = "haystack-agent",
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

    def run(self, action: str, **kwargs: Any) -> dict[str, Any]:
        """Execute a coordination action.

        Args:
            action: One of discover, post_task, claim_task, complete_task,
                    send_msg, poll_msg, broadcast, get_state, set_state.
            **kwargs: Action-specific parameters.

        Returns:
            Dict with action results.
        """
        actions = {
            "discover": self._discover,
            "post_task": self._post_task,
            "claim_task": self._claim_task,
            "complete_task": self._complete_task,
            "send_msg": self._send_msg,
            "poll_msg": self._poll_msg,
            "broadcast": self._broadcast,
            "get_state": self._get_state,
            "set_state": self._set_state,
            "deregister": self._deregister,
        }
        handler = actions.get(action)
        if not handler:
            return {"error": f"Unknown action: {action}", "available": list(actions.keys())}
        return handler(**kwargs)

    def _discover(self, role: str | None = None, group: str | None = None) -> dict[str, Any]:
        params = []
        if role:
            params.append(f"role={role}")
        if group:
            params.append(f"group={group}")
        qs = f"?{'&'.join(params)}" if params else ""
        return self.client.request("GET", f"/agent/discover{qs}")

    def _post_task(self, description: str, required_capability: str | None = None, priority: int = 0, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.client.request("POST", "/task/post", {
            "description": description,
            "posted_by": self.agent_id,
            "required_capability": required_capability,
            "priority": priority,
            "channel": self.channel,
            "metadata": metadata or {},
        })

    def _claim_task(self) -> dict[str, Any]:
        return self.client.request("POST", "/task/claim", {
            "agent_id": self.agent_id,
            "channel": self.channel,
        })

    def _complete_task(self, task_id: str, result: str, status: str = "complete") -> dict[str, Any]:
        return self.client.request("POST", "/task/complete", {
            "task_id": task_id,
            "agent_id": self.agent_id,
            "result": result,
            "status": status,
        })

    def _send_msg(self, to: str, content: str) -> dict[str, Any]:
        return self.client.request("POST", "/msg/send", {
            "from": self.agent_id,
            "to": to,
            "content": content,
            "channel": self.channel,
        })

    def _poll_msg(self, timeout: int = 5) -> dict[str, Any]:
        return self.client.request("GET", f"/msg/poll?agent_id={self.agent_id}&timeout={timeout}")

    def _broadcast(self, content: str, group: str | None = None) -> dict[str, Any]:
        return self.client.request("POST", "/msg/broadcast", {
            "from": self.agent_id,
            "group": group,
            "content": content,
            "channel": self.channel,
        })

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

    def _deregister(self) -> dict[str, Any]:
        return self.client.request("POST", "/agent/deregister", {"agent_id": self.agent_id})
