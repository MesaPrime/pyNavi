import uvicorn
from fastapi import FastAPI, Depends
from moudle.Security.token import get_current_user

pyNaviApp = FastAPI()

headers = {'Authorization': 'Basic q25289577@outlook.com:pass'}


@pyNaviApp.post('/upload', dependencies=[Depends(get_current_user)])
async def upload(lat, long, name):
    pass

if __name__ == "__main__":

    uvicorn.run(
        "pyNaviApi:pyNaviApp",
        host="0.0.0.0",
        reload=False,
        port=8002
    )