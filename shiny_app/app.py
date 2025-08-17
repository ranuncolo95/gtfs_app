from shiny import App, ui, reactive, module
from maplibre import output_maplibregl, render_maplibregl, Map, MapContext
import httpx
import json
from maplibre.sources import GeoJSONSource
from maplibre.layer import Layer, LayerType

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
            height: 100%;
            margin: 0;
            padding: 0;
            width: 100vw;
        }
        #maplibre {
            height: 100% !important;
            width: 100% !important;
        }
    """),
    ui.div(
        output_maplibregl("maplibre"),
        id="map-container",
        class_="container-fluid"
    )
)

def server(input, output, session):
    @render_maplibregl
    def maplibre():
        # Initialize map with default view
        return Map(
            container="maplibre",
            center=[9.12, 39.22],
            zoom=12,
        )
    
    @reactive.Effect
    @reactive.event(input.route_data)
    def update_map():
        route_data = input.route_data()
        if not route_data:
            return
        
        async def update_map_async():
            async with MapContext("maplibre") as m:
                # Clear existing sources and layers if they exist
                try:
                    m.remove_layer("stops-layer")
                    m.remove_source("stops")
                except:
                    pass
                
                try:
                    m.remove_layer("shapes-layer")
                    m.remove_source("shapes")
                except:
                    pass
                
                # Add new sources
                stops_source = GeoJSONSource(data=route_data["stops_geojson"])
                shapes_source = GeoJSONSource(data=route_data["shapes_geojson"])

                m.add_source(source=stops_source, id="stops")
                m.add_source(source=shapes_source, id="shapes")
                
                # Add new layers
                stops_layer = Layer(
                    id="stops-layer",
                    type=LayerType.CIRCLE,
                    source="stops",
                    paint={"circle-radius": 3, "circle-color": "#FF5722"}
                )
                m.add_layer(stops_layer)
                
                shapes_layer = Layer(
                    id="shapes-layer",
                    type=LayerType.LINE,
                    source="shapes",
                    paint={"line-width": 2, "line-color": "#4285F4"}
                )
                m.add_layer(shapes_layer)
                
        # Run the async update
        import asyncio
        asyncio.create_task(update_map_async())

app = App(app_ui, server)