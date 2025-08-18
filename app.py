import folium
import math
import itertools
from flask import Flask, render_template, request, jsonify
from folium.plugins import MarkerCluster
from folium.plugins import LocateControl
import os

app = Flask(__name__)

class RouteOptimizer:
    def __init__(self):
        self.points = []
        
    def add_point(self, lat, lon, name, icon='bicycle'):
        """Add a point to the route calculation"""
        self.points.append({
            'lat': lat,
            'lon': lon,
            'name': name,
            'icon': icon
        })
    
    def calculate_distance(self, point1, point2):
        """Calculate distance between two points using Haversine formula"""
        lat1, lon1 = math.radians(point1['lat']), math.radians(point1['lon'])
        lat2, lon2 = math.radians(point2['lat']), math.radians(point2['lon'])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # Earth's radius in kilometers
        
        return r * c
    
    def calculate_route_distance(self, route_indices, return_to_start=True):
        """Calculate total distance for a given route"""
        if len(route_indices) < 2:
            return 0
        
        total_distance = 0
        for i in range(len(route_indices) - 1):
            current_point = self.points[route_indices[i]]
            next_point = self.points[route_indices[i + 1]]
            total_distance += self.calculate_distance(current_point, next_point)
        
        # Add distance back to start only if specified
        if return_to_start and len(route_indices) > 2:
            last_point = self.points[route_indices[-1]]
            first_point = self.points[route_indices[0]]
            total_distance += self.calculate_distance(last_point, first_point)
        
        return total_distance
    
    def find_shortest_route_with_endpoints(self, start_idx=None, end_idx=None):
        """Find shortest route with specified start and end points"""
        if len(self.points) < 2:
            return [], 0
        
        # If no start/end specified, use TSP (circular route)
        if start_idx is None and end_idx is None:
            return self.nearest_neighbor_tsp_circular()
        
        # Create list of intermediate points (excluding start and end)
        intermediate_points = []
        for i in range(len(self.points)):
            if i != start_idx and i != end_idx:
                intermediate_points.append(i)
        
        if not intermediate_points:
            # Only start and end points
            if start_idx is not None and end_idx is not None:
                return [start_idx, end_idx], self.calculate_route_distance([start_idx, end_idx], False)
            else:
                return [start_idx or end_idx], 0
        
        # Find best order for intermediate points
        best_route = None
        best_distance = float('inf')
        
        # For small number of intermediate points, use brute force
        if len(intermediate_points) <= 8:
            for perm in itertools.permutations(intermediate_points):
                route = []
                if start_idx is not None:
                    route.append(start_idx)
                route.extend(perm)
                if end_idx is not None:
                    route.append(end_idx)
                
                distance = self.calculate_route_distance(route, False)
                if distance < best_distance:
                    best_distance = distance
                    best_route = route
        else:
            # Use nearest neighbor for larger sets
            route = []
            if start_idx is not None:
                route.append(start_idx)
            
            # Find nearest neighbor path through intermediate points
            unvisited = intermediate_points[:]
            current_idx = start_idx if start_idx is not None else unvisited[0]
            
            if start_idx is None:
                route.append(current_idx)
                unvisited.remove(current_idx)
            
            while unvisited:
                current_point = self.points[current_idx]
                nearest_idx = min(unvisited, 
                                key=lambda x: self.calculate_distance(current_point, self.points[x]))
                route.append(nearest_idx)
                unvisited.remove(nearest_idx)
                current_idx = nearest_idx
            
            if end_idx is not None:
                route.append(end_idx)
            
            best_route = route
            best_distance = self.calculate_route_distance(route, False)
        
        return best_route, best_distance
    
    def nearest_neighbor_tsp_circular(self):
        """Solve circular TSP using nearest neighbor heuristic"""
        if len(self.points) <= 1:
            return list(range(len(self.points))), 0
        
        unvisited = list(range(1, len(self.points)))
        route = [0]  # Start with first point
        
        while unvisited:
            current_idx = route[-1]
            current_point = self.points[current_idx]
            
            nearest_idx = min(unvisited, 
                            key=lambda x: self.calculate_distance(current_point, self.points[x]))
            
            route.append(nearest_idx)
            unvisited.remove(nearest_idx)
        
        total_distance = self.calculate_route_distance(route, True)
        return route, total_distance

# Global optimizer instance
optimizer = RouteOptimizer()

def initialize_points():
    """Initialize the points data"""
    global optimizer
    optimizer = RouteOptimizer()
    
    points_data = [
        (50.10544963658487, 14.427315231276873, 'Planetarium', 'bicycle'),
        (50.10831045673811, 14.424126005952495, 'Playground', 'heart'),
        (50.10965658330681, 14.420232509911955, 'Tenis', 'phone'),
        (50.110355321102915, 14.413503010582618, 'Waterfall', 'masks-theater'),
        (50.10812548984484, 14.412958241589292, 'Bench', 'bicycle'),
        (50.106058787595565, 14.410833563743788, 'Turnik', 'heart'),
        (50.105211210875616, 14.415743779890281, 'Restaurant', 'phone'),
    ]
    
    for lat, lon, name, icon in points_data:
        optimizer.add_point(lat, lon, name, icon)

def create_base_map():
    """Create base folium map without route"""
    initialize_points()
    
    # Calculate center point
    center_lat = sum(p['lat'] for p in optimizer.points) / len(optimizer.points)
    center_lon = sum(p['lon'] for p in optimizer.points) / len(optimizer.points)
    
    prg_map = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=15,
        tiles='OpenStreetMap'
    )
    
    # Add responsive script and controls
    responsive_script = """
    <style>
    .folium-map {
        width: 100% !important;
        height: 100% !important;
    }
    .route-controls {
        position: fixed;
        top: 10px;
        right: 10px;
        background: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        z-index: 1000;
        min-width: 250px;
    }
    .control-group {
        margin-bottom: 10px;
    }
    .control-group label {
        display: block;
        margin-bottom: 5px;
        font-weight: bold;
    }
    .control-group select {
        width: 100%;
        padding: 5px;
        border: 1px solid #ccc;
        border-radius: 4px;
    }
    .calculate-btn {
        width: 100%;
        padding: 10px;
        background: #007cff;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-weight: bold;
    }
    .calculate-btn:hover {
        background: #0056b3;
    }
    .route-info {
        margin-top: 10px;
        padding: 10px;
        background: #f8f9fa;
        border-radius: 4px;
        display: none;
    }
    </style>
    
    <div class="route-controls">
        <h4 style="margin-top: 0;">Route Calculator</h4>
        
        <div class="control-group">
            <label for="start-point">Start Point:</label>
            <select id="start-point">
                <option value="">No specific start</option>
            </select>
        </div>
        
        <div class="control-group">
            <label for="end-point">End Point:</label>
            <select id="end-point">
                <option value="">No specific end</option>
            </select>
        </div>
        
        <button class="calculate-btn" onclick="calculateRoute()">Calculate Route</button>
        <button class="calculate-btn" onclick="clearRoute()" style="background: #6c757d; margin-top: 5px;">Clear Route</button>
        
        <div id="route-info" class="route-info">
            <div id="route-details"></div>
        </div>
    </div>
    
    <script>
    let currentRouteLayer = null;
    let map = null;
    
    // Wait for folium map to be fully loaded
    function waitForMap() {
        return new Promise((resolve) => {
            function checkMap() {
                // Try multiple ways to access the map
                const mapDiv = document.querySelector('.folium-map div[id^="map"]');
                if (mapDiv && window[mapDiv.id]) {
                    map = window[mapDiv.id];
                    resolve(map);
                } else {
                    setTimeout(checkMap, 100);
                }
            }
            checkMap();
        });
    }
    
    // Initialize when page loads
    window.addEventListener('load', async function() {
        await waitForMap();
        populateDropdowns();
    });
    
    function populateDropdowns() {
        // Get points from server
        fetch('/get-points')
        .then(response => response.json())
        .then(points => {
            const startSelect = document.getElementById('start-point');
            const endSelect = document.getElementById('end-point');
            
            // Clear existing options (except first)
            startSelect.innerHTML = '<option value="">No specific start</option>';
            endSelect.innerHTML = '<option value="">No specific end</option>';
            
            points.forEach((point) => {
                const option1 = new Option(point.name, point.index);
                const option2 = new Option(point.name, point.index);
                startSelect.add(option1);
                endSelect.add(option2);
            });
        })
        .catch(error => console.error('Error loading points:', error));
    }
    
    function calculateRoute() {
        if (!map) {
            alert('Map not ready yet, please try again in a moment');
            return;
        }
        
        const startIdx = document.getElementById('start-point').value;
        const endIdx = document.getElementById('end-point').value;
        
        // Prepare request data
        const requestData = {
            start_idx: startIdx === '' ? null : parseInt(startIdx),
            end_idx: endIdx === '' ? null : parseInt(endIdx)
        };
        
        // Show loading
        const btn = document.querySelector('.calculate-btn');
        btn.textContent = 'Calculating...';
        btn.disabled = true;
        
        // Make request to calculate route
        fetch('/calculate-route', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        })
        .then(response => response.json())
        .then(data => {
            displayRoute(data);
            btn.textContent = 'Calculate Route';
            btn.disabled = false;
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error calculating route: ' + error.message);
            btn.textContent = 'Calculate Route';
            btn.disabled = false;
        });
    }
    
    function displayRoute(routeData) {
        if (!map) {
            console.error('Map not available');
            return;
        }
        
        // Remove previous route if exists
        if (currentRouteLayer) {
            map.removeLayer(currentRouteLayer);
            currentRouteLayer = null;
        }
        
        if (routeData.route_coordinates && routeData.route_coordinates.length > 1) {
            // Create route polyline
            currentRouteLayer = L.polyline(routeData.route_coordinates, {
                color: '#007cff',
                weight: 5,
                opacity: 0.8,
                dashArray: '10, 5'
            });
            
            // Add to map
            currentRouteLayer.addTo(map);
            
            // Add popup to route line
            currentRouteLayer.bindPopup(`
                <b>Optimized Route</b><br>
                Distance: ${routeData.total_distance.toFixed(2)} km<br>
                Stops: ${routeData.num_stops}
            `);
            
            // Show route information in control panel
            const routeInfo = document.getElementById('route-info');
            const routeDetails = document.getElementById('route-details');
            
            let routeText = `<strong>Distance:</strong> ${routeData.total_distance.toFixed(2)} km<br>`;
            routeText += `<strong>Stops:</strong> ${routeData.num_stops}<br>`;
            routeText += `<strong>Type:</strong> ${routeData.is_circular ? 'Circular' : 'Point-to-Point'}<br><br>`;
            routeText += '<strong>Route Order:</strong><br>';
            
            routeData.route_order.forEach((stop, index) => {
                routeText += `${index + 1}. ${stop.name}<br>`;
            });
            
            routeDetails.innerHTML = routeText;
            routeInfo.style.display = 'block';
            
            // Fit map to show entire route
            const group = new L.featureGroup([currentRouteLayer]);
            map.fitBounds(group.getBounds().pad(0.1));
        } else {
            document.getElementById('route-info').style.display = 'none';
        }
    }
    
    function clearRoute() {
        if (currentRouteLayer && map) {
            map.removeLayer(currentRouteLayer);
            currentRouteLayer = null;
        }
        document.getElementById('route-info').style.display = 'none';
        
        // Reset dropdowns
        document.getElementById('start-point').value = '';
        document.getElementById('end-point').value = '';
    }
    </script>
    """
    
    prg_map.get_root().html.add_child(folium.Element(responsive_script))
    
    # Create marker cluster
    marker_cluster = MarkerCluster().add_to(prg_map)
    
    # Add all markers without initial route
    for i, point in enumerate(optimizer.points):
        folium.Marker(
            [point['lat'], point['lon']],
            popup=folium.Popup(f"<b>{point['name']}</b><br>Point #{i+1}", max_width=300),
            icon=folium.Icon(color="red", prefix='fa', icon=point['icon'])
        ).add_to(marker_cluster)
    
    # Add locate control
    LocateControl(auto_start=False).add_to(prg_map)
    
    return prg_map

