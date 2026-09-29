import uuid
from typing import Literal

from pydantic import BaseModel, Field, model_validator

Stage = Literal["new", "qualified", "contacted", "disqualified"]


class LeadUpdate(BaseModel):
    stage: Stage | None = None
    notes: str | None = Field(default=None, max_length=5000)


class BulkAction(BaseModel):
    ids: list[uuid.UUID] = Field(min_length=1, max_length=1000)
    action: Literal["set_stage", "re_enrich", "delete"]
    value: Stage | None = None

    @model_validator(mode="after")
    def stage_needs_value(self):
        if self.action == "set_stage" and not self.value:
            raise ValueError("set_stage needs a value")
        return self


class BulkResult(BaseModel):
    action: str
    affected: int
