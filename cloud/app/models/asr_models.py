from pydantic import BaseModel


class UploadResponse(BaseModel):
    task_id: str
    status: str = "pending"


class TranscriptResponse(BaseModel):
    task_id: str
    transcript: str
    status: str


class SummaryResponse(BaseModel):
    task_id: str
    summary: dict
    status: str
