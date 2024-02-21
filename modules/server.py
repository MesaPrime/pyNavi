import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional

from starlette import status

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
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    try:
        return loginForToken(form_data)
    except UserDatabase.UserAuthFailException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.post('/uploadDestination', name='上传目标点数据')
async def uploadTargetData(destinationData: DestinationDatabase.DestinationData,
                           token: Token = Depends(oauth2_scheme),
                           debugMode: bool = False) -> dict:
    with DestinationDatabase.DestinationDatabase('./dataStorage/destination.db', debugMode) as db:
        message: dict = db.insert(destinationData)
        return message


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=5800)
