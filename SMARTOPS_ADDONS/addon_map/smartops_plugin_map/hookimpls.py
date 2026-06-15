import pluggy
hookimpl = pluggy.HookimplMarker("smartops")

class MapPlugin:
    """
    Plugin de cartographie pour SMARTOPS.
    Affiche les sites clients et les tickets sur OpenStreetMap.
    """
    @hookimpl
    def register_menu_items(self):
        return [{
            "label": "Carte Interactive",
            "url": "/app/map/",
            "icon": "la-map-marked-alt"
        }]

plugin_implementation = MapPlugin()
