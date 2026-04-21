from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class Beacon(SQLModel, table=True):
    id: str = Field(primary_key=True)
    hostname: str
    username: str
    os: str
    ip: str
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)

    tasks: List["Task"] = Relationship(back_populates="beacon")


class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    beacon_id: str = Field(foreign_key="beacon.id")
    command: str
    args: Optional[str] = None
    status: str = Field(default="pending")
    result: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    beacon: Beacon = Relationship(back_populates="tasks")