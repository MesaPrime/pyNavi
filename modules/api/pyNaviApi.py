import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from starlette import status
from modules.Security.fastapiToken import get_current_user
from modules.db import DestinationDatabase
from modules.api import osmAPI
from modules.server import Message
import httpx

pyNaviApp = FastAPI()

headers = {'Authorization': 'Basic q25289577@outlook.com:pass'}


@pyNaviApp.post('/upload', dependencies=[Depends(get_current_user)])
async def upload(destination: DestinationDatabase.DestinationData):
    changeSetID: str = await osmAPI.CHANGESET().createChangeSet()
    match destination.destinationType:
        case 'node':
            data = osmAPI.NODE(lat=destination.lat,
                               lon=destination.lon,
                               text=destination.name)
            try:
                msg: Message = await data.upload(changeSetID)
                return msg
            except httpx.TimeoutException:
                raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT, detail='提交至osm服务器连接超时')
        case 'way':
            pass
        case 'relation':
            pass


@pyNaviApp.post('/createNode')
async def createNode(lat, lon, changeset: None | str = None, **kwargs) -> Message:
    node = osmAPI.NODE(lat=lat, lon=lon, **kwargs)
    if changeset is not None:
        msg = await node.upload(changeset)
    else:
        changeset = await osmAPI.CHANGESET().createChangeSet()
        msg = await node.upload(changeset)

    return msg


if __name__ == "__main__":
    uvicorn.run(
        "pyNaviApi:pyNaviApp",
        host="0.0.0.0",
        reload=False,
        port=5701
    )
