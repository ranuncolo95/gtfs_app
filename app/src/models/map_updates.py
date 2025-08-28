from app.src.models.defs import get_stop_destinazione
from fastapi import Request, HTTPException
import urllib.parse
from pymongo.mongo_client import MongoClient
from pymongo import ASCENDING
from pymongo.server_api import ServerApi
import pandas as pd
import geopandas as gpd
import json
from shapely.geometry import LineString
from datetime import datetime, timedelta
from fastapi import Request
from fastapi.templating import Jinja2Templates


templates = Jinja2Templates(directory="./app/view/templates")

# MongoDB Atlas Configuration
username = urllib.parse.quote_plus("guest")
password = urllib.parse.quote_plus("guest")
cluster_url = "cluster0.dzcyoux.mongodb.net"

# MongoDB URI with additional connection parameters for better performance
uri = f"mongodb+srv://{username}:{password}@{cluster_url}/?retryWrites=true&w=majority"

client = MongoClient(uri, server_api=ServerApi('1'), tlsAllowInvalidCertificates=True)
db = client["gtfs"]

async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        # You can pass variables to template here
        "shiny_url": "http://localhost:8001"  
    })


async def calculate_route(request: Request):
    data = await request.json()
    origin = data.get('origin')
    destination = data.get('destination')
    print(origin, destination)
    
    try:
        stops_df = pd.DataFrame(list(db["cagliari_ctm_stops"].find()))
        orario = "16:30:00"

        # trovo lo stop più vicino alla destinazione
        stop_destinazione_df = get_stop_destinazione(destination[1], destination[0], stops_df)

        # prendo in considerazione l'orario
        orario = datetime.strptime(orario, "%H:%M:%S")

        #considero l'intervallo tra il mio arrivo e un ora prima
        orario_earlier = (orario - timedelta(hours=1)).strftime("%H:%M:%S")
        orario = orario.strftime("%H:%M:%S")  # Convert back to string!

        # trovo i trip che comprendono la fermata della destinazione, orario di arrivo più vicina al mio orario
        destinazione = stop_destinazione_df["stop_id"]
        closest_trip_doc = db["cagliari_ctm_stop_times"].find(
            {
                "stop_id": destinazione,
                "arrival_time": {"$gte": orario_earlier, "$lte": orario}
            },
            {
                "_id": 0,
                "trip_id": 1,
                "arrival_time": 1
            }
        ).sort("arrival_time", -1)  # descending order to get closest before or at orario

        # to_df
        closest_trip_df = pd.DataFrame(list(closest_trip_doc))

        # stop times dei trip precedenti
        trip_ids = closest_trip_df["trip_id"].unique().tolist()
        stop_times_cursor = db["cagliari_ctm_stop_times"].find(
            {
                "trip_id": {"$in": trip_ids}},
            {
                "_id": 0,
                "trip_id": 1,
                "arrival_time": 1,
                "departure_time": 1,
                "stop_id": 1,
                "stop_sequence": 1
            }
        ).sort([
            ("trip_id", ASCENDING),
            ("stop_sequence", ASCENDING)
        ])
        df_stop_times_filtered = pd.DataFrame(list(stop_times_cursor))

        # trovare di quei trip quale abbia la fermata più vicina al mio punto di partenza
        stops_viaggio_gr = df_stop_times_filtered[["stop_id", "trip_id","arrival_time", "stop_sequence"]].merge(stops_df[["stop_id", "stop_name", "stop_lat", "stop_lon"]], on="stop_id")
        stop_partenza_df = get_stop_destinazione(origin[1], origin[0], stops_viaggio_gr)
        partenza = stop_partenza_df["stop_id"]

        # trip viaggio finale
        trip_viaggio = stops_viaggio_gr[stops_viaggio_gr["stop_id"] == partenza].sort_values("arrival_time", ascending=False).iloc[0]["trip_id"]

        # stop times viaggio finale
        df_stop_times_viaggio = stops_viaggio_gr[stops_viaggio_gr["trip_id"] == trip_viaggio]
        index_partenza = df_stop_times_viaggio[df_stop_times_viaggio["stop_id"] == partenza].index[0]
        index_destinazione = df_stop_times_viaggio[df_stop_times_viaggio["stop_id"] == destinazione].index[0]
        df_stop_times_viaggio = df_stop_times_viaggio.loc[index_partenza:index_destinazione]

        trips_cursor = db["cagliari_ctm_trips"].find(
                {
                    "trip_id": int(trip_viaggio)  # Direct comparison instead of $in
                },
                {
                    "_id": 0,
                    "route_id": 1,
                    "service_id": 1,
                    "trip_id": 1,
                    "trip_headsign": 1,
                    "direction_id": 1,
                    "shape_id": 1
                }
            )

        df_trips_filtered = pd.DataFrame(list(trips_cursor))

        shape_id = df_trips_filtered.iloc[0]["shape_id"]

        # trovare tutte le shape del percorso
        shapes_cursor = db["cagliari_ctm_shapes"].find(
            {
                "shape_id": shape_id  # Direct comparison instead of $in
            },
            {
                "_id": 0,
                "shape_id": 1,
                "shape_pt_lat": 1,
                "shape_pt_lon": 1,
                "shape_pt_sequence": 1
            }
        ).sort([("shape_pt_sequence", ASCENDING)])

        df_shapes_filtered = pd.DataFrame(list(shapes_cursor))

        lat_partenza = df_stop_times_viaggio.iloc[0]["stop_lat"].round(3)
        lon_partenza = df_stop_times_viaggio.iloc[0]["stop_lon"].round(3)
        shape_sequence_partenza = df_shapes_filtered[(df_shapes_filtered["shape_pt_lat"].round(3) == lat_partenza) & 
                        (df_shapes_filtered["shape_pt_lon"].round(3) == lon_partenza)].iloc[0]["shape_pt_sequence"]

        lat_destinazione = df_stop_times_viaggio.iloc[-1]["stop_lat"].round(3)
        lon_destinazione = df_stop_times_viaggio.iloc[-1]["stop_lon"].round(3)
        shape_sequence_destinazione = df_shapes_filtered[(df_shapes_filtered["shape_pt_lat"].round(3) == lat_destinazione) & 
                        (df_shapes_filtered["shape_pt_lon"].round(3) == lon_destinazione)].iloc[0]["shape_pt_sequence"]

        index_shape_partenza = df_shapes_filtered[df_shapes_filtered["shape_pt_sequence"] == shape_sequence_partenza].index[0]
        index_shape_destinazione = df_shapes_filtered[df_shapes_filtered["shape_pt_sequence"] == shape_sequence_destinazione].index[0]
        df_shapes_filtered = df_shapes_filtered.loc[index_shape_partenza:index_shape_destinazione]

        shapes_gdf = gpd.GeoDataFrame(
            df_shapes_filtered, 
            geometry=gpd.points_from_xy(df_shapes_filtered.shape_pt_lon, df_shapes_filtered.shape_pt_lat), crs="EPSG:4326")
        
        shapes_gdf = shapes_gdf.groupby("shape_id")['geometry'].apply(lambda x: LineString(x.tolist()))
        shapes_gdf = gpd.GeoDataFrame(shapes_gdf, geometry='geometry')

        shapes_geojson = json.loads(shapes_gdf.to_json())

        stops_gdf = gpd.GeoDataFrame(
            df_stop_times_viaggio,
            geometry=gpd.points_from_xy(
                df_stop_times_viaggio.stop_lon, 
                df_stop_times_viaggio.stop_lat
            ), 
            crs="EPSG:4326"
        )
        
        stops_geojson = json.loads(stops_gdf[["stop_id", "stop_name", "geometry"]].to_json())
        
        print(origin)
        
        return {
            "status": "success",
            "route": {
                "origin": origin,
                "destination": destination,
                "start_stop": stop_partenza_df,
                "end_stop": stop_destinazione_df,
                "distance": stop_destinazione_df["distance"],
                "duration": "duration",
                "shapes_geojson": shapes_geojson,
                "stops_geojson": stops_geojson,  # Add stops data
                "waypoints": []      # could include intermediate points
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

