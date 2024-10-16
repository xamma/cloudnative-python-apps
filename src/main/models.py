from pydantic_settings import BaseSettings
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List

"""
Configuration class for the app.
Precendences:
1. ENV Vars
2. .env File
3. Default Vars
"""

class AppSettings(BaseSettings):
    api_port: int | None = 8000
    secret_key: str | None = "R4nd00mSecretStr1ng!"
    mongo_host: str | None = "localhost"
    mongo_user: str | None = None
    mongo_password: str | None = None
    mongo_port: int | None = 27017
    mongo_db_name: str | None = "back2lifedb"
    mongo_usercoll_name: str | None = "b2lusercoll"

    class Config:
        env_file = ".env"

class User(BaseModel):
    username: str | None = None
    avatar: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    admin:bool | None = None
    age: int | None = None
    achievements: List[str] | None = None
    gender: str | None = None
    password: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
