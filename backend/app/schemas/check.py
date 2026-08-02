from pydantic import BaseModel, Field, model_validator
from typing import List


class CreateCheckTaskRequest(BaseModel):
    name: str
    experimentId: int
    mode: str = "BOTH"  # IN_CLASS, HISTORY_ONLY, BOTH
    reportIds: List[int] = Field(min_length=1)
    highRiskThreshold: float = Field(default=0.8, ge=0, le=1)
    similarThreshold: float = Field(default=0.5, ge=0, le=1)

    @model_validator(mode="after")
    def validate_thresholds(self):
        if self.highRiskThreshold < self.similarThreshold:
            raise ValueError("高风险阈值不能低于相似阈值")
        return self
