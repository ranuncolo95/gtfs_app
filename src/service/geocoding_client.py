from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

import httpx
from pydantic import ValidationError

from src.core.config import Settings
from src.model.geocode import MapTilerGeocodeResponse


@dataclass
class GeocodingError(Exception):
    message: str


@dataclass
class ProviderError(GeocodingError):
    status_code: int | None = None


class MapTilerGeocodingClient:
    """
    Client minimale per MapTiler Geocoding API.
    Ritorna sempre un MapTilerGeocodeResponse validato.
    """

    def __init__(self, settings: Settings):
        self._api_key = settings.maptiler_api_key
        self._limit = settings.maptiler_geocode_limit
        self._timeout_s = settings.maptiler_timeout_s

        if not self._api_key:
            # meglio fallire subito: se preferisci, puoi alzare questo solo quando chiamato
            raise GeocodingError("MAPTILER_API_KEY non configurata (setta MAPTILER_API_KEY nel .env).")

    async def geocode(self, query: str) -> MapTilerGeocodeResponse:
        q = query.strip()
        if not q:
            return MapTilerGeocodeResponse(features=[])

        encoded = quote(q, safe="")
        url = f"https://api.maptiler.com/geocoding/{encoded}.json"

        timeout = httpx.Timeout(self._timeout_s, connect=min(2.0, self._timeout_s))

        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                resp = await client.get(
                    url,
                    params={"key": self._api_key, "limit": self._limit},
                    headers={"Accept": "application/json"},
                )
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise ProviderError(
                    message="Errore dal provider di geocoding (MapTiler).",
                    status_code=e.response.status_code,
                ) from e
            except httpx.RequestError as e:
                raise ProviderError(
                    message="Impossibile contattare il provider di geocoding (MapTiler).",
                    status_code=None,
                ) from e

        data = resp.json()
        try:
            return MapTilerGeocodeResponse.model_validate(data)
        except ValidationError as e:
            raise ProviderError(
                message="Risposta del provider non valida rispetto al contratto atteso.",
                status_code=502,
            ) from e
