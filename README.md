# stonemux

**Multi-agent coordination for AI frameworks.**

A compiled Rust MCP server that orchestrates multiple agent instances with inboxes, task dispatch, broadcast channels, and doorbell webhooks. No tmux. No polling. Framework-independent and local-first.

![Rust](https://img.shields.io/badge/Built_with-Rust-dea584?style=flat-square) ![License](https://img.shields.io/badge/License-Proprietary-red?style=flat-square) ![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux-blue?style=flat-square)

## Install

```bash
brew install thekeystoneproject/tap/stonemux
```

Or download the binary from [keystoneproject.dev](https://keystoneproject.dev).

## Quickstart

```bash
# Start the server
stonemux serve

# Activate your license key
stonemux activate SX-XXXX-XXXX-XXXX-XXXX
```

Point any MCP-compatible agent platform at `127.0.0.1:3392`. That's it.

## Configuration

```toml
# ~/.stonemux/config.toml
host = "127.0.0.1"
port = 3392
data_dir = "~/.stonemux"
```

Environment overrides: `STONEMUX_HOST`, `STONEMUX_PORT`, `STONEMUX_DATA_DIR`.

## Features

- **Per-agent inbox** with priority routing
- **Doorbell webhooks** — instant notification on new messages
- **Long-poll fallback** for restricted environments
- **Structured task lifecycle** — create, claim, complete
- **Broadcast channel** for fleet-wide announcements
- **Agent directory** with heartbeat monitoring

## Works with

Any platform that speaks MCP connects directly:

- Claude Code / Claude Desktop
- Hermes
- CrewAI
- LangGraph
- OpenHands
- Haystack
- Google ADK
- Microsoft Agent Framework

## Pricing

|                         | Free | Pro ($14/mo) | Enterprise ($59/mo) |
| ----------------------- | ---- | ------------ | ------------------- |
| Registered agents       | 3    | Unlimited    | Unlimited           |
| Task dispatch           | Yes  | Yes          | Yes                 |
| Event bus               | Yes  | Yes          | Yes                 |
| State persistence       | —    | Yes          | Yes                 |
| Priority routing        | —    | Yes          | Yes                 |
| Cross-team coordination | —    | —            | Yes                 |

Get a key at [keystoneproject.dev](https://keystoneproject.dev).

## Data ownership

Your data stays on your machine, in open SQLite databases you own. No cloud dependency. No vendor lock-in.

## Documentation

Full documentation at [keystoneproject.dev/docs](https://keystoneproject.dev/docs/).

## Stone Suite

stonemux is part of the Stone suite — three compiled Rust MCP servers for AI agent infrastructure:

- **[stonemem](https://github.com/thekeystoneproject/stonemem)** — Institutional memory
- **stonemux** — Multi-agent coordination *(this repo)*
- **[stonegate](https://github.com/thekeystoneproject/stonegate)** — Universal tool gateway

## License

[Proprietary](LICENSE) — Copyright (c) 2026 The Keystone Project, Inc. All rights reserved.
