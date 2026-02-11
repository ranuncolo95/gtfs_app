from fastapi import APIRouter, Depends, HTTPException, Query

from src.core.deps import get_settings
from src.core.config import Settings
from src.model.geocode import MapTilerGeocodeResponse
from src.service.geocoding_client import MapTilerGeocodingClient, GeocodingError, ProviderError


router = APIRouter()


@router.get("/api/geocode", response_model=MapTilerGeocodeResponse)
async def geocode_endpoint(
    q: str = Query(..., min_length=1, description="Testo da geocodificare"),
    settings: Settings = Depends(get_settings),
):
    # Evita chiamate inutili mentre l’utente sta digitando
    if len(q.strip()) < 3:
        return MapTilerGeocodeResponse(features=[])

    try:
        client = MapTilerGeocodingClient(settings)
        return await client.geocode(q)
    except GeocodingError as e:
        # configurazione mancante (es. key)
        raise HTTPException(status_code=500, detail=str(e)) from e
    except ProviderError as e:
        # provider giù / errore / payload invalido
        status = e.status_code or 502
        raise HTTPException(status_code=status, detail=e.message) from e