@app.route("/")
def show_map():
    """Display the interactive map"""
    prg_map = create_base_map()
    
    # Save the map as HTML file to render it
    map_html = os.path.join('templates', 'map.html')
    prg_map.save(map_html)
    
    return render_template('map.html')

@app.route("/calculate-route", methods=['POST'])
def calculate_route():
    """API endpoint to calculate route with specified start/end points"""
    data = request.get_json()
    start_idx = data.get('start_idx')
    end_idx = data.get('end_idx')
    
    # Convert None strings to actual None
    if start_idx == 'null' or start_idx == '':
        start_idx = None
    if end_idx == 'null' or end_idx == '':
        end_idx = None
    
    initialize_points()  # Refresh points
    
    route_indices, total_distance = optimizer.find_shortest_route_with_endpoints(start_idx, end_idx)
    
    # Prepare route coordinates for the map
    route_coordinates = []
    for idx in route_indices:
        point = optimizer.points[idx]
        route_coordinates.append([point['lat'], point['lon']])
    
    # If it's a circular route (no specific start/end), close the loop
    if start_idx is None and end_idx is None and len(route_coordinates) > 2:
        route_coordinates.append(route_coordinates[0])
    
    route_info = {
        'total_distance': total_distance,
        'num_stops': len(route_indices),
        'route_order': [
            {
                'name': optimizer.points[idx]['name'],
                'lat': optimizer.points[idx]['lat'],
                'lon': optimizer.points[idx]['lon']
            }
            for idx in route_indices
        ],
        'route_coordinates': route_coordinates,
        'is_circular': start_idx is None and end_idx is None
    }
    
    return jsonify(route_info)

