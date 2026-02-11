# src/data/gtfs_route.py
from __future__ import annotations

from math import radians, sin, cos, sqrt, asin
from datetime import datetime, timedelta

import pandas as pd
import geopandas as gpd
import json
from shapely.geometry import LineString
from pymongo import ASCENDING

from src.error import NotFound


def haversine_ref_point(row, lat, lon) -> float:
    lon1, lat1, lon2, lat2 = lon, lat, row["stop_lon"], row["stop_lat"]
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return 6367 * c


def get_service_ids_for_date(db, input_date) -> int:
    if isinstance(input_date, str):
        input_date_obj = datetime.strptime(input_date, "%Y-%m-%d")
        date_int = int(input_date_obj.strftime("%Y%m%d"))
    else:
        date_int = int(input_date.strftime("%Y%m%d"))

    cursor = db["cagliari_ctm_calendar"].find(
        {"start_date": {"$lte": date_int}, "end_date": {"$gte": date_int}}
    )
    rows = list(cursor)
    if not rows:
        raise NotFound(f"Nessun service_id attivo per la data {input_date}")
    return rows[0]["service_id"]


def filter_trips_by_service_id(db, trip_ids: list[int], service_id: int) -> list[int]:
    trips = db["cagliari_ctm_trips"].find({"trip_id": {"$in": trip_ids}, "service_id": service_id})
    return [t["trip_id"] for t in trips]


def get_stop_destinazione(lat: float, lon: float, stops_df: pd.DataFrame) -> pd.DataFrame:
    stop_dest = stops_df[["stop_id", "stop_name", "stop_lat", "stop_lon"]].copy()
    stop_dest["distance"] = stop_dest.apply(lambda row: haversine_ref_point(row, lat, lon), axis=1)
    return stop_dest.sort_values(by="distance")


def get_trip_from_stop_id(db, stop_id, service_id: int, orario: str) -> list[int]:
    t = datetime.strptime(orario, "%H:%M")
    orario_earlier = (t - timedelta(hours=1)).strftime("%H:%M")
    orario = t.strftime("%H:%M")

    cursor = db["cagliari_ctm_stop_times"].find(
        {"stop_id": stop_id, "arrival_time": {"$gte": orario_earlier, "$lte": orario}},
        {"_id": 0, "trip_id": 1, "arrival_time": 1, "stop_sequence": 1},
    ).sort("arrival_time", -1)

    df = pd.DataFrame(list(cursor))
    if df.empty:
        raise NotFound("Nessun trip trovato per l'orario selezionato")

    trip_ids = df["trip_id"].unique().tolist()
    valid = filter_trips_by_service_id(db, trip_ids, service_id)
    if not valid:
        raise NotFound("Nessun trip trovato per la data selezionata")
    return valid


def get_first_stop_and_trip_ids(db, valid_trip_ids, origin_coords, stop, stops_df):
    cursor = db["cagliari_ctm_stop_times"].find(
        {"trip_id": {"$in": valid_trip_ids}},
        {"_id": 0, "trip_id": 1, "arrival_time": 1, "departure_time": 1, "stop_id": 1, "stop_sequence": 1},
    ).sort([("trip_id", ASCENDING), ("stop_sequence", ASCENDING)])

    df_stop_times = pd.DataFrame(list(cursor))

    stops_viaggio = df_stop_times[["stop_id", "trip_id", "arrival_time", "stop_sequence"]].merge(
        stops_df[["stop_id", "stop_name", "stop_lat", "stop_lon"]],
        on="stop_id",
    )

    stop_partenza_df = get_stop_destinazione(origin_coords[1], origin_coords[0], stops_viaggio)
    stop_id_partenza = stop_partenza_df["stop_id"].unique()[0]

    a = (
        df_stop_times[
            (df_stop_times["stop_id"] == stop_id_partenza) | (df_stop_times["stop_id"] == stop)
        ]
        .groupby("trip_id")
        .agg(stop_id=("stop_id", lambda x: x))
        .reset_index()
    )

    result = a[a["stop_id"].apply(lambda x: list(x) == [stop_id_partenza, stop] if hasattr(x, "__array__") else False)]
    return stop_id_partenza, result, df_stop_times


def filter_trip_by_time_and_get_final_trip(df_stop_times, stop, trip_date: str, trip_time: str) -> pd.DataFrame:
    trip_datetime_str = f"{trip_date} {trip_time}"
    orario = datetime.strptime(trip_datetime_str, "%Y-%m-%d %H:%M")

    stop_df = df_stop_times[df_stop_times["stop_id"] == stop].copy()
    stop_df["departure_time_dt"] = pd.to_datetime(trip_date + " " + stop_df["departure_time"])

    candidates = stop_df[stop_df["departure_time_dt"] <= orario]
    if candidates.empty:
        raise NotFound("Nessun trip compatibile con data/ora selezionate")

    closest_row = candidates.loc[(orario - candidates["departure_time_dt"]).abs().idxmin()]
    trip = closest_row["trip_id"]
    return df_stop_times[df_stop_times["trip_id"] == trip]


