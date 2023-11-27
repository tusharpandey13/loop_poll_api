from fastapi import APIRouter
import redis

from app.model.PollRequest import PollRequest
from app.services.report_orchestrator_service import trigger_report_generation
from app.utils.common_utils import generate_report_id

from app.config import settings

redis_connection_pool = redis.ConnectionPool(
    host = settings.redis_host, 
    port = settings.redis_port, 
    password = settings.redis_password
)

router = APIRouter(
    prefix="",
    tags=["report"],
)

@router.get("/trigger_report", description="Trigger report generation")
async def trigger_report():
    report_id = generate_report_id()
    trigger_report_generation(redis_connection_pool, report_id)
    return {"report_id": report_id}


@router.post("/get_report", description="Return the status of the report")
async def get_report(poll_request: PollRequest):
    redis_connection = redis.Redis(connection_pool=redis_connection_pool)
    return redis_connection.hgetall(poll_request.report_id)