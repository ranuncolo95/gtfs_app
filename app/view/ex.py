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


import numpy as np
from shapely.geometry import Polygon

def get_granular_boundaries(df, lat_col='shape_pt_lat', lon_col='shape_pt_lon', 
                           lat_intervals=100, padding=0.0001):
    """
    Create granular boundaries by analyzing latitude intervals
    """
    print(f"Creating granular boundaries for {len(df)} points...")
    
    # Get the latitude range
    min_lat, max_lat = df[lat_col].min(), df[lat_col].max()
    lat_range = max_lat - min_lat
    
    # Create latitude bins
    lat_bins = np.linspace(min_lat, max_lat, lat_intervals + 1)
    
    left_boundaries = []
    right_boundaries = []
    
    # For each latitude interval, find the leftmost and rightmost points
    for i in range(len(lat_bins) - 1):
        lat_low = lat_bins[i]
        lat_high = lat_bins[i + 1]
        
        # Find points in this latitude band
        mask = (df[lat_col] >= lat_low) & (df[lat_col] <= lat_high)
        points_in_band = df[mask]
        
        if len(points_in_band) > 0:
            # Find leftmost (min longitude) and rightmost (max longitude) points
            leftmost_idx = points_in_band[lon_col].idxmin()
            rightmost_idx = points_in_band[lon_col].idxmax()
            
            left_boundaries.append({
                'lat': points_in_band.loc[leftmost_idx, lat_col],
                'lon': points_in_band.loc[leftmost_idx, lon_col] - padding
            })
            
            right_boundaries.append({
                'lat': points_in_band.loc[rightmost_idx, lat_col],
                'lon': points_in_band.loc[rightmost_idx, lon_col] + padding
            })
    
    # If no boundaries found, fall back to simple bounds
    if not left_boundaries or not right_boundaries:
        return get_simple_bounds(df, lat_col, lon_col, padding)
    
    # Sort boundaries by latitude
    left_boundaries.sort(key=lambda x: x['lat'])
    right_boundaries.sort(key=lambda x: x['lat'])
    
    # Create polygon from boundaries
    left_points = [(point['lon'], point['lat']) for point in left_boundaries]
    right_points = [(point['lon'], point['lat']) for point in reversed(right_boundaries)]
    
    polygon_coords = left_points + right_points
    if polygon_coords:
        polygon_coords.append(polygon_coords[0])  # Close the polygon
        
        granular_polygon = Polygon(polygon_coords)
        bounds = granular_polygon.bounds
        
        bounds_dict = {
            'min_lon': bounds[0],
            'min_lat': bounds[1],
            'max_lon': bounds[2],
            'max_lat': bounds[3],
            'center_lon': (bounds[0] + bounds[2]) / 2,
            'center_lat': (bounds[1] + bounds[3]) / 2
        }
        
        hull_gdf = gpd.GeoDataFrame({'geometry': [granular_polygon]}, crs='EPSG:4326')
        return hull_gdf, bounds_dict
    
    return get_simple_bounds(df, lat_col, lon_col, padding)

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


def get_direction_aware_boundaries(df, lat_col='shape_pt_lat', lon_col='shape_pt_lon', 
                                  segments=20, padding=0.0003):
    """
    Create boundaries that follow the route direction by segmenting
    """
    print("Creating direction-aware boundaries...")
    
    if 'shape_pt_sequence' in df.columns:
        df = df.sort_values('shape_pt_sequence')
    
    # Split into segments
    segment_size = len(df) // segments
    boundaries = []
    
    for i in range(0, len(df), segment_size):
        segment = df.iloc[i:i + segment_size]
        
        if len(segment) > 0:
            # For each segment, find bounding box
            seg_min_lon, seg_max_lon = segment[lon_col].min(), segment[lon_col].max()
            seg_min_lat, seg_max_lat = segment[lat_col].min(), segment[lat_col].max()
            
            boundaries.append({
                'min_lon': seg_min_lon - padding,
                'max_lon': seg_max_lon + padding,
                'min_lat': seg_min_lat - padding,
                'max_lat': seg_max_lat + padding,
                'center_lat': (seg_min_lat + seg_max_lat) / 2
            })
    
    # Create a smooth polygon connecting segment boundaries
    if boundaries:
        left_points = []
        right_points = []
        
        for bound in boundaries:
            left_points.append((bound['min_lon'], bound['center_lat']))
            right_points.append((bound['max_lon'], bound['center_lat']))
        
        # Reverse right points for polygon creation
        right_points.reverse()
        
        polygon_coords = left_points + right_points
        if polygon_coords:
            polygon_coords.append(polygon_coords[0])
            
            granular_polygon = Polygon(polygon_coords)
            overall_bounds = granular_polygon.bounds
            
            bounds_dict = {
                'min_lon': overall_bounds[0],
                'min_lat': overall_bounds[1],
                'max_lon': overall_bounds[2],
                'max_lat': overall_bounds[3],
                'center_lon': (overall_bounds[0] + overall_bounds[2]) / 2,
                'center_lat': (overall_bounds[1] + overall_bounds[3]) / 2
            }
            
            hull_gdf = gpd.GeoDataFrame({'geometry': [granular_polygon]}, crs='EPSG:4326')
            return hull_gdf, bounds_dict
    
    return get_simple_bounds(df, lat_col, lon_col, padding)


def server(input, output, session):
    @render_maplibregl
    def maplibre():
        m = Map(center=[9.12, 39.22], zoom=12)
        
        df_shapes = pd.DataFrame(list(db["cagliari_ctm_shapes"].find()))
        
        if len(df_shapes) > 0:
            print(f"Data shape: {df_shapes.shape}")
            
            # Try granular boundaries first
            hull_gdf, bounds = get_granular_boundaries(
                df_shapes, 
                lat_intervals=80,  # More intervals = more granular
                padding=0.0002     # Adjust padding as needed
            )
            
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