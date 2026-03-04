# A2A Experiment — Claude Code Multi-Terminal Communication

The goal: run an A2A agent server in one terminal, then have Claude Code in another terminal communicate with it using the **a2a-bridge MCP**.

```ascii
Terminal A                          Terminal B
──────────────────────────          ──────────────────────────
python a2a_agent_v2.py              claude (Claude Code)
(AssistantAgent :8080)  ←── A2A ── (with a2a MCP bridge)
```

---

## Tools Used

| Tool | Purpose |
|------|---------|
| [GongRzhe/A2A-MCP-Server](https://github.com/GongRzhe/A2A-MCP-Server) | MCP bridge between Claude Code and A2A agents |
| [a2a SDK](https://github.com/google-a2a/a2a-python) | Google's Agent-to-Agent Python SDK |
| [claude-agent-sdk](https://github.com/anthropics/claude-agent-sdk-python) | Powering the assistant inside the agent |
| FastAPI + uvicorn | HTTP server for the A2A agent (v2) |

---

## Setup

### 1 — Add the MCP to Claude Code (project scope, once)

**Original (GongRzhe):**
```bash
claude mcp add --scope project a2a -- uvx a2a-mcp-server
```

**Our fixed fork (recommended):**
```bash
claude mcp add --scope project a2a -- uvx --from git+https://github.com/locchh/A2A-MCP-Server a2a-mcp-server
```

> The original has a bug where `send_message` returns empty — see [Problems & Fixes](#problems--fixes).

Verify:

```bash
claude mcp list
```

### 2 — Start the agent (Terminal A)

```bash
cd ~/Works/snx
python a2a_agent_v2.py
# INFO: Starting assistant agent (v2) on 0.0.0.0:8080
```

### 3 — Talk to it from Claude Code (Terminal B)

```bash
cd ~/Works/snx
claude
```

Ask Claude to register and communicate:

```
Register the A2A agent at http://localhost:8080, then ask it what files are in this project.
```

Claude will call these MCP tools in sequence:

1. `register_agent http://localhost:8080`
2. `send_message` → returns a `task_id`
3. `get_task_result task_id` → returns the agent's response

---

## Available MCP Tools

| Tool | What it does |
|------|-------------|
| `register_agent` | Register an A2A agent by URL |
| `list_agents` | List all registered agents |
| `unregister_agent` | Remove an agent |
| `send_message` | Send a prompt, returns `task_id` |
| `get_task_result` | Fetch the response by `task_id` |
| `send_message_stream` | Send with streaming (requires streaming=True agent) |
| `cancel_task` | Cancel a running task |

---

## Problems & Fixes

### Problem 1 — Protocol mismatch (a2a_agent.py v1)

`a2a_agent.py` used the new **A2A SDK 0.3.0** (`message/send`, `kind: "text"`).
The MCP bridge uses the **old protocol** (`tasks/send`, `type: "text"`).

**Fix:** Rewrote the agent as `a2a_agent_v2.py` — a plain FastAPI JSON-RPC server that speaks the old protocol the bridge expects, with no A2A SDK dependency.

### Problem 2 — `send_message` always returned empty (MCP bridge bug)

In `a2a_mcp_server.py`, the `send_message` tool accessed the wrong level of the response:

```python
# Bug: result is SendTaskResponse, not Task
if hasattr(result, "status") ...       # always False
for artifact in result.artifacts ...   # always empty

# Fix: Task is wrapped inside result.result
task = result.result
if hasattr(task, "status") ...
for artifact in task.artifacts ...
```

`SendTaskResponse` wraps the `Task` in its `.result` field, but the bridge was checking `.status` directly on the response object.

**Fix:** Forked the repo → [locchh/A2A-MCP-Server](https://github.com/locchh/A2A-MCP-Server) and patched `send_message` to extract data from `result.result` instead of `result`.

### Problem 3 — `get_task_result` returned empty (our server)

Even after fixing the bridge, `get_task_result` needed the task to be stored server-side. The original `a2a_agent_v2.py` returned an error for `tasks/get`.

**Fix:** Added a `task_store` dict in `a2a_agent_v2.py` — tasks are saved on `tasks/send` and returned on `tasks/get`.

---

## Multi-Agent Setup

Run multiple agents on different ports and have Claude coordinate:

```bash
# Terminal A
ASSISTANT_PORT=8080 python a2a_agent_v2.py

# Terminal B
ASSISTANT_PORT=8081 python a2a_agent_v2.py

# Terminal C — Claude Code
claude
# Register agents at :8080 and :8081, ask both the same question and compare.
```

---

## Claude Code ↔ Claude Code

The ideal: open two terminals, run `claude` in each, and let them talk to each other.

```
Terminal A                              Terminal B
──────────────────────────              ──────────────────────────
claude                                  claude
  │  a2a MCP bridge                       │  a2a MCP bridge
  │                                       │
  └──── send_message ────────────────────►?
                                          ↑
                               no A2A endpoint here
```

### How Sessions Discover Each Other

The `a2a-mcp-server` persists state to two JSON files in the project:

```
registered_agents.json     ← who is available
task_agent_mapping.json    ← task_id → agent URL
```

Both terminals connect to their own `uvx a2a-mcp-server` process, but both read and write the **same files on disk** — so they share state automatically:

```
Terminal A (claude)                Terminal B (claude)
    │  uvx a2a-mcp-server               │  uvx a2a-mcp-server
    │        │                          │        │
    │        └──── registered_agents.json ───────┘
    │              task_agent_mapping.json
```

- Terminal B registers an agent → written to `registered_agents.json`
- Terminal A calls `list_agents` → reads the same file → sees Terminal B's agent

This means **discovery already works** across sessions with no extra infrastructure.

---

## Multi-Agent Team Experiment

We tried a simpler experiment — no A2A protocol, no sidecars. Just multiple Claude Code sessions each with a persona, communicating through a shared file.

### Structure

```
tmp/
├── agents.json        ← shared state + inboxes
├── alice/
│   └── CLAUDE.md      ← "You are Alice, a code reviewer"
├── bob/
│   └── CLAUDE.md      ← "You are Bob, a test writer"
└── tom/
    └── CLAUDE.md      ← "You are Tom, a documentation writer"
```

Each `CLAUDE.md` defines the agent's persona and instructs it to read/write `agents.json` to communicate:

```json
{
  "alice": { "inbox": [] },
  "bob":   { "inbox": [{"from": "alice", "message": "write tests for add(a,b)"}] },
  "tom":   { "inbox": [{"from": "alice", "message": "write docs for add(a,b)"}] }
}
```

Run each in its own terminal:

```bash
cd tmp/alice && claude   # Terminal 1
cd tmp/bob   && claude   # Terminal 2
cd tmp/tom   && claude   # Terminal 3
```

### The Problem — No Real-Time Communication

The shared file works, but it requires each Claude to **actively poll** — it only sees messages when told to check. There is no way for Bob to know Alice sent him something without reading the file first.

This is not true communication — it is more like a bulletin board.

### Why We Need a Broker

For real-time communication between Claude Code sessions, you need a **message broker** — one persistent server all sessions connect to:

```
alice (claude) ──┐
                 ├──► broker :9000
bob   (claude) ──┤        │
                 │   messages stored
tom   (claude) ──┘   and routed live
```

Each Claude session uses MCP tools to talk to the broker:
- `send_message(to="bob", text="...")` → broker stores it immediately
- `get_messages(for="alice")` → broker returns waiting messages

| Approach | Real-time | Extra process |
|----------|-----------|---------------|
| Shared JSON file | ❌ polling | ❌ none |
| Message broker | ✅ instant | ✅ one server |
| `a2a_agent_v2.py` per agent | ✅ instant | ✅ one per agent |

The broker is the right balance — one small server, no Claude running inside it, just routes messages between sessions. `a2a_agent_v2.py` is overkill here since it runs a full Claude instance inside each agent.

---

## References

- [locchh/A2A-MCP-Server](https://github.com/locchh/A2A-MCP-Server) — our fixed fork
- [GongRzhe/A2A-MCP-Server](https://github.com/GongRzhe/A2A-MCP-Server) — original
- [A2A Bridge on MCPMarket](https://mcpmarket.com/server/a2a-bridge)
- [google-a2a/a2a-python](https://github.com/google-a2a/a2a-python)
