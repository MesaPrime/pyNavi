import uvicorn
from fastapi import FastAPI

OAuthApp = FastAPI()


@OAuthApp.get('/redirect')
async def redirect(code, state):
    return {'code': code, 'state': state}


if __name__ == '__main__':
    uvicorn.run('OAuth2API:OAuthApp', host='127.0.0.1', port=7777)
