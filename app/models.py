from datetime import datetime

from pydantic import BaseModel, field_validator

ALLOWED_CATEGORIES = {"bug", "feature_request", "question", "urgent"}
ALLOWED_PRIORITIES = {"P1", "P2", "P3"}
ALLOWED_STATUSES = {"open", "in_progress", "closed"}


class TicketCreate(BaseModel):
    title: str
    description: str

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title must not be blank")
        if len(v) > 200:
            raise ValueError("title must be 200 chars or fewer")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("description must not be blank")
        if len(v) > 5000:
            raise ValueError("description must be 5000 chars or fewer")
        return v


class TicketUpdate(BaseModel):
    status: str | None = None
    priority: str | None = None


class TicketOut(BaseModel):
    id: int
    title: str
    description: str
    category: str
    priority: str
    tags: list[str]
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
