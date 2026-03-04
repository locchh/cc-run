"""
A2A agent server compatible with a2a-mcp-server v0.1.5 (old protocol).

The MCP bridge uses:
  - JSON-RPC method: tasks/send
  - TextPart with `type: "text"` (not `kind`)
  - Task response with status.state and status.message
"""

import os
import uuid
import asyncio
import logging
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

from agent import Assistant

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

assistant = Assistant()
app = FastAPI()
task_store: dict[str, dict] = {}  # task_id -> task dict


def make_task_response(task_id: str, session_id: str | None, text: str) -> dict:
    """Build a task response in the old A2A protocol format."""
    return {
        "id": task_id,
        "sessionId": session_id,
        "status": {
            "state": "completed",
            "message": {
                "role": "agent",
                "parts": [
                    {"type": "text", "text": text}
                ]
            }
        },
        "artifacts": [],
    }


def make_error_response(rpc_id, code: int, message: str) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": rpc_id,
        "error": {"code": code, "message": message},
    }


@app.get("/.well-known/agent.json")
async def agent_card():
    PORT = int(os.environ.get("ASSISTANT_PORT", 8080))
    HOST = os.environ.get("ASSISTANT_HOST", "0.0.0.0")
    return {
        "name": "Assistant",
        "description": "A helpful assistant powered by Claude.",
        "url": f"http://{HOST}:{PORT}/",
        "version": "1.0.0",
        "capabilities": {"streaming": False},
        "defaultInputModes": ["text"],
        "defaultOutputModes": ["text"],
        "skills": [
            {
                "id": "assistant",
                "name": "Assistant",
                "description": "Answer questions and help with tasks.",
                "tags": ["assistant", "help"],
                "examples": ["What files are in this project?", "Summarize README.md"],
            }
        ],
    }


@app.post("/")
async def handle_jsonrpc(request: Request):
    body = await request.json()
    rpc_id = body.get("id")
    method = body.get("method")
    params = body.get("params", {})

    logger.info(f"RPC method: {method}")

    if method == "tasks/send":
        task_id = params.get("id", str(uuid.uuid4()))
        session_id = params.get("sessionId")
        message = params.get("message", {})

        # Extract text from parts
        text = ""
        for part in message.get("parts", []):
            if part.get("type") == "text":
                text += part.get("text", "")

        if not text:
            return JSONResponse(make_error_response(rpc_id, -32602, "No text in message"))

        logger.info(f"Prompt: {text!r}")
        response_text = await assistant.ask(text)
        logger.info(f"Response: {response_text!r}")

        task = make_task_response(task_id, session_id, response_text)
        task_store[task_id] = task

        return JSONResponse({
            "jsonrpc": "2.0",
            "id": rpc_id,
            "result": task,
        })

    elif method == "tasks/get":
        task_id = params.get("id")
        task = task_store.get(task_id)
        if not task:
            return JSONResponse(make_error_response(rpc_id, -32001, f"Task not found: {task_id}"))
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": rpc_id,
            "result": task,
        })

    elif method == "tasks/cancel":
        return JSONResponse(make_error_response(rpc_id, -32601, "tasks/cancel not supported"))

    else:
        return JSONResponse(make_error_response(rpc_id, -32601, f"Method not found: {method}"))


if __name__ == "__main__":
    PORT = int(os.environ.get("ASSISTANT_PORT", 8080))
    HOST = os.environ.get("ASSISTANT_HOST", "0.0.0.0")
    logger.info(f"Starting assistant agent (v2) on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)
