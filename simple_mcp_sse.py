
#!/usr/bin/env python3
"""
Simple MCP Server - SSE Version for Render
Compatible with remote access
"""

import os
import asyncio
from mcp.server import Server
from starlette.middleware.cors import CORSMiddleware
from mcp.types import Tool, TextContent
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import Response
import uvicorn

# Create server instance
mcp_server = Server("simple-mcp-sse")

# Create transport ONCE at module level (not inside the handler)
transport = SseServerTransport("/messages")

@mcp_server.list_tools()
async def list_tools():
    return [
        Tool(
            name="echo",
            description="Echo back the input text",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to echo back"
                    }
                },
                "required": ["text"]
            }
        ),
        Tool(
            name="add",
            description="Add two numbers",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "number"},
                    "b": {"type": "number"}
                },
                "required": ["a", "b"]
            }
        )
    ]

@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "echo":
        text = arguments.get("text", "")
        return [TextContent(type="text", text=f"Echo: {text}")]
    elif name == "add":
        a = arguments.get("a", 0)
        b = arguments.get("b", 0)
        return [TextContent(type="text", text=f"Result: {a + b}")]
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

async def handle_sse(request):
    """Handle SSE connections"""
    async with transport.connect_sse(request.scope, request.receive, request._send) as streams:
        await mcp_server.run(
            streams[0],
            streams[1],
            mcp_server.create_initialization_options()
        )

async def handle_messages(request):
    """Handle message posts from client — THIS IS THE FIX"""
    await transport.handle_post_message(request.scope, request.receive, request._send)

async def health_check(request):
    return Response("OK", media_type="text/plain")

app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse,methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]),
        Route("/messages", endpoint=handle_messages, methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]),
        Route("/health", endpoint=health_check),
        Route("/", endpoint=health_check),
    ]
)
# Add CORS middleware 
app.add_middleware( 
    CORSMiddleware, 
    allow_origins=["*"], # Allow all origins 
    allow_methods=["*"], # Allow all HTTP methods 
    allow_headers=["*"], # Allow all headers 
    allow_credentials=True # Allow cookies/auth headers if needed 
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting MCP SSE Server on 0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)