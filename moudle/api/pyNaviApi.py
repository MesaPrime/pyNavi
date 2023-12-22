from fastapi import FastAPI, Depends
from ..Security.token import create_access_token, get_current_user

pyNaviApp = FastAPI()

headers = {'Authorization': 'Basic q25289577@outlook.com:869613109'}

@pyNaviApp.post('/upload', dependencies=[Depends(get_current_user)])
async def upload(lat, long, name):
    pass