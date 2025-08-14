from shiny import App, ui
from maplibre import output_maplibregl, render_maplibregl, Map

app_ui = ui.page_fluid(
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
        return Map(center=[9.12, 39.22], zoom=12)

app = App(app_ui, server)