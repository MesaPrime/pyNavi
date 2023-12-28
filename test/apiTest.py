import httpx
import playwright.async_api
import xmltodict
import asyncio
import json
from authlib.integrations.httpx_client import AsyncOAuth2Client
from playwright.async_api import Playwright, Page, Locator, async_playwright
import aiofiles

pytest_plugins = ('pytest_asyncio',)
# with open(r'../module/osmAuth.json') as file:
#     headerFromFile = json.loads(file.read())
# headers = httpx.Headers({"Authorization": "Basic cTI1Mjg5NTc3QG91dGxvb2suY29tJTNBQm9tYjczNTU2MDg="})

with open(r'../module/osmAuthSecret.json', 'r') as file:
    data = json.loads(file.read())
    client_id = data['client_id']
    client_secret = data['client_secret']
    scope = data['scope']
    userAgent = 'PyNavi/0.1'

# api scopes (see https://wiki.openstreetmap.org/wiki/OAuth)
# scope = 'read_prefs write_api'

# URI to redirect to after successful authorization
# redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
redirect_uri = 'http://127.0.0.1:7777/redirect'


async def getOSMToken(client_id, client_secret, scope, userAgent, redirect_uri):
    client = AsyncOAuth2Client(
        client_id,
        client_secret,
        scope=scope,
        redirect_uri=redirect_uri,
        headers={'User-Agent': userAgent})
    # generate authorization URL and state (save it for later)
    uri, state = client.create_authorization_url('https://www.openstreetmap.org/oauth2/authorize')
    print(uri, state)

    code = httpx.get(uri)

    payload = {'grant_type': 'authorization_code', 'client_id': client_id, 'client_secret': client_secret,
               'code': code, 'redirect_uri': 'http://127.0.0.1:7777/redirect', 'scope': scope}
    token = await client.post('https://www.openstreetmap.org/oauth2/token', data=payload)['access_token']
    print(token)
    # return token

    async with async_playwright() as play:
        browser = await play.chromium.launch(headless=False, channel='chrome')
        try:
            context = await browser.new_context(storage_state=r'../module/osmStorage.json')
        except FileNotFoundError:
            context = await browser.new_context()
        page = await context.new_page()
        await page.goto(uri)
        try:
            await page.locator(
                '#content > div.content-body > div > div> div:nth-child(1) > form > input.btn.btn-primary').click(
                timeout=300000)
        except playwright.async_api.TimeoutError:
            print('get osmToken timeout!')
        token = await page.locator('#authorization_code').inner_html()
        print(token)
        await context.storage_state(path=r'../module/osmStorage.json')
        await page.wait_for_timeout(300)
        await context.close()

        async with aiofiles.open(r'../module/osmToken.json', 'w') as tokenFile:
            await tokenFile.write(json.dumps({'token': token}))
        return token


asyncio.run(getOSMToken(client_id, client_secret, scope, userAgent, redirect_uri))
