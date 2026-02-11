# src/service/map_update.py
from __future__ import annotations

from src.data.map_update import calculate_route_data
from src.model.route import RouteRequest, RouteResponse, RoutePayload, StopInfo


def calculate_route(req: RouteRequest) -> RouteResponse:
    shapes_geojson, stops_geojson, start_stop, end_stop = calculate_route_data(
        trip_date=req.trip_date.isoformat(),
        trip_time=req.trip_time.strftime("%H:%M"),
        origin_coords=req.origin_coords,
        destination_coords=req.destination_coords,
    )

    payload = RoutePayload(
        origin=req.origin,
        destination=req.destination,
        origin_coords=req.origin_coords,
        destination_coords=req.destination_coords,
        start_stop=StopInfo.model_validate(start_stop),
        end_stop=StopInfo.model_validate(end_stop),
        distance="distance",   # TODO: calcolo reale
        duration="duration",   # TODO: calcolo reale
        shapes_geojson=shapes_geojson,
        stops_geojson=stops_geojson,
        waypoints=[],
    )
    return RouteResponse(route=payload)
