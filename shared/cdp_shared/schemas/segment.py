import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class TimeWindow(BaseModel):
    last_n_days: int | None = None
    from_date: str | None = None
    to_date: str | None = None


class RuleCondition(BaseModel):
    # traits.tier | events.booking_completed.destination | traits.total_spend_vnd
    field: str
    # eq | neq | gt | gte | lt | lte | contains | not_contains | in | not_in | exists | not_exists
    op: str
    value: Any | None = None
    time_window: TimeWindow | None = None


class RuleAST(BaseModel):
    operator: Literal["AND", "OR"] = "AND"
    conditions: list["RuleCondition | RuleAST"] = Field(default_factory=list)


class SegmentCreate(BaseModel):
    name: str
    description: str | None = None
    rules: RuleAST
    refresh_mode: Literal["scheduled", "realtime"] = "scheduled"
    refresh_cron: str | None = "0 2 * * *"


class SegmentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    rules: RuleAST | None = None
    refresh_mode: str | None = None
    refresh_cron: str | None = None


class SegmentOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    rules: dict
    refresh_mode: str
    refresh_cron: str | None
    member_count: int
    last_computed: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
