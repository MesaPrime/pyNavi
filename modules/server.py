import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from db import DestinationDatabase, UserDatabase
from pathlib import Path
from Security.fastapiToken import get_current_user, Token, loginForToken

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Message(BaseModel):
    msg: str
    code: int
    token: Optional[Token] = None


@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()) -> Message:
    try:
        return Message(msg='create new token', code=200, token=loginForToken(form_data))
    except UserDatabase.UserAuthFailException as fail:
        return Message(msg=fail.message, code=402)


@app.post('/uploadDestination', name='上传目标点数据')
async def uploadTargetData(destinationData: DestinationDatabase.DestinationData,
                           token: str = Depends(login_for_access_token),
                           debugMode: bool = False) -> dict:
    with DestinationDatabase.DestinationDatabase(Path('./dataStorage/destination.db'), debugMode) as db:
        message: dict = db.insert(destinationData)
        return message


if __name__ == '__main__':
    uvicorn.run('server:app', host='0.0.0.0', port=5800)
