"""
Demonstrate session persistence: start a session, exit, then resume it.

Runs start_session then resume_session in sequence.
session_id is captured from ResultMessage and passed to resume via ClaudeAgentOptions(resume=...).
"""

import anyio
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

# Unset CLAUDECODE so the subprocess doesn't think it's nested inside Claude Code
os.environ.pop("CLAUDECODE", None)

from claude_agent_sdk import (
    ClaudeAgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    query,
)


class AgentSession:
    def __init__(self):
        self.run_id = uuid.uuid4()
        self.session_id = None


session = AgentSession()


async def start_session():
    print("=== Starting new session ===")
    options = ClaudeAgentOptions(
        system_prompt="You are a helpful assistant.",
    )

    async for message in query(
        prompt="Remember this: my name is Loc. Just acknowledge it briefly.",
        options=options,
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Claude: {block.text}")
        elif isinstance(message, ResultMessage):
            session.session_id = message.session_id
            print(f"Session ID: {session.session_id}")


async def resume_session():
    print(f"=== Resuming session {session.session_id} ===")

    options = ClaudeAgentOptions(
        resume=session.session_id,
    )

    async for message in query(
        prompt="What's my name? (You should remember from earlier.)",
        options=options,
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Claude: {block.text}")


async def main():
    await start_session()
    await resume_session()


if __name__ == "__main__":
    anyio.run(main)
