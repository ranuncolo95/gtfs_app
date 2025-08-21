from shiny import App, ui, reactive, module
from maplibre import output_maplibregl, render_maplibregl, Map, MapContext
from maplibre.sources import GeoJSONSource
from maplibre.layer import Layer, LayerType
from maplibre.controls import Marker, MarkerOptions, Popup
import urllib.parse
from pymongo.mongo_client import MongoClient
from pymongo import ASCENDING
from pymongo.server_api import ServerApi
import pandas as pd
import geopandas as gpd
import json
from shapely.geometry import Point, Polygon, MultiPoint

# MongoDB Atlas Configuration
username = urllib.parse.quote_plus("guest")
password = urllib.parse.quote_plus("guest")
cluster_url = "cluster0.dzcyoux.mongodb.net"
uri = f"mongodb+srv://{username}:{password}@{cluster_url}/?retryWrites=true&w=majority"

client = MongoClient(uri, server_api=ServerApi('1'))
db = client["gtfs"]

def get_coordinate_bounds(df, lat_col='shape_pt_lat', lon_col='shape_pt_lon'):
    """
    Calculate the convex hull (outer bounds) of coordinates in a DataFrame
    """
    if len(df) == 0:
        return gpd.GeoDataFrame({'geometry': []}, crs='EPSG:4326'), {
            'min_lon': 0, 'min_lat': 0, 'max_lon': 0, 'max_lat': 0,
            'center_lon': 0, 'center_lat': 0
        }
    
    # Create GeoDataFrame from coordinates
    gdf = gpd.GeoDataFrame(
        df[[lon_col, lat_col]],
        geometry=gpd.points_from_xy(df[lon_col], df[lat_col]), 
        crs="EPSG:4326"
    )
    
    # Calculate convex hull using MultiPoint
    combined_geometry = MultiPoint(gdf.geometry.tolist())
    convex_hull = combined_geometry.convex_hull
    
    # Get bounds
    bounds = convex_hull.bounds
    
    bounds_dict = {
        'min_lon': bounds[0],
        'min_lat': bounds[1],
        'max_lon': bounds[2],
        'max_lat': bounds[3],
        'center_lon': (bounds[0] + bounds[2]) / 2,
        'center_lat': (bounds[1] + bounds[3]) / 2
    }
    
    # Create GeoDataFrame for the hull
    hull_gdf = gpd.GeoDataFrame({'geometry': [convex_hull]}, crs='EPSG:4326')
    
    return hull_gdf, bounds_dict


import numpy as np
from shapely.geometry import Polygon

def get_simple_bounds(df, lat_col, lon_col, padding=0.0001):
    """Fallback to simple bounding box"""
    min_lon, max_lon = df[lon_col].min(), df[lon_col].max()
    min_lat, max_lat = df[lat_col].min(), df[lat_col].max()
    
    bbox_polygon = Polygon([
        [min_lon - padding, min_lat - padding],
        [max_lon + padding, min_lat - padding],
        [max_lon + padding, max_lat + padding],
        [min_lon - padding, max_lat + padding],
        [min_lon - padding, min_lat - padding]
    ])
    
    bounds_dict = {
        'min_lon': min_lon - padding,
        'min_lat': min_lat - padding,
        'max_lon': max_lon + padding,
        'max_lat': max_lat + padding,
        'center_lon': (min_lon + max_lon) / 2,
        'center_lat': (min_lat + max_lat) / 2
    }
    
    hull_gdf = gpd.GeoDataFrame({'geometry': [bbox_polygon]}, crs='EPSG:4326')
    return hull_gdf, bounds_dict


app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.script("""
        $(document).on('shiny:connected', function() {
            window.addEventListener('message', function(event) {
                if (event.data && event.data.type === "route_update") {
                    Shiny.setInputValue('route_data', event.data.payload, {priority: 'event'});
                }
            });
        });
        """)
    ),
    ui.tags.style("""
        html, body, .container-fluid, #map-container {
            height: 100vh;
            margin: 0;
            padding: 0;
            width: 100vw;
        }
        #maplibre {
            height: 100vh !important;
            width: 100vw !important;
        }
    """),
    ui.div(
        output_maplibregl("maplibre"),
        id="map-container",
        style="height: 100vh; width: 100vw;"
    )
)


def server(input, output, session):
    @render_maplibregl
    def maplibre():
        m = Map(center=[9.12, 39.22], zoom=12)
        
        df_shapes = pd.DataFrame(list(db["cagliari_ctm_shapes"].find()))
        
        if len(df_shapes) > 0:
            print(f"Data shape: {df_shapes.shape}")
            
            try:
                # Try granular boundaries first
                hull_gdf, bounds = get_coordinate_bounds(
                    df_shapes, 
                    lat_intervals=80,  # More intervals = more granular
                    padding=0.0002     # Adjust padding as needed
                )
                print("Using granular boundaries method")
                
            except Exception as e:
                print(f"All methods failed: {e}")
                # Final fallback
                hull_gdf, bounds = get_simple_bounds(df_shapes)
                print("Using simple bounding box")
            
            # Convert to GeoJSON and add to map
            hull_geojson = json.loads(hull_gdf.to_json())
            
            m.add_source("hull-source", {
                "type": "geojson",
                "data": hull_geojson
            })
            
            hull_fill_layer = Layer(
                id="hull-fill-layer",
                type=LayerType.FILL,
                source="hull-source",
                paint={
                    "fill-color": "#007cbf",
                    "fill-opacity": 0.3,
                    "fill-outline-color": "#005a8f"
                }
            )
            
            m.add_layer(hull_fill_layer)
            
            # Fit map to bounds
            m.fit_bounds([
                [bounds['min_lon'], bounds['min_lat']],
                [bounds['max_lon'], bounds['max_lat']]
            ])
        
        return m

app = App(app_ui, server)

if __name__ == "__main__":
    app.run()