from pydantic import BaseModel
from typing import Optional, Any

class BeaconCheckIn(BaseModel):
    id: str
    data: dict

class TaskCreate(BaseModel):
    command: str
    args: Optional[list] = []

class TaskResponse(BaseModel):
    task_id: str
    output: str
    status: str