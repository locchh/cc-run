"""
Simple message broker MCP server for multi-agent Claude Code communication.

Each Claude Code session connects to this broker via MCP and can:
  - register itself by name
  - send messages to other agents
  - read its own inbox
  - acknowledge (remove) messages after reading

Run:
    python broker.py
"""

from datetime import datetime

from fastmcp import FastMCP

mcp = FastMCP("broker")

# In-memory state
agents: dict[str, dict] = {}   # name -> {registered_at}
inbox: dict[str, list] = {}    # name -> [{from, text, timestamp}]


@mcp.tool()
def register(name: str) -> str:
    """Register this agent with the broker so others can discover it."""
    agents[name] = {"registered_at": datetime.now().isoformat()}
    if name not in inbox:
        inbox[name] = []
    return f"Registered as '{name}'. {len(agents)} agent(s) online: {list(agents.keys())}"


@mcp.tool()
def list_agents() -> list[str]:
    """List all currently registered agents."""
    return list(agents.keys())


@mcp.tool()
def send(to: str, sender: str, text: str) -> str:
    """Send a message to another agent."""
    if to not in agents:
        return f"Agent '{to}' is not registered. Online agents: {list(agents.keys())}"
    if to not in inbox:
        inbox[to] = []
    inbox[to].append({
        "from": sender,
        "text": text,
        "timestamp": datetime.now().isoformat(),
    })
    return f"Message sent to '{to}'."


@mcp.tool()
def get_messages(name: str) -> list[dict]:
    """Fetch all messages in your inbox."""
    return inbox.get(name, [])


@mcp.tool()
def ack(name: str, index: int) -> str:
    """Remove a message from your inbox after reading (0-indexed)."""
    messages = inbox.get(name, [])
    if index < 0 or index >= len(messages):
        return f"No message at index {index}. You have {len(messages)} message(s)."
    removed = messages.pop(index)
    return f"Message from '{removed['from']}' removed."


if __name__ == "__main__":
    mcp.run(transport="stdio")
