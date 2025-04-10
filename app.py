from flask import Flask, render_template
from branca.element import Figure
import os

## for data
import pandas as pd  #1.1.5
import numpy as np  #1.21.0

## for plotting
import matplotlib.pyplot as plt  #3.3.2
import seaborn as sns  #0.11.1
import folium  #0.14.0
from folium import plugins
from folium.plugins import LocateControl, MarkerCluster
import plotly.express as px  #5.1.0

## for simple routing
import osmnx as ox  #1.2.2
import networkx as nx  #3.0

## for advanced routing 
from ortools.constraint_solver import pywrapcp  #9.6
from ortools.constraint_solver import routing_enums_pb2

app = Flask(__name__)

def create_map():
    # prg_map=folium.Map(location=[50.0869808355617, 14.420696466020118],zoom_start=16)
    prg_map=folium.Map(location=[50.10757904960116, 14.420951629813585],zoom_start=16)

    responsive_script = """
    <script>
        // Get the map container
        var map = document.querySelector('.folium-map');
        
        // Function to adjust zoom based on screen width
        function adjustZoom() {
            var mapObj = document.querySelector('.folium-map')._leaflet_map;
            if (window.innerWidth < 768) {
                // Mobile view - set zoom to a lower level
                mapObj.setZoom(12);
            } else {
                // Desktop view - use original zoom
                mapObj.setZoom(16);
            }
        }
        
        // Add a listener for map load event
        if (map._leaflet_map) {
            adjustZoom();
        } else {
            map.addEventListener('leaflet.map.init', function() {
                // Run after the map is initialized
                setTimeout(adjustZoom, 100);
            });
        }
        
        // Adjust zoom when window is resized
        window.addEventListener('resize', adjustZoom);
    </script>
    """

    prg_map.get_root().html.add_child(folium.Element(responsive_script))
    
    marker_cluster = MarkerCluster().add_to(prg_map)
    # folium.Marker([50.08755474796508, 14.423318842912195], icon=folium.Icon(color="red", prefix='fa',icon='bicycle'),).add_to(marker_cluster)
    # folium.Marker([50.090322944037986, 14.42162471740614], icon=folium.Icon(color="red", prefix='fa',icon='heart'),).add_to(marker_cluster)
    # folium.Marker([50.08441631969368, 14.428302542337063], icon=folium.Icon(color="red", prefix='fa',icon='phone'),).add_to(marker_cluster)
    # folium.Marker([50.081328739825466, 14.41321606932961], icon=folium.Icon(color="red", prefix='fa',icon='masks-theater'),).add_to(marker_cluster)
    folium.Marker([50.10544963658487, 14.427315231276873],
                   popup=folium.Popup('Planetarium', max_width=300),
                   icon=folium.Icon(color="red", prefix='fa',icon='bicycle'),).add_to(marker_cluster)
    folium.Marker([50.10831045673811, 14.424126005952495],
                   popup=folium.Popup('Playground', max_width=300),
                   icon=folium.Icon(color="red", prefix='fa',icon='heart'),).add_to(marker_cluster)
    folium.Marker([50.10965658330681, 14.420232509911955],
                   popup=folium.Popup('Tenis', max_width=300),
                   icon=folium.Icon(color="red", prefix='fa',icon='phone'),).add_to(marker_cluster)
    folium.Marker([50.110355321102915, 14.413503010582618],
                   popup=folium.Popup('Waterfall', max_width=300),
                   icon=folium.Icon(color="red", prefix='fa',icon='masks-theater'),).add_to(marker_cluster)
    folium.Marker([50.10812548984484, 14.412958241589292],
                   popup=folium.Popup('Bench', max_width=300),
                   icon=folium.Icon(color="red", prefix='fa',icon='bicycle'),).add_to(marker_cluster)
    folium.Marker([50.106058787595565, 14.410833563743788],
                   popup=folium.Popup('Turnik', max_width=300),
                   icon=folium.Icon(color="red", prefix='fa',icon='heart'),).add_to(marker_cluster)
    folium.Marker([50.105211210875616, 14.415743779890281],
                   popup=folium.Popup('Restaurant', max_width=300),
                   icon=folium.Icon(color="red", prefix='fa',icon='phone'),).add_to(marker_cluster)
    LocateControl(auto_start=False).add_to(prg_map)



    return prg_map

@app.route("/")
def show_map():
    nyc_map = create_map()
    # Save the map as HTML file to render it
    map_html = os.path.join('templates', 'map.html')
    nyc_map.save(map_html)
    return render_template('map.html') 



if __name__ == '__main__':
    app.run(debug=True)
