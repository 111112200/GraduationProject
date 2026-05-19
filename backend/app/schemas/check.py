from pydantic import BaseModel
from typing import List, Optional


class CreateCheckTaskRequest(BaseModel):
    name: str
    experimentId: int
    mode: str = "BOTH"  # IN_CLASS, HISTORY_ONLY, BOTH
    reportIds: List[int]
    highRiskThreshold: float = 0.8
    similarThreshold: float = 0.5
