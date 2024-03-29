import datetime
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from typing import Dict, Optional, Union
import sys

sys.path.insert(0, '..')
from modules.db import UserDatabase

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "5ebde0c5711987c6be4373b383abccb9a5ab01222163d3d60f8a08f7b87d4e64"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


class User(BaseModel):
    username: str
    email: Optional[str] = None


class ListData(BaseModel):
    payload: list


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def authenticate_user(username: str, password: str):
    with UserDatabase.UserDatabase(debugMode=False) as db:
        user = db[username]
    if not user:
        return False
    else:
        if not verify_password(password, user.hashed_password):
            return False
        else:
            return user


def create_access_token(data: dict, expires_delta: Union[datetime.timedelta, None] = None) -> Token:
    global SECRET_KEY
    global ALGORITHM

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return Token(access_token=encoded_jwt, token_type='bearer')


def get_current_user(token: str = Depends(oauth2_scheme)):
    global SECRET_KEY
    global ALGORITHM

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("username")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    with UserDatabase.UserDatabase(debugMode=False) as db:
        user = db[token_data.username]
    if user is None:
        raise credentials_exception
    return user


def loginForToken(formData: OAuth2PasswordRequestForm = Depends(OAuth2PasswordRequestForm)) -> Token:
    if user := authenticate_user(formData.username, formData.password):
        return create_access_token({'username': user.username})
    else:
        raise UserDatabase.UserAuthFailException
