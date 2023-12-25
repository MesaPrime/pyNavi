import asyncio
import json
from authlib.integrations.httpx_client import AsyncOAuth2Client
from playwright.async_api import Playwright, Page, Locator, async_playwright
import aiofiles


async def getOSMToken() -> str:
    """
    使用asyncio.createTask(Security.getOSMToken)创建任务
    OSMToken保存在module/osmToken.json文件内
    :return: osmToken
    """

    # 导入module/osmAuthSecret.json文件内的osm OAuth2 信息
    with open(r'../module/osmAuthSecret.json', 'r') as file:
        data = json.loads(file.read())
        client_id = data['client_id']
        client_secret = data['client_secret']
        scope = data['scope']
        userAgent = 'PyNavi/0.1'
        redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'

    client = AsyncOAuth2Client(
        client_id,
        client_secret,
        scope=scope,
        redirect_uri=redirect_uri,
        headers={'User-Agent': userAgent})
    # generate authorization URL and state (save it for later)
    uri, state = client.create_authorization_url('https://www.openstreetmap.org/oauth2/authorize')

    async with async_playwright() as play:
        browser = await play.chromium.launch(headless=True, channel='chrome')
        try:
            context = await browser.new_context(storage_state=r'../module/osmStorage.json')  # 尝试导入会话避免反复登录
        except FileNotFoundError:
            context = await browser.new_context()
        page = await context.new_page()
        await page.goto(uri)
        await page.locator(
            '#content > div.content-body > div > div> div:nth-child(1) > form > input.btn.btn-primary').click(
            timeout=300000)
        token = await page.locator('#authorization_code').inner_html()
        await context.storage_state(path=r'../module/osmStorage.json')
        await context.close()

        async with aiofiles.open(r'../module/osmToken.json', 'w') as tokenFile:
            await tokenFile.write(json.dumps({'token': token}))
        return token


if __name__ == '__main__':
    asyncio.run(getOSMToken())