@app.route("/get-points")
def get_points():
    """Get all available points for dropdown population"""
    initialize_points()
    
    points_list = [
        {
            'index': i,
            'name': point['name'],
            'lat': point['lat'],
            'lon': point['lon']
        }
        for i, point in enumerate(optimizer.points)
    ]
    
    return jsonify(points_list)

# Enhanced RouteOptimizer methods for start/end point functionality
def find_shortest_route_with_endpoints(self, start_idx=None, end_idx=None):
    """Find shortest route with specified start and end points"""
    if len(self.points) < 2:
        return [], 0
    
    # Validate indices
    if start_idx is not None and (start_idx < 0 or start_idx >= len(self.points)):
        start_idx = None
    if end_idx is not None and (end_idx < 0 or end_idx >= len(self.points)):
        end_idx = None
    
    # If start and end are the same, treat as circular route
    if start_idx == end_idx:
        start_idx = None
        end_idx = None
    
    # Case 1: Circular route (no specific start/end)
    if start_idx is None and end_idx is None:
        return self.nearest_neighbor_tsp_circular()
    
    # Case 2: Only start point specified
    if start_idx is not None and end_idx is None:
        return self.find_route_from_start(start_idx)
    
    # Case 3: Only end point specified
    if start_idx is None and end_idx is not None:
        return self.find_route_to_end(end_idx)
    
    # Case 4: Both start and end specified
    return self.find_route_start_to_end(start_idx, end_idx)

