from fastapi import APIRouter

router = APIRouter(
    prefix="/echo",
    tags=["echo"],
)

@router.get("/{message}")
async def echo(message: str):
    return {"message": message}