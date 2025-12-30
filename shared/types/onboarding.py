from pydantic import BaseModel, Field
from typing import Literal


class CompleteTourRequest(BaseModel):
    tour: str = Field(
        ...,
        description="Identificador del tour (welcome, dashboard, analytics, calls)",
        example="welcome",
    )
    completion_type: Literal["completed", "skipped"] = Field(
        ...,
        description="Indica si el tour fue completado o saltado",
        example="completed",
    )
