from typing import Any, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

class MapTilerFeature(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: Literal["Feature"] = "Feature"
    place_name: str
    # center è [lng, lat]; accetta lista/tupla e serializza in JSON come lista
    center: tuple[float, float] = Field(..., description="(lng, lat)")

class MapTilerGeocodeResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: Optional[str] = None
    query: Optional[list[Any]] = None
    features: list[MapTilerFeature] = Field(default_factory=list)
    attribution: Optional[str] = None
