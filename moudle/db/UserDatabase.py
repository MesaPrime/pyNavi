import sqlite3
from typing import Optional, Literal
from functools import wraps
from pydantic import BaseModel


class UserInDB(BaseModel):
    id: Optional[int] = None
    username: str
    hashed_password: str
    email: Optional[str] = None


class UserDatabase:
    writeFunctions = dict()

    def __init__(self, path: Optional[str] = None, debugMode: bool = False):
        self.debugMode = debugMode
        if debugMode:
            self.path = r":memory:"
        else:
            if path is not None:
                self.path = path
            else:
                self.path = r"./user.db"

    def __enter__(self):
        self.database = sqlite3.connect(self.path)
        self.cursor = self.database.cursor()
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS user(id integer primary key autoincrement, \n"
            "            username str, \n"
            "            hashed_password str, \n"
            "            email str)")

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        self.database.commit()
        self.database.close()

    def __getitem__(self, username) -> UserInDB:
        userData = self.cursor.execute("SELECT * FROM user WHERE username IS ?", (username,)).fetchone()
        data = {key: value for key, value in zip(("id", "username", "hashed_password", "email"), userData)}
        return UserInDB(**data)

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

    def insert(self, data: tuple):
        """
        插入数据库
        :param data: (username, passwordhash, email)
        :return:
        """
        try:
            self.cursor.execute("INSERT INTO user('username', 'hashed_password', 'email') values(?,?,?)", data)
            return "data insert success"
        except sqlite3.ProgrammingError as error:
            return str(error)

    def update(self, data: tuple):
        """
        更新数据库
        :param data:(username, param: Literal["username", "passwordhash","email"], newData)
        :return:
        """
        username, param, newData = data
        try:
            self.cursor.execute(f"UPDATE user SET {param}='{str(newData)}' WHERE username='{username}'")
            return "data update success"
        except sqlite3.ProgrammingError as error:
            return str(error)

    def delete(self, username):
        """
        删除数据
        :param username:
        :return:
        """
        try:
            self.cursor.execute(f"""DELETE FROM user WHERE username='{username}'""")
            return f"{username} data deleted"
        except sqlite3.ProgrammingError as error:
            return str(error)


if __name__ == '__main__':
    pass