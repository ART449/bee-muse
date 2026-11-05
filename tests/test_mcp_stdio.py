import asyncio
import json
from pathlib import Path
import sys
import tempfile
import unittest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT=Path(__file__).resolve().parents[1]

class McpStdioTests(unittest.TestCase):
    def test_an_external_client_can_discover_and_search(self):
        async def run():
            with tempfile.TemporaryDirectory() as folder:
                base=Path(folder)
                (base/'catalog.json').write_text(json.dumps({'files':[{'id':'a'*20,'name':'demo.html','title':'Demo MCP','path':str(base/'demo.html')}]}),encoding='utf-8')
                params=StdioServerParameters(command=sys.executable,args=[str(ROOT/'service'/'tools_mcp.py'),'--library',folder])
                async with stdio_client(params) as (reader,writer):
                    async with ClientSession(reader,writer) as session:
                        await session.initialize()
                        listed=await session.list_tools()
                        names={tool.name for tool in listed.tools}
                        self.assertIn('search_html',names);self.assertIn('inbeebox_messages',names)
                        self.assertTrue({'browser_open','browser_search','browser_back','browser_forward','browser_reload','browser_state'} <= names)
                        result=await session.call_tool('search_html',{'query':'Demo MCP'})
                        self.assertFalse(result.isError)
                        data=result.structuredContent or json.loads(result.content[0].text)
                        self.assertEqual(data['matches'],1)
                        self.assertEqual(data['files'][0]['name'],'demo.html')
        asyncio.run(run())

if __name__=='__main__':unittest.main()
