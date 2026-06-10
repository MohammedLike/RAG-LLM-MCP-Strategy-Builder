import json
from . import TOOLS
import asyncio

class MCPServer:
    def __init__(self):
        self.tools = {tool["name"]: tool for tool in TOOLS}
        
    def get_tool_schemas(self):
        return [
            {
                "name": name,
                "description": tool["description"],
                "schema": tool["schema"].model_json_schema()
            }
            for name, tool in self.tools.items()
        ]
        
    async def execute_tool(self, tool_name: str, arguments: dict) -> dict:
        if tool_name not in self.tools:
            return {"error": f"Tool {tool_name} not found"}
            
        tool = self.tools[tool_name]
        try:
            # Validate using pydantic schema
            input_model = tool["schema"](**arguments)
            # Execute function (check if async)
            if asyncio.iscoroutinefunction(tool["func"]):
                result = await tool["func"](input_model)
            else:
                result = tool["func"](input_model)
            return result
        except Exception as e:
            return {"error": str(e)}

server = MCPServer()
