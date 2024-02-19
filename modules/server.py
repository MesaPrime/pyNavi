from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional

from starlette import status

from .db import DestinationDatabase, UserDatabase
from pathlib import Path
from .Security.fastapiToken import get_current_user, Token

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/token")
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends()
) -> Token:
    with UserDatabase.UserDatabase() as userDatabase:
        user = userDatabase[username]

    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.post('/uploadDestination', name='上传目标点数据')
async def uploadTargetData(destinationData: DestinationDatabase.DestinationData,
                           token: str = Depends(get_current_user()),
                           debugMode: bool = False) -> dict:
    with DestinationDatabase.DestinationDatabase(Path('./dataStorage/destination.db'), debugMode) as db:
        message: dict = db.insert(destinationData)
        return message
