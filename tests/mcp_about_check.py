"""Comprobación ad hoc (no es test unitario): llama about_iartlabs por MCP stdio."""
import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVICE = Path(__file__).resolve().parents[1] / 'service'


async def main() -> None:
    params = StdioServerParameters(command=sys.executable, args=[str(SERVICE / 'tools_mcp.py'), '--library', sys.argv[1]])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            names = [t.name for t in (await session.list_tools()).tools]
            print('tools:', names)
            result = await session.call_tool('about_iartlabs', {})
            payload = json.loads(result.content[0].text)
            print('site:', payload['site'])
            print('context chars:', len(payload['context']))
            print(payload['context'][:300])


asyncio.run(main())
