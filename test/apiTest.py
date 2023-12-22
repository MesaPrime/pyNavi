import httpx
import asyncio
import pytest

pytest_plugins = ('pytest_asyncio',)

headers = {'Authorization': 'Basic q25289577@outlook.com:pass'}


@pytest.mark.asyncio
async def test_asyncHttp():
    async with httpx.AsyncClient(verify=False) as client:
        req = await client.get('https://master.apis.dev.openstreetmap.org.json')
        print(req.json())
