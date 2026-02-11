# src/data/map_update.py
from __future__ import annotations

import os
import urllib.parse
from functools import lru_cache

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from src.data.gtfs_route import calcolo_trip
from src.error import DataFailure, NotFound


@lru_cache
def _get_db():
    # didattico: fallback ai guest, ma meglio passare da Settings/env
    uri = os.getenv("MONGO_URI")
    if not uri:
        username = urllib.parse.quote_plus(os.getenv("MONGO_USER", "guest"))
        password = urllib.parse.quote_plus(os.getenv("MONGO_PASS", "guest"))
        cluster_url = os.getenv("MONGO_CLUSTER", "cluster0.dzcyoux.mongodb.net")
        uri = f"mongodb+srv://{username}:{password}@{cluster_url}/?retryWrites=true&w=majority"

    client = MongoClient(uri, server_api=ServerApi("1"), tlsAllowInvalidCertificates=True)
    db_name = os.getenv("MONGO_DB", "gtfs")
    return client[db_name]


def calculate_route_data(*, trip_date: str, trip_time: str, origin_coords, destination_coords):
    """
    Data layer: ritorna dati 'grezzi' (geojson + stop start/end) senza FastAPI.
    """
    db = _get_db()
    try:
        shapes_geojson, stops_geojson, df_trip_slice = calcolo_trip(
            db, trip_date, trip_time, origin_coords, destination_coords
        )
        start_stop = df_trip_slice.iloc[0].to_dict()
        end_stop = df_trip_slice.iloc[-1].to_dict()
        return shapes_geojson, stops_geojson, start_stop, end_stop
    except NotFound:
        raise
    except Exception as e:
        # qualsiasi errore tecnico resta "tecnico"
        raise DataFailure("Errore tecnico nel calcolo rotta") from e
