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
import plotly.express as px  #5.1.0

## for simple routing
import osmnx as ox  #1.2.2
import networkx as nx  #3.0

## for advanced routing 
from ortools.constraint_solver import pywrapcp  #9.6
from ortools.constraint_solver import routing_enums_pb2

app = Flask(__name__)

def create_map():
    prg_map=folium.Map(location=[50.0869808355617, 14.420696466020118],zoom_start=16)
    folium.Marker([50.08755474796508, 14.423318842912195], icon=folium.Icon(color="green", prefix='fa',icon='bicycle'),).add_to(prg_map)

    return prg_map

@app.route("/")
def show_map():
    nyc_map = create_map()
    # Save the map as HTML file to render it
    map_html = os.path.join('templates', 'map.html')
    nyc_map.save(map_html)
    return render_template('map.html') 



if __name__ == '__main__':  
    app.run()  
