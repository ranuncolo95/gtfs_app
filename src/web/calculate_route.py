# src/web/calculate_route.py
from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import ValidationError
import json

from src.model.route import RouteRequest
from src.service.map_update import calculate_route
from src.error import NotFound, InvalidInput, DataFailure

router = APIRouter()


@router.post("/api/calculate-route", response_class=HTMLResponse)
def calculate_route_endpoint(
    origin: str = Form(...),
    destination: str = Form(...),
    origin_coords: str = Form(...),
    destination_coords: str = Form(...),
    trip_date: str = Form(...),
    trip_time: str = Form(...),
):
    # 1) Web: valida input e crea modello
    try:
        req = RouteRequest(
            origin=origin,
            destination=destination,
            origin_coords=origin_coords,
            destination_coords=destination_coords,
            trip_date=trip_date,
            trip_time=trip_time,
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors()) from e

    # 2) Web: chiama use-case (service) e mappa errori a HTTP
    try:
        result = calculate_route(req)
    except InvalidInput as e:
        raise HTTPException(status_code=400, detail=e.msg) from e
    except NotFound as e:
        raise HTTPException(status_code=404, detail=e.msg) from e
    except DataFailure as e:
        raise HTTPException(status_code=502, detail=e.msg) from e

    # 3) Web: risposta compatibile col tuo frontend (iframe + postMessage)
    payload_json = json.dumps(result.model_dump())

    html_content = f"""
    <html>
        <body>
            <script>
                window.parent.postMessage({{
                    type: "route_response",
                    payload: {payload_json}
                }}, "*");
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)