def get_shape(db, df_trip_slice: pd.DataFrame) -> pd.DataFrame:
    trip_id = df_trip_slice["trip_id"].unique()[0]

    trips_cursor = db["cagliari_ctm_trips"].find(
        {"trip_id": int(trip_id)},
        {"_id": 0, "shape_id": 1},
    )
    trips = list(trips_cursor)
    if not trips:
        raise NotFound("Trip non trovato (shape_id mancante)")
    shape_id = trips[0]["shape_id"]

    shapes_cursor = db["cagliari_ctm_shapes"].find(
        {"shape_id": shape_id},
        {"_id": 0, "shape_id": 1, "shape_pt_lat": 1, "shape_pt_lon": 1, "shape_pt_sequence": 1},
    ).sort([("shape_pt_sequence", ASCENDING)])

    df_shapes = pd.DataFrame(list(shapes_cursor))
    if df_shapes.empty:
        raise NotFound("Shape non trovata")

    lat_p = df_trip_slice.iloc[0]["stop_lat"].round(3)
    lon_p = df_trip_slice.iloc[0]["stop_lon"].round(3)
    lat_d = df_trip_slice.iloc[-1]["stop_lat"].round(3)
    lon_d = df_trip_slice.iloc[-1]["stop_lon"].round(3)

    seq_p = df_shapes[(df_shapes["shape_pt_lat"].round(3) == lat_p) & (df_shapes["shape_pt_lon"].round(3) == lon_p)].iloc[0]["shape_pt_sequence"]
    seq_d = df_shapes[(df_shapes["shape_pt_lat"].round(3) == lat_d) & (df_shapes["shape_pt_lon"].round(3) == lon_d)].iloc[0]["shape_pt_sequence"]

    i_p = df_shapes[df_shapes["shape_pt_sequence"] == seq_p].index[0]
    i_d = df_shapes[df_shapes["shape_pt_sequence"] == seq_d].index[0]
    return df_shapes.loc[i_p:i_d]


def calcolo_trip(db, trip_date: str, trip_time: str, origin_coords, destination_coords):
    stops_df = pd.DataFrame(list(db["cagliari_ctm_stops"].find()))
    if stops_df.empty:
        raise NotFound("Stops non disponibili")

    closest_stop_df = get_stop_destinazione(destination_coords[1], destination_coords[0], stops_df)
    service_id = get_service_ids_for_date(db, trip_date)

    result = None
    df_stop_times_filtered = None
    stop_id_partenza = None
    stop = None

    for stop in closest_stop_df["stop_id"]:
        valid_trip_ids = get_trip_from_stop_id(db, stop, service_id, trip_time)
        stop_id_partenza, tmp_result, df_stop_times_filtered = get_first_stop_and_trip_ids(
            db, valid_trip_ids, origin_coords, stop, stops_df
        )
        if tmp_result.values.size:
            result = tmp_result
            break

    if result is None or df_stop_times_filtered is None or stop_id_partenza is None or stop is None:
        raise NotFound("Nessuna rotta trovata verso la destinazione")

    valid_trip_ids = result["trip_id"].unique()
    df_stop_times_filtered = df_stop_times_filtered[df_stop_times_filtered["trip_id"].isin(valid_trip_ids)]

    df_trip = filter_trip_by_time_and_get_final_trip(df_stop_times_filtered, stop, trip_date, trip_time)

    df_trip_gr = df_trip[["stop_id", "trip_id", "arrival_time", "departure_time", "stop_sequence"]].merge(
        stops_df[["stop_id", "stop_name", "stop_lat", "stop_lon"]],
        on="stop_id",
    )

    df_trip_gr["distance_from_start"] = df_trip_gr.apply(
        lambda row: haversine_ref_point(row, origin_coords[1], origin_coords[0]), axis=1
    )
    df_trip_gr["distance_from_destination"] = df_trip_gr.apply(
        lambda row: haversine_ref_point(row, destination_coords[1], destination_coords[0]), axis=1
    )

    index_p = df_trip_gr[df_trip_gr["stop_id"] == stop_id_partenza].index[0]
    index_d = df_trip_gr[df_trip_gr["stop_id"] == stop].index[0]
    df_trip_slice = df_trip_gr.loc[index_p:index_d]

    df_shapes = get_shape(db, df_trip_slice)

    shapes_gdf = gpd.GeoDataFrame(
        df_shapes,
        geometry=gpd.points_from_xy(df_shapes.shape_pt_lon, df_shapes.shape_pt_lat),
        crs="EPSG:4326",
    )
    shapes_line = shapes_gdf.groupby("shape_id")["geometry"].apply(lambda x: LineString(x.tolist()))
    shapes_line = gpd.GeoDataFrame(shapes_line, geometry="geometry")
    shapes_geojson = json.loads(shapes_line.to_json())

    stops_gdf = gpd.GeoDataFrame(
        df_trip_slice,
        geometry=gpd.points_from_xy(df_trip_slice.stop_lon, df_trip_slice.stop_lat),
        crs="EPSG:4326",
    )
    stops_geojson = json.loads(stops_gdf[["stop_id", "stop_name", "geometry"]].to_json())

    return shapes_geojson, stops_geojson, df_trip_slice
