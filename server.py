from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import subprocess
import threading
import uvicorn
import httpx

from math import radians, sin, cos, sqrt, asin
import urllib.parse
from pymongo.mongo_client import MongoClient
from pymongo import ASCENDING
from pymongo.server_api import ServerApi
import pandas as pd
import geopandas as gpd
import json
from shapely.geometry import LineString

# MongoDB Atlas Configuration
username = urllib.parse.quote_plus("root")
password = urllib.parse.quote_plus("root")
cluster_url = "cluster0.dzcyoux.mongodb.net"

# MongoDB URI with additional connection parameters for better performance
uri = f"mongodb+srv://{username}:{password}@{cluster_url}/?retryWrites=true&w=majority"

client = MongoClient(uri, server_api=ServerApi('1'))
db = client["gtfs"]

shiny_process = None
MAPTILER_API_KEY = "OCVJ6l477kLTb0IRr0k5"  # Replace with your key

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start Shiny when FastAPI starts
    def run_shiny():
        global shiny_process
        shiny_process = subprocess.Popen([
            "shiny", "run", 
            "--port", "8001",
            "./shiny_app/app.py"  # Your Shiny app file
        ])
    
    threading.Thread(target=run_shiny, daemon=True).start()
    yield
    # Cleanup on shutdown
    if shiny_process:
        shiny_process.terminate()

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="./app/static"), name="static")
templates = Jinja2Templates(directory="./app/templates")

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        # You can pass variables to template here
        "shiny_url": "http://localhost:8001"  
    })

@app.get("/api/geocode")
async def geocode(q: str):
    """Proxy geocoding requests to MapTiler API"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"https://api.maptiler.com/geocoding/{q}.json",
                params={"key": MAPTILER_API_KEY, "limit": 5}
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/reverse-geocode")
async def reverse_geocode(lng: float, lat: float):
    """Proxy reverse geocoding requests to MapTiler API"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"https://api.maptiler.com/geocoding/{lng},{lat}.json",
                params={"key": MAPTILER_API_KEY}
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=400, detail=str(e))
        

# Add this to server.py after the existing endpoints
@app.post("/api/calculate-route")
async def calculate_route(request: Request):
    data = await request.json()
    origin = data.get('origin')
    destination = data.get('destination')
    
    print(f"Partenza: {origin}, arrivo: {destination}")
    if not origin or not destination:
        raise HTTPException(status_code=400, detail="Missing origin or destination")
    
    try:
        stops_df = pd.DataFrame(list(db["cagliari_ctm_stops"].find()))
        orario = "16:30:00"

        # funzione Haversine distance per calcolare la distanza tra punti geografici
        def haversine_ref_point(row, lat, lon):
            lon1 = lon
            lat1 = lat
            lon2 = row['stop_lon']
            lat2 = row['stop_lat']
            lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
            dlon = lon2 - lon1 
            dlat = lat2 - lat1 
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a)) 
            km = 6367 * c
            return km
        

        def get_stop_destinazione(lat, lon, stops_df):
            stop_destinazione = stops_df[["stop_id", "stop_name", "stop_lat", "stop_lon"]].copy()

            # calcolo la distanza tra dove voglio andare e le fermate, cerco quella più vicina
            stop_destinazione["distance"] = stop_destinazione.apply(lambda row: haversine_ref_point(row, lat, lon), axis=1)
            stop_destinazione = stop_destinazione[stop_destinazione["distance"] == stop_destinazione["distance"].min()]
            return stop_destinazione.iloc[0]


        stop_destinazione_df = get_stop_destinazione(destination[1], destination[0], stops_df)

        from datetime import datetime, timedelta

        # Your target time as datetime object
        orario = datetime.strptime(orario, "%H:%M:%S")

        # Calculate 1 hour before
        orario_earlier = (orario - timedelta(hours=1)).strftime("%H:%M:%S")
        orario = orario.strftime("%H:%M:%S")  # Convert back to string!

        stop_id = stop_destinazione_df["stop_id"]

        closest_trip_doc = db["cagliari_ctm_stop_times"].find(
            {
                "stop_id": stop_id,
                "arrival_time": {"$gte": orario_earlier, "$lte": orario}
            },
            {
                "_id": 0,
                "trip_id": 1,
                "arrival_time": 1
            }
        ).sort("arrival_time", -1)  # descending order to get closest before or at orario

        closest_trip_df = pd.DataFrame(list(closest_trip_doc))

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

        stops_viaggio_gr = df_stop_times_filtered[["stop_id"]].merge(stops_df[["stop_id", "stop_name", "stop_lat", "stop_lon"]], on="stop_id")

        stop_partenza_df = get_stop_destinazione(origin[1], origin[0], stops_viaggio_gr)
        partenza = stop_partenza_df["stop_id"]

        trip_viaggio = df_stop_times_filtered[df_stop_times_filtered["stop_id"] == partenza].sort_values("arrival_time", ascending=False).iloc[0]["trip_id"]

        df_stop_times_viaggio = df_stop_times_filtered[df_stop_times_filtered["trip_id"] == trip_viaggio]

        trip_id = df_stop_times_viaggio.iloc[0]["trip_id"]

        trips_cursor = db["cagliari_ctm_trips"].find(
            {
                "trip_id": int(trip_id)  # Direct comparison instead of $in
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

        # Assuming you have a single trip_id value (not a list)
        shape_id = df_trips_filtered.iloc[0]["shape_id"]

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

        shapes_gdf = gpd.GeoDataFrame(
            df_shapes_filtered, 
            geometry=gpd.points_from_xy(df_shapes_filtered.shape_pt_lon, df_shapes_filtered.shape_pt_lat), crs="EPSG:4326")
        
        shapes_gdf = shapes_gdf.groupby("shape_id")['geometry'].apply(lambda x: LineString(x.tolist()))
        shapes_gdf = gpd.GeoDataFrame(shapes_gdf, geometry='geometry')

        shapes_geojson = json.loads(shapes_gdf.to_json())


        # Create GeoJSON for stops along the route
        stops_along_route = df_stop_times_viaggio.merge(
            stops_df[["stop_id", "stop_name", "stop_lat", "stop_lon"]], 
            on="stop_id"
        )
        
        stops_gdf = gpd.GeoDataFrame(
            stops_along_route,
            geometry=gpd.points_from_xy(
                stops_along_route.stop_lon, 
                stops_along_route.stop_lat
            ), 
            crs="EPSG:4326"
        )
        
        stops_geojson = json.loads(stops_gdf[["stop_id", "stop_name", "geometry"]].to_json())
        
        print(f"Fermata di partenza: {stop_partenza_df['stop_name']}, che dista {round(stop_partenza_df['distance'],2)}km dal tuo punto di partenza.")
        print(f"Fermata di arrivo: {stop_destinazione_df['stop_name']}, che dista {round(stop_destinazione_df['distance'],2)}km dal tuo punto di arrivo.")
        
        return {
            "status": "success",
            "route": {
                "origin": stop_partenza_df["stop_name"],
                "destination": stop_destinazione_df["stop_name"],
                "distance": stop_destinazione_df["distance"],
                "duration": "duration",
                "shapes_geojson": shapes_geojson,
                "stops_geojson": stops_geojson,  # Add stops data
                "waypoints": []      # could include intermediate points
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

if __name__ == "__main__":
    uvicorn.run(app, port=8000)