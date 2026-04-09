from typing import Literal

from pydantic import BaseModel


class EvaluationAiProcessingPublic(BaseModel):
    evaluation_id: int
    transcript_segment_count: int
    has_analysis: bool
    status: Literal["pending", "transcript_only", "complete"]
    user_message_es: str
    hint: str
