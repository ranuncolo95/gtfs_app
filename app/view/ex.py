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
        # Initialize map with default view
        m = Map(
            container="maplibre",
            center=[9.12, 39.22],
            zoom=12,
        )
        
        # Get data from MongoDB
        df_shapes = pd.DataFrame(list(db["cagliari_ctm_shapes"].find()))
        
        if len(df_shapes) > 0:
            # Calculate hull and bounds
            hull_gdf, bounds = get_coordinate_bounds(df_shapes)
            
            # Convert to GeoJSON
            hull_geojson = json.loads(hull_gdf.to_json())
            
            # DEBUG: Print bounds and geojson structure
            print(f"Bounds: {bounds}")
            print(f"GeoJSON type: {hull_geojson['type']}")
            print(f"Number of features: {len(hull_geojson['features'])}")
            
            # Add source first
            m.add_source("hull-source", {
                "type": "geojson",
                "data": hull_geojson
            })
            
            # Add hull fill layer
            hull_fill_layer = Layer(
                id="hull-fill-layer",
                type=LayerType.FILL,
                source="hull-source",
                paint={
                    "fill-color": "#007cbf",
                    "fill-opacity": 0.5,
                    "fill-outline-color": "#005a8f"
                }
            )
            
            # Add hull line layer for better visibility
            hull_line_layer = Layer(
                id="hull-line-layer",
                type=LayerType.LINE,
                source="hull-source",
                paint={
                    "line-color": "#005a8f",
                    "line-width": 3,
                    "line-opacity": 0.8
                }
            )
            
            m.add_layer(hull_fill_layer)
            m.add_layer(hull_line_layer)
            
            # Also add the original points for reference
            points_data = [
                {"lng": row['shape_pt_lon'], "lat": row['shape_pt_lat']} 
                for _, row in df_shapes.iterrows()
            ]
            
            m.add_source("points-source", points_data)
            
            points_layer = Layer(
                id="points-layer",
                type=LayerType.CIRCLE,
                source="points-source",
                paint={
                    "circle-radius": 3,
                    "circle-color": "#ff0000",
                    "circle-stroke-width": 1,
                    "circle-stroke-color": "#ffffff"
                }
            )
            
            m.add_layer(points_layer)
            
            # Fit map to bounds
            m.fit_bounds([
                [bounds['min_lon'], bounds['min_lat']],
                [bounds['max_lon'], bounds['max_lat']]
            ])
        
        return m

app = App(app_ui, server)

if __name__ == "__main__":
    app.run()