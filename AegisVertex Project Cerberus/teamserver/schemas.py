from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TeamCreate(BaseModel):
    name: str
    description: Optional[str] = None

class TeamRead(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class BeaconCreate(BaseModel):
    team_id: int
    name: str

class BeaconRead(BaseModel):
    id: int
    team_id: int
    name: str
    last_seen: datetime
    active: bool
    model_config = ConfigDict(from_attributes=True)