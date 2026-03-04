## Session

Session features:

- Support human's permissions -> permission callback

- Support human's intermediate input

- Intermediate output -> Skip

- File output

- Interaction, Feedback

- Fallback, Handle errors gracefully

- Resource monitor

```ascii
╔══════════════════════════════════════════════════════════════╗
║                         REST APP                             ║
║                                                              ║
║  ╔════════════════════════════════════════════════════════╗  ║
║  ║                       Session                          ║  ║
║  ║                                                        ║  ║
║  ║  ╔═══════════════════════════════════════════════╗     ║  ║
║  ║  ║                  Claude Code                  ║     ║  ║
║  ║  ║                                               ║     ║  ║
║  ║  ║   ┌─────────────┐     ┌─────────────────┐     ║     ║  ║
║  ║  ║   │  LLM Proxy  │     │      Skill      │     ║     ║  ║
║  ║  ║   │             │     │                 │     ║     ║  ║
║  ║  ║   └─────────────┘     └─────────────────┘     ║     ║  ║
║  ║  ║                                               ║     ║  ║
║  ║  ╚═══════════════════════════════════════════════╝     ║  ║
║  ║                                                        ║  ║
║  ╚════════════════════════════════════════════════════════╝  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sessions` | Create + start session (returns run_id) |
| GET | `/sessions/{id}` | Get status, output_files, error |
| GET | `/sessions/{id}/stream` | SSE stream - drains _message_queue |
| POST | `/sessions/{id}/input` | Send input() when IDLE |
| POST | `/sessions/{id}/cancel` | Cancel session |
| DELETE | `/sessions/{id}` | Close session |
| GET | `/sessions/{id}/files/{name}` | Download output file |

## SSE Stream

The SSE stream is the key - the client connects to `/stream` and receives all messages as server-sent events:

- **AssistantMessage** - Claude's responses
- **ToolUseBlock** - Tool execution requests  
- **_IdleEvent** - "Claude is waiting for your input now"
- **_ErrorEvent** - Error messages

**_IdleEvent** tells the frontend when to show the input box.

## Typical Flow

```
POST /sessions     → run_id
GET  /stream       → ...messages... → IdleEvent (Claude asking question)
POST /input        → user answer
GET  /stream       → ...messages... → IdleEvent (Claude asking again)  
POST /input        → user answer
GET  /stream       → ...messages... → IdleEvent (files written)
DELETE /sessions   → cleanup
```

**Notes**
- One `ClaudeSDKClient` per session
- wait-for-full-result

## Message Types

Message Hierarchy:

```
Message (base type)
├── UserMessage
│   ├── content: str | list[ContentBlock]
│   ├── uuid: str | None
│   ├── parent_tool_use_id: str | None
│   └── tool_use_result: dict[str, Any] | None
│
├── AssistantMessage  
│   ├── content: list[ContentBlock]
│   ├── model: str
│   ├── parent_tool_use_id: str | None
│   └── error: AssistantMessageError | None
│
├── SystemMessage
│   ├── subtype: str
│   └── data: dict[str, Any]
│
└── ResultMessage
    ├── subtype: str
    ├── duration_ms: int
    └── duration_api_ms: int
```

## Content Block Types

Content Block Hierarchy:

```
ContentBlock (union type)
├── TextBlock
│   └── text: str
│
├── ThinkingBlock
│   ├── thinking: str
│   └── signature: str
│
├── ToolUseBlock
│   ├── id: str
│   ├── name: str
│   └── input: dict[str, Any]
│
└── ToolResultBlock
    ├── tool_use_id: str
    ├── content: str | list[dict[str, Any]] | None
    └── is_error: bool | None
```

## System Message

Example System:

```
SystemMessage(
    subtype='init', 
    data={
        'type': 'system', 
        'subtype': 'init', 
        'cwd': '/home/locch/Works/snx', 
        'session_id': '27ae3f62-9f96-4347-9874-783a3435ce10', 
        'tools': [
            'Agent', 'TaskOutput', 'Bash', 'Glob', 'Grep', 
            'ExitPlanMode', 'Read', 'Edit', 'Write', 
            'NotebookEdit', 'WebFetch', 'TodoWrite', 'WebSearch', 
            'TaskStop', 'AskUserQuestion', 'Skill', 'EnterPlanMode', 
            'EnterWorktree', 'TeamCreate', 'TeamDelete', 
            'SendMessage', 'ToolSearch'
        ], 
        'mcp_servers': [], 
        'model': 'claude-sonnet-4-6', 
        'permissionMode': 'default', 
        'slash_commands': [
            'debug', 'simplify', 'batch', 'compact', 'context', 
            'cost', 'init', 'pr-comments', 'release-notes', 
            'review', 'security-review', 'insights'
        ], 
        'apiKeySource': 'none', 
        'claude_code_version': '2.1.63', 
        'output_style': 'default', 
        'agents': [
            'general-purpose', 'statusline-setup', 'Explore', 'Plan'
        ], 
        'skills': ['debug', 'simplify', 'batch'], 
        'plugins': [], 
        'uuid': 'f81623ca-b344-4cbd-9767-a09ebda430a7', 
        'fast_mode_state': 'off'
    }
)
```