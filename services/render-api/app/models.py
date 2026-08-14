from pydantic import BaseModel, Field


class RenderRequest(BaseModel):
    mass: float = Field(gt=0)
    field_of_view: float = Field(gt=0)
