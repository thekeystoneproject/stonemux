# stonemux

**Multi-agent coordination engine for AI frameworks.**

![Rust](https://img.shields.io/badge/Built_with-Rust-dea584?style=flat-square) ![MCP](https://img.shields.io/badge/MCP-compatible-blue?style=flat-square) ![Platforms](https://img.shields.io/badge/Adapters-7_platforms-green?style=flat-square) ![License](https://img.shields.io/badge/License-BSL_1.1-yellow?style=flat-square)

stonemux coordinates multiple AI agents across any framework. Agent registry, task routing, event bus, state synchronization, and channel-based messaging — all through a single binary. Connect agents across CrewAI, LangGraph, Hermes, and four more platforms without glue code.

## Install

```bash
brew install thekeystoneproject/tap/stonemux
```

Or download the binary from [Releases](https://github.com/thekeystoneproject/stonemux/releases).

## Quick Start

```bash
# Start the server
stonemux serve

# Register an agent
curl -X POST http://127.0.0.1:3392/agents/register \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "researcher-1", "capabilities": ["search", "summarize"]}'

# Send a task
curl -X POST http://127.0.0.1:3392/tasks/dispatch \
  -H "Content-Type: application/json" \
  -d '{"task": "Research competitor pricing", "target": "researcher-1"}'

# Check status
curl http://127.0.0.1:3392/health
```

## Adapters

MIT-licensed adapters for every major AI agent framework.

| Platform | Directory | Description |
|----------|-----------|-------------|
| [Hermes](adapters/hermes/) | `adapters/hermes/` | Agent coordinator |
| [CrewAI](adapters/crewai/) | `adapters/crewai/` | Crew task router |
| [LangGraph](adapters/langgraph/) | `adapters/langgraph/` | Graph state sync |
| [Haystack](adapters/haystack/) | `adapters/haystack/` | Pipeline coordinator |
| [OpenHands](adapters/openhands/) | `adapters/openhands/` | Agent coordinator |
| [MS Agent Framework](adapters/ms_agent/) | `adapters/ms_agent/` | Agent router |
| [Google ADK](adapters/google_adk/) | `adapters/google_adk/` | Agent coordinator |

Each adapter is a thin Python shim (~150 LOC) that implements the platform's coordination interface and routes all operations to the stonemux REST API.

## Configuration

```toml
# ~/.stonemux/config.toml
host = "127.0.0.1"
port = 3392
data_dir = "~/.stonemux"
```

Environment overrides: `STONEMUX_HOST`, `STONEMUX_PORT`, `STONEMUX_DATA_DIR`

## Pricing

| Feature | Free | Pro ($14/mo) | Enterprise |
|---------|------|--------------|------------|
| Registered agents | 3 | Unlimited | Unlimited |
| Task routing | Yes | Yes | Yes |
| Event bus | Yes | Yes | Yes |
| State persistence | — | Yes | Yes |
| Priority routing | — | Yes | Yes |
| Cross-team coordination | — | — | Yes |

Get a license key at [keystoneproject.dev](https://keystoneproject.dev).

## Links

- [keystoneproject.dev](https://keystoneproject.dev) — Product site and docs
- [stonemem](https://github.com/thekeystoneproject/stonemem) — Institutional memory engine
- [stonegate](https://github.com/thekeystoneproject/stonegate) — MCP tool gateway

## License

The stonemux binary is licensed under [BSL 1.1](LICENSE). Adapters are [MIT licensed](adapters/LICENSE).

Built by [The Keystone Project](https://keystoneproject.dev).
