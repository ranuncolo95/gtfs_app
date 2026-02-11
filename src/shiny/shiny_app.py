from shiny import App, ui, reactive
from maplibre import output_maplibregl, render_maplibregl, Map, MapContext
from maplibre.sources import GeoJSONSource
from maplibre.layer import Layer, LayerType


def _empty_feature_collection():
    return {"type": "FeatureCollection", "features": []}


def _point_feature_collection(lng_lat):
    if lng_lat is None:
        return _empty_feature_collection()
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": lng_lat},
                "properties": {},
            }
        ],
    }


def _normalize_lng_lat(value):
    """Accept either [lng, lat] or 'lng,lat' and return [lng, lat] floats."""
    if value is None:
        return None
    if isinstance(value, str):
        parts = [p.strip() for p in value.split(",")]
        if len(parts) == 2:
            return [float(parts[0]), float(parts[1])]
        return None
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return [float(value[0]), float(value[1])]
    return None


app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.script(
            """
        $(document).on('shiny:connected', function() {
            window.addEventListener('message', function(event) {
                if (event.data && event.data.type === "route_update") {
                    Shiny.setInputValue('route_data', event.data.payload, {priority: 'event'});
                }
            });
        });
        """
        )
    ),
    ui.tags.style(
        """
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
    """
    ),
    ui.div(output_maplibregl("maplibre"), id="map-container", class_="container-fluid"),
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

        # Route-related sources (created once)
        m.add_source(source=GeoJSONSource(data=_empty_feature_collection()), id="stops")
        m.add_source(source=GeoJSONSource(data=_empty_feature_collection()), id="shapes")
        m.add_source(source=GeoJSONSource(data=_empty_feature_collection()), id="origin")
        m.add_source(source=GeoJSONSource(data=_empty_feature_collection()), id="destination")

        # Route-related layers (created once)
        m.add_layer(
            Layer(
                id="shapes-layer",
                type=LayerType.LINE,
                source="shapes",
                paint={"line-width": 2, "line-color": "#4285F4"},
            )
        )

        m.add_layer(
            Layer(
                id="stops-layer",
                type=LayerType.CIRCLE,
                source="stops",
                paint={"circle-radius": 3, "circle-color": "#FF5722"},
            )
        )

        m.add_layer(
            Layer(
                id="origin-layer",
                type=LayerType.CIRCLE,
                source="origin",
                paint={"circle-radius": 6, "circle-color": "#2E7D32"},
            )
        )

        m.add_layer(
            Layer(
                id="destination-layer",
                type=LayerType.CIRCLE,
                source="destination",
                paint={"circle-radius": 6, "circle-color": "#C62828"},
            )
        )

        return m

    @reactive.Effect
    @reactive.event(input.route_data)
    def update_map():
        route_data = input.route_data()
        if not route_data:
            return

        async def update_map_async():
            async with MapContext("maplibre") as m:
                # Defensive reads
                stops_fc = route_data.get("stops_geojson") or _empty_feature_collection()
                shapes_fc = route_data.get("shapes_geojson") or _empty_feature_collection()

                origin_ll = _normalize_lng_lat(route_data.get("origin_coords"))
                dest_ll = _normalize_lng_lat(route_data.get("destination_coords"))

                m.set_data(source_id="stops", data=stops_fc)
                m.set_data(source_id="shapes", data=shapes_fc)
                m.set_data(source_id="origin", data=_point_feature_collection(origin_ll))
                m.set_data(source_id="destination", data=_point_feature_collection(dest_ll))

        import asyncio

        asyncio.create_task(update_map_async())


app = App(app_ui, server)
