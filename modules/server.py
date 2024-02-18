from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from .db import DestinationDatabase
from pathlib import Path

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post('/uploadDestination', name='上传目标点数据')
async def uploadTargetData(destinationData: DestinationDatabase.DestinationData,token: str, debugMode: bool = False) -> dict:
    with DestinationDatabase.DestinationDatabase(Path('./dataStorage/destination.db'), debugMode) as db:
        message: dict = db.insert(destinationData)
        return message
