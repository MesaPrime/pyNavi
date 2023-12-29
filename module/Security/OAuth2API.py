import json
from authlib.integrations.httpx_client import AsyncOAuth2Client
import aiofiles
import httpx
import uvicorn
from fastapi import FastAPI

OAuthApp = FastAPI()


@OAuthApp.get('/getAccessToken')
async def getOSMToken():
    async with aiofiles.open(r'../osmAuthSecret.json') as file:
        osmSecret = json.loads(await file.read())
        client_id = osmSecret['client_id']
        client_secret = osmSecret['client_secret']
        scope = osmSecret['scope']
        redirect_uri = 'http://127.0.0.1:7777/redirect'
        userAgent = 'PyNavi/0.1'

    client = AsyncOAuth2Client(
        client_id,
        client_secret,
        scope=scope,
        redirect_uri=redirect_uri,
        headers={'User-Agent': userAgent})
    # generate authorization URL and state (save it for later)
    uri, state = client.create_authorization_url('https://www.openstreetmap.org/oauth2/authorize')
    print(uri, state)

    async with aiofiles.open(r'../osmCookies.json', 'r') as file:
        cookies = json.loads(await file.read())

    async with httpx.AsyncClient(cookies=cookies, follow_redirects=True) as client:
        osmAccessTokenResponse = await client.get(uri)  # get code via uri
    return osmAccessTokenResponse.json()


@OAuthApp.get('/redirect')
async def redirect(code, state):
    async with aiofiles.open(r'../osmAuthSecret.json') as file:
        osmSecret = json.loads(await file.read())
        client_id = osmSecret['client_id']
        client_secret = osmSecret['client_secret']
        scope = osmSecret['scope']

    # request codeVerifier
    payload = {'client_id': client_id,
               'client_secret': client_secret,
               'scope': scope,
               'grant_type': 'authorization_code',
               'code': code,
               'redirect_uri': 'http://127.0.0.1:7777/redirect'}

    async with httpx.AsyncClient() as client:
        accessTokenResponse = await client.post('https://www.openstreetmap.org/oauth2/token',
                                                data=payload)

    async with aiofiles.open(r'../osmAccessToken.json', 'w') as file:
        await file.write(json.dumps(accessTokenResponse.json()))
    return accessTokenResponse.json()


if __name__ == '__main__':
    uvicorn.run('OAuth2API:OAuthApp', host='127.0.0.1', port=7777)
