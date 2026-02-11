# src/model/route.py
from __future__ import annotations

from datetime import date, time
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


LngLat = tuple[float, float]  # (lng, lat)


class RouteRequest(BaseModel):
    origin: str = Field(..., min_length=1)
    destination: str = Field(..., min_length=1)
    origin_coords: LngLat
    destination_coords: LngLat
    trip_date: date
    trip_time: time

    @field_validator("origin_coords", "destination_coords", mode="before")
    @classmethod
    def parse_coords(cls, v: Any) -> LngLat:
        # accetta "lng,lat" oppure [lng, lat] o (lng, lat)
        if isinstance(v, str):
            parts = [p.strip() for p in v.split(",")]
            if len(parts) != 2:
                raise ValueError("coords must be 'lng,lat'")
            return (float(parts[0]), float(parts[1]))
        if isinstance(v, (list, tuple)) and len(v) == 2:
            return (float(v[0]), float(v[1]))
        raise ValueError("invalid coords format")


class StopInfo(BaseModel):
    # i dict arrivano dal dataframe -> permettiamo extra
    model_config = ConfigDict(extra="allow")


class RoutePayload(BaseModel):
    origin: str
    destination: str
    origin_coords: LngLat
    destination_coords: LngLat
    start_stop: StopInfo
    end_stop: StopInfo
    distance: str | None = None
    duration: str | None = None
    shapes_geojson: dict[str, Any]
    stops_geojson: dict[str, Any]
    waypoints: list[Any] = Field(default_factory=list)


class RouteResponse(BaseModel):
    status: Literal["success"] = "success"
    route: RoutePayload
