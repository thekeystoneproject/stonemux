# stonemux

**Multi-agent coordination across frameworks.**

![Rust](https://img.shields.io/badge/Built_with-Rust-dea584?style=flat-square) ![License](https://img.shields.io/badge/License-BSL_1.1-yellow?style=flat-square)

A compiled Rust server that coordinates AI agents across any framework. Agent registry, task dispatch, channel messaging, event streaming, group coordination, and shared state — all through one binary on port 3392. Run agents on CrewAI, LangGraph, Hermes, and four more platforms in one coordinated fleet.

## Install

```bash
brew install thekeystoneproject/tap/stonemux
```

Or download from [Releases](https://github.com/thekeystoneproject/stonemux/releases).

## Quick Start

```bash
stonemux serve
```

### With CrewAI

```python
from stonemux_crewai import StonemuxCrewRouter

router = StonemuxCrewRouter(agent_id="research-crew")
router.dispatch(task="Analyze competitor pricing", target="analyst-1")
```

### With Hermes

```python
from stonemux_hermes import StonemuxCoordinator

coordinator = StonemuxCoordinator(agent_id="hermes-agent-1")
coordinator.register(capabilities=["search", "summarize"])
coordinator.listen()  # SSE event stream
```

## REST API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/agents/register` | POST | Register an agent with capabilities |
| `/agents/deregister` | POST | Deregister an agent |
| `/tasks/dispatch` | POST | Dispatch a task to an agent by capability |
| `/tasks/status` | GET | Task status and results |
| `/msg/send` | POST | Send a message to an agent or channel |
| `/msg/read` | GET | Read messages for an agent |
| `/channels/create` | POST | Create a communication channel |
| `/channels/join` | POST | Join a channel |
| `/state/get` | GET | Read shared coordination state |
| `/state/set` | POST | Write shared coordination state |
| `/events` | GET | SSE event stream for real-time coordination |
| `/stats` | GET | Fleet status and coordination metrics |
| `/health` | GET | Server health check |

## Framework Adapters

Each adapter implements the framework's native coordination interface and routes to stonemux's REST API. Full lifecycle integrations — registration, dispatch, event streaming, state sync.

| Framework | Adapter | What it implements |
|-----------|---------|-------------------|
| [Hermes](adapters/hermes/) | `StonemuxCoordinator` | Agent registration, task dispatch, SSE event listener |
| [CrewAI](adapters/crewai/) | `StonemuxCrewRouter` | Crew task routing with deregister/shutdown |
| [LangGraph](adapters/langgraph/) | `StonemuxGraphSync` | Graph state synchronization across agents |
| [Haystack](adapters/haystack/) | `StonemuxPipelineCoordinator` | Pipeline-level agent coordination |
| [OpenHands](adapters/openhands/) | `StonemuxAgentCoordinator` | Agent coordination with event streaming |
| [MS Agent Framework](adapters/ms_agent/) | `StonemuxAgentRouter` | Agent routing and state management |
| [Google ADK](adapters/google_adk/) | `StonemuxADKCoordinator` | Full ADK coordination including broadcast/discover |

All adapters are MIT licensed.

## Configuration

```toml
# ~/.stonemux/config.toml
host = "127.0.0.1"
port = 3392
data_dir = "~/.stonemux"
```

`STONEMUX_HOST`, `STONEMUX_PORT`, `STONEMUX_DATA_DIR` environment overrides.

## Pricing

| | Free | Pro ($14/mo) | Enterprise |
|---|------|--------------|------------|
| Registered agents | 3 | Unlimited | Unlimited |
| Task dispatch | Yes | Yes | Yes |
| Event bus | Yes | Yes | Yes |
| State persistence | — | Yes | Yes |
| Priority routing | — | Yes | Yes |
| Cross-team coordination | — | — | Yes |

```bash
stonemux activate SX-XXXX-XXXX-XXXX-XXXX
```

Get a key at [keystoneproject.dev](https://keystoneproject.dev).

## Stone Suite

| Server | Purpose |
|--------|---------|
| [stonemem](https://github.com/thekeystoneproject/stonemem) | Persistent agent memory |
| **stonemux** | Multi-agent coordination |
| [stonegate](https://github.com/thekeystoneproject/stonegate) | MCP tool gateway |

## License

Binary: [BSL 1.1](LICENSE). Adapters: [MIT](adapters/LICENSE).

[The Keystone Project](https://keystoneproject.dev)
