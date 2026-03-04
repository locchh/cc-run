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
    TextBlock,
    ClaudeSDKClient,
)


async def resume_session():

    session_id = "11ece7bb-61cc-4374-8800-663bfc9e2932"
    print(f"=== Resuming session {session_id} ===")

    options = ClaudeAgentOptions(
        resume=session_id,
    )

    async with ClaudeSDKClient(options=options) as client:                                                         
      await client.query("What's my name? (You should remember from earlier.)")                                  
      async for message in client.receive_response():                                                            
          if isinstance(message, AssistantMessage):                                                              
              for block in message.content:                 
                  if isinstance(block, TextBlock):
                      print(f"Claude: {block.text}")

async def main():
    await resume_session()


if __name__ == "__main__":
    anyio.run(main)
