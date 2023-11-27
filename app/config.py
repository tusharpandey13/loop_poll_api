import os
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    redis_host: str = Field(..., env='REDIS_HOST')
    redis_password: str = Field(..., env='REDIS_PASSWORD')
    redis_port: str = Field(..., env='REDIS_PORT')

settings = Settings()
