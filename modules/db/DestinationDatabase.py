import sqlite3
from typing import Optional, Literal
from functools import wraps
from pydantic import BaseModel
from pathlib import Path


class DestinationData(BaseModel):
    name: str
    destinationType: str
    lat: float  # 纬度
    lon: float  # 经度
    comment: Optional[str] = None
    note: Optional[str] = None


class DestinationDataWithID(DestinationData):
    id: int


class DestinationDatabase:
    writeFunctions = dict()

    def __init__(self, path: Path | str | None = None, debugMode: bool = False):
        self.debugMode = debugMode
        if debugMode:
            self.path = r":memory:"
        else:
            if isinstance(path, Path):
                self.path = path.absolute()
            elif isinstance(path, str):
                self.path = path
            else:
                self.path = r"./dataStorage/destination.db"

    def __enter__(self):
        self.database = sqlite3.connect(self.path)
        self.cursor = self.database.cursor()
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS destination(id integer primary key autoincrement, \n"
            "            username TEXT, \n"
            "            destinationType TEXT, \n"
            "            lat INTEGER, \n"
            "            lon INTEGER, \n"
            "            comment TEXT, \n"
            "            note TEXT)")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        self.database.commit()
        self.database.close()

    def __getitem__(self, dataID) -> DestinationDataWithID:
        destinationData = self.cursor.execute("SELECT * FROM destination WHERE id IS ?", (dataID,)).fetchone()
        data = {key: value for key, value in
                zip(("id", "name", "destination", "lat", "lon", "comment"), destinationData)}
        return DestinationDataWithID(**data)

    def register(cls, func):
        cls.writeFunctions[func.__name__] = func

        @wraps(func)
        def warp(*args, **kwargs):
            return func(*args, **kwargs)

        return warp

    @staticmethod
    def error(*args, **kwargs):
        return "write mode unsupported"

    def write(self, mode: Literal["insert", "update", "delete"], **kwargs):
        return self.writeFunctions.get(mode)(**kwargs)

    def insert(self, data: DestinationData) -> dict:
        """
        插入数据库
        :param data: ("name", "destinationType", "lat", "lon", "comment", "note")
        :return:
        """
        try:
            self.cursor.execute(
                'INSERT INTO destination("name", "destinationType", "lat", "lon", "comment", "note") values(?,?,?,?,?,?)',
                (data.name, data.destinationType, data.lat, data.lon, data.comment, data.comment))
            return {"msg": "data insert success", "code": 200}
        except sqlite3.ProgrammingError as error:
            return {"msg": str(error), "code": 402}

    def update(self, data: tuple | DestinationDataWithID | dict):
        """
        更新数据库
        :param data:(dataID, param: Literal["name", "destinationType", "lat", "lon", "comment", "note"], newData)
        :return:
        """
        if isinstance(data, tuple):
            dataID, param, newData = data
            try:
                self.cursor.execute(f"UPDATE destination SET {param}='{str(newData)}' WHERE id='{dataID}'")
                return "data update success"
            except sqlite3.ProgrammingError as error:
                return str(error)

        elif isinstance(data, DestinationDataWithID):
            dataID = data.id
            self.cursor.execute(f"""
            """)
            self.cursor.execute(
                f"""DELETE FROM destination WHERE id='{dataID}' 
                INSERT INTO destination("name", "destinationType", "lat", "lon", "comment", "note") 
                values(?,?,?,?,?,?)""",
                (data.name, data.destinationType, data.lat, data.lon, data.comment, data.comment))

        elif isinstance(data, dict):
            dataID = data['id']
            param = data['param']
            newData = data['newData']
            try:
                self.cursor.execute(f"UPDATE destination SET {param}='{str(newData)}' WHERE id='{dataID}'")
                return "data update success"
            except sqlite3.ProgrammingError as error:
                return str(error)

    def delete(self, dataID):
        """
        删除数据
        :param dataID:
        :return:
        """
        try:
            self.cursor.execute(f"""DELETE FROM destination WHERE id='{dataID}'""")
            return f"{dataID} data deleted"
        except sqlite3.ProgrammingError as error:
            return str(error)

    def selectAll(self) -> list:
        return self.cursor.execute("SELECT * FROM destination").fetchall()


if __name__ == '__main__':
    pass
