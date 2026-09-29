import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class IcpRules(BaseModel):
    industries: list[str] = []
    countries: list[str] = []
    states: list[str] = []
    employee_min: int | None = Field(default=None, ge=0)
    employee_max: int | None = Field(default=None, ge=0)
    min_years_in_business: int | None = Field(default=None, ge=0, le=200)
    tech_include: list[str] = []
    weights: dict[str, int] = {}

    @model_validator(mode="after")
    def check_range(self):
        if (
            self.employee_min is not None
            and self.employee_max is not None
            and self.employee_min > self.employee_max
        ):
            raise ValueError("employee_min can't be bigger than employee_max")
        return self


class IcpProfileIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    mode: Literal["sales", "acquisition"] = "sales"
    rules: IcpRules = IcpRules()


class IcpProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    mode: str
    is_active: bool
    rules: dict
    created_at: datetime
    updated_at: datetime


class ActivateOut(BaseModel):
    profile: IcpProfileOut
    rescored: int
