import uvicorn
from fastapi import FastAPI, Depends
from module.Security.fastapiToken import get_current_user
from osmAPI import NODE, ELEMENT, Relation, createChangeSet

pyNaviApp = FastAPI()

headers = {'Authorization': 'Basic q25289577@outlook.com:pass'}


@pyNaviApp.post('/upload', dependencies=[Depends(get_current_user)])
async def upload(lat, long, name):
    pass


@pyNaviApp.post('/createNode')
async def createNode(lat, lon, changeset: None | str = None, **kwargs) -> dict:
    node = NODE(lat=lat, lon=lon, **kwargs)
    if changeset is not None:
        msg = await node.upload(changeset)
    else:
        changeset = await createChangeSet()
        msg = await node.upload(changeset)

    return msg


if __name__ == "__main__":
    uvicorn.run(
        "pyNaviApi:pyNaviApp",
        host="0.0.0.0",
        reload=False,
        port=8002
    )
