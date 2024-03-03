import json
import sys
from typing import Optional, Any

import aiofiles
import pydantic
import uvicorn

sys.path.append(r'./')

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from starlette import status
from starlette.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Depends
from modules.db import DestinationDatabase, UserDatabase
from modules.Security import fastapiToken, OAuth2API
from modules.api import osmAPI
import httpx

ServerURL = '127.0.0.1:5700'
ServerUploadEndpoint = ServerURL + '/uploadDestination'

OsmAPI = '127.0.0.1:5701'  # PynaviAPI.py
OsmAPIUploadEndpoint = OsmAPI + '/upload'


class Message(BaseModel):
    msg: str
    code: int
    token: Optional[fastapiToken.Token] = None
    data: Any = None


app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
oauthApp = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()) -> fastapiToken.Token:
    try:
        return fastapiToken.loginForToken(form_data)
    except UserDatabase.UserAuthFailException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.get('/pull')
async def pull(token: fastapiToken.Token = Depends(oauth2_scheme)) -> Message:
    async with httpx.AsyncClient(proxy='http://127.0.0.1:7890') as client:
        res: httpx.Response = await client.get('http://127.0.0.1:5800/feedAll',
                                               headers={'Authorization': f'Bearer {token}'})
        resData: Message = Message.model_validate(res.json())

    # create or load changeset
    try:
        async with aiofiles.open(r'./latestChangeset.json', 'r') as file:
            changesetData = json.loads(await file.read())
            changesetID = changesetData['changesetID']
            changeset = osmAPI.CHANGESET(changeSetID=changesetID)
    except FileNotFoundError:
        changeset = osmAPI.CHANGESET()
        changeSetID = await changeset.createChangeSet()
        async with aiofiles.open(r'./latestChangeset.json', 'w') as file:
            await file.write(json.dumps(changeset.json()))

    dataFormatter = ['id', 'name', 'destinationType', 'lat', 'lon', 'comment', 'note']
    for destinationData in resData.data:
        try:
            destinationData = {k: v for k, v in zip(dataFormatter, destinationData)}
            destination: DestinationDatabase.DestinationData = DestinationDatabase.DestinationData.model_validate(
                destinationData)
            match destination.destinationType:
                case 'node':
                    node = osmAPI.NODE(lat=destination.lat, lon=destination.lon,
                                       tags={'place': 'isolated_dwelling', 'name': destination.name})
                    msg: Message = await node.upload(changeset)
                    print(msg)
                case 'way':
                    pass  # todo: upload way
                case 'relation':
                    pass  # todo: upload relation
                case _:
                    print(f'unknown destination type: {destination}')

        except pydantic.ValidationError as error:
            return error
    return Message(msg='all destination uploaded', code=200)


app.mount('/oauth', OAuth2API.OAuthApp)

if __name__ == '__main__':
    uvicorn.run('client:app', port=7777, reload=False)
