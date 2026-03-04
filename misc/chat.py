import anyio
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    AssistantMessage,
    TextBlock,
)


async def main():
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Write", "Edit"],
        system_prompt="You are a helpful file assistant.",
        cwd=str(Path.cwd()),
    )

    async with ClaudeSDKClient(options=options) as client:
        while True:
            # Get user input in a non-blocking way
            user_input = await anyio.to_thread.run_sync(lambda: input("You: "))

            if user_input.lower() == "exit":
                break

            await client.query(user_input)

            # Receive response
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(f"Claude: {block.text}")


if __name__ == "__main__":
    anyio.run(main)
