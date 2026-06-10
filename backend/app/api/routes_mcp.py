from fastapi import APIRouter
from pydantic import BaseModel

from ..mcp.server import server

router = APIRouter()

class ToolExecuteRequest(BaseModel):
    tool_name: str
    arguments: dict

@router.get("/mcp/tools")
async def get_tool_schemas():
    return {"tools": server.get_tool_schemas()}

@router.post("/mcp/execute")
async def execute_tool(request: ToolExecuteRequest):
    result = await server.execute_tool(request.tool_name, request.arguments)
    return {"result": result}
