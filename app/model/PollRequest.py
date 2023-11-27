from pydantic import BaseModel
class PollRequest(BaseModel):
    report_id: str