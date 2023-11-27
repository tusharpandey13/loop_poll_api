from fastapi import FastAPI
from .routers import echo, poll_main

app = FastAPI()

app.include_router(echo.router)
app.include_router(poll_main.router)