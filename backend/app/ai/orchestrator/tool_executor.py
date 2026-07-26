"""Execute registered tools on behalf of agents."""

from ..tools.base import Tool

class ToolExecutor:
    async def execute(self, tool: Tool, *args, **kwargs):
        return await tool.run(*args, **kwargs)
