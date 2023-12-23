import httpx
import asyncio
import pytest
import xmltodict
import json
from authlib.integrations.httpx_client import AsyncOAuth2Client
from playwright.async_api import Playwright, Page, Locator, async_playwright

pytest_plugins = ('pytest_asyncio',)
with open(r'../moudle/osmAuth.json') as file:
    headerFromFile = json.loads(file.read())
headers = httpx.Headers({"Authorization": "Basic cTI1Mjg5NTc3QG91dGxvb2suY29tJTNBQm9tYjczNTU2MDg="})

with open(r'../moudle/osmToken.json', 'r') as file:
    data = json.loads(file.read())
    client_id = data['client_id']
    client_secret = data['client_secret']
    scope = data['scope']
    userAgent = 'PyNavi/0.1'

# api scopes (see https://wiki.openstreetmap.org/wiki/OAuth)
scope = 'read_prefs write_api'

# URI to redirect to after successful authorization
redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'


async def getOSMToken(client_id, client_secret, scope, userAgent):
    # client = AsyncOAuth2Client(
    #     client_id,
    #     client_secret,
    #     scope=scope,
    #     redirect_uri=redirect_uri,
    #     headers={'User-Agent': userAgent})
    # # generate authorization URL and state (save it for later)
    # uri, state = client.create_authorization_url('https://www.openstreetmap.org/oauth2/authorize')
    # print(uri, state)

    async with async_playwright() as play:
        browser = await play.chromium.launch(headless=False,channel='chrome')
        page = await browser.new_page()
        await page.goto('https://www.openstreetmap.org/oauth2/authorize?response_type=code&client_id=8IaGIedbHRrxUYUvF55_tisxUXQQglStUGq48PT1c8s&redirect_uri=urn%3Aietf%3Awg%3Aoauth%3A2.0%3Aoob&scope=read_prefs+write_api&state=qI4DgmL7zUY3eopu7CXHO5rPSMTQrA')
        await page.locator(
            '#content > div.content-body > div > div > div:nth-child(1) > form > input.btn.btn-primary').click()
        token = await page.locator('#authorization_code').inner_html()
        print(token)
        return token

asyncio.run(getOSMToken(client_id,client_secret,scope,userAgent))