def find_route_from_start(self, start_idx):
    """Find route starting from specific point"""
    unvisited = [i for i in range(len(self.points)) if i != start_idx]
    route = [start_idx]
    
    current_idx = start_idx
    while unvisited:
        current_point = self.points[current_idx]
        nearest_idx = min(unvisited, 
                        key=lambda x: self.calculate_distance(current_point, self.points[x]))
        route.append(nearest_idx)
        unvisited.remove(nearest_idx)
        current_idx = nearest_idx
    
    total_distance = self.calculate_route_distance(route, False)
    return route, total_distance

def find_route_to_end(self, end_idx):
    """Find route ending at specific point"""
    # Start from point that's farthest from end, then work backwards
    other_points = [i for i in range(len(self.points)) if i != end_idx]
    
    if not other_points:
        return [end_idx], 0
    
    # Find starting point (farthest from end)
    end_point = self.points[end_idx]
    start_idx = max(other_points, 
                   key=lambda x: self.calculate_distance(self.points[x], end_point))
    
    # Build route from start to end
    unvisited = [i for i in other_points if i != start_idx]
    route = [start_idx]
    
    current_idx = start_idx
    while unvisited:
        current_point = self.points[current_idx]
        nearest_idx = min(unvisited, 
                        key=lambda x: self.calculate_distance(current_point, self.points[x]))
        route.append(nearest_idx)
        unvisited.remove(nearest_idx)
        current_idx = nearest_idx
    
    route.append(end_idx)
    total_distance = self.calculate_route_distance(route, False)
    return route, total_distance

def find_route_start_to_end(self, start_idx, end_idx):
    """Find shortest route from start to end point"""
    intermediate_points = [i for i in range(len(self.points)) 
                          if i != start_idx and i != end_idx]
    
    if not intermediate_points:
        route = [start_idx, end_idx]
        distance = self.calculate_route_distance(route, False)
        return route, distance
    
    best_route = None
    best_distance = float('inf')
    
    # For small sets, try all permutations of intermediate points
    if len(intermediate_points) <= 8:
        for perm in itertools.permutations(intermediate_points):
            route = [start_idx] + list(perm) + [end_idx]
            distance = self.calculate_route_distance(route, False)
            
            if distance < best_distance:
                best_distance = distance
                best_route = route
    else:
        # Use nearest neighbor heuristic for larger sets
        route = [start_idx]
        unvisited = intermediate_points[:]
        current_idx = start_idx
        
        while unvisited:
            current_point = self.points[current_idx]
            nearest_idx = min(unvisited, 
                            key=lambda x: self.calculate_distance(current_point, self.points[x]))
            route.append(nearest_idx)
            unvisited.remove(nearest_idx)
            current_idx = nearest_idx
        
        route.append(end_idx)
        best_route = route
        best_distance = self.calculate_route_distance(route, False)
    
    return best_route, best_distance

# Add methods to RouteOptimizer class
RouteOptimizer.find_shortest_route_with_endpoints = find_shortest_route_with_endpoints
RouteOptimizer.find_route_from_start = find_route_from_start
RouteOptimizer.find_route_to_end = find_route_to_end
RouteOptimizer.find_route_start_to_end = find_route_start_to_end

@app.route("/route-info")
def route_info():
    """Get basic route information"""
    initialize_points()
    
    return jsonify({
        'points': [
            {
                'index': i,
                'name': point['name'],
                'lat': point['lat'],
                'lon': point['lon']
            }
            for i, point in enumerate(optimizer.points)
        ],
        'total_points': len(optimizer.points)
    })

# Example usage and testing
if __name__ == '__main__':
    print("Starting Route Calculator Flask App...")
    print("Features:")
    print("- Interactive map with all your Prague locations")
    print("- Choose start and/or end points from dropdowns")
    print("- Calculate button to find optimal route")
    print("- Real-time route visualization")
    print("\nAccess the app at: http://127.0.0.1:5000")
    
    app.run(debug=True)