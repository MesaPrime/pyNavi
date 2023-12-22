import httpx
import asyncio
import pytest
import xmltodict
import json

pytest_plugins = ('pytest_asyncio',)
with open(r'../moudle/osmAuth.json') as file:
    headerFromFile = json.loads(file.read())
headers = httpx.Headers(headerFromFile)


@pytest.mark.asyncio
async def asyncHttp_test():
    async with httpx.AsyncClient() as client:
        req = await client.get('https://master.apis.dev.openstreetmap.org/api/capabilities.json', headers=headers)
        print(req.json())


asyncio.run(asyncHttp_test())
