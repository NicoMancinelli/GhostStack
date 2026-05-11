from flask import Flask, render_template_string
import sqlite3
import os
import re

# GhostStack: Live Threat Dashboard
# 
# A lightweight Flask application that reads the local SQLite database
# populated by ghoststack_ctl.py and visualizes detected threats.
# Now includes Leaflet.js for geographic mapping of intercepted coordinates.

app = Flask(__name__)
DB_PATH = 'ghoststack.db'

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>GhostStack Dashboard</title>
    <style>
        body { font-family: 'Courier New', Courier, monospace; background-color: #121212; color: #00ff00; margin: 0; padding: 20px; }
        h1 { border-bottom: 1px solid #00ff00; padding-bottom: 10px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #00ff00; padding: 10px; text-align: left; }
        th { background-color: #1e1e1e; }
        .threat { color: #ff0000; font-weight: bold; }
        #map { height: 400px; width: 100%; margin-top: 20px; border: 1px solid #00ff00; }
    </style>
    <!-- Leaflet CSS & JS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <!-- Auto-refresh page every 5 seconds -->
    <meta http-equiv="refresh" content="5">
</head>
<body>
    <h1>📡 GhostStack Live Threat Dashboard</h1>
    <p>Monitoring active RF, Network, and CV alerts.</p>
    
    <div id="map"></div>

    <table>
        <tr>
            <th>Timestamp</th>
            <th>Module</th>
            <th>Event Details</th>
        </tr>
        {% for row in rows %}
        <tr>
            <td>{{ row[1] }}</td>
            <td>[{{ row[2] }}]</td>
            <td class="threat">{{ row[3] }}</td>
        </tr>
        {% else %}
        <tr><td colspan="3" style="text-align: center;">No threats detected... yet.</td></tr>
        {% endfor %}
    </table>

    <script>
        // Initialize Map
        var map = L.map('map').setView([37.7749, -122.4194], 10); // Default to SF
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            className: 'map-tiles'
        }).addTo(map);

        // Add markers from intercepted coordinates
        var coordinates = {{ coordinates | tojson }};
        if (coordinates.length > 0) {
            var bounds = [];
            coordinates.forEach(function(coord) {
                var marker = L.marker([coord.lat, coord.lon]).addTo(map)
                    .bindPopup(coord.desc);
                bounds.push([coord.lat, coord.lon]);
            });
            map.fitBounds(bounds);
        }
    </script>
</body>
</html>
"""

def extract_coordinates(rows):
    """Simple regex to extract Lat/Lon from event text."""
    coords = []
    # Looks for simple patterns like "Pos: 37.77490, -122.41940" or "Lat: 37.1, Lon: -122.1"
    coord_pattern = re.compile(r'([-+]?\d{1,2}\.\d+),\s*([-+]?\d{1,3}\.\d+)')
    
    for row in rows:
        event_text = row[3]
        match = coord_pattern.search(event_text)
        if match:
            lat, lon = float(match.group(1)), float(match.group(2))
            coords.append({
                "lat": lat,
                "lon": lon,
                "desc": f"[{row[1]}] {row[2]}"
            })
    return coords

@app.route('/')
def index():
    rows = []
    coordinates = []
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            # Fetch the 50 most recent events
            c.execute('SELECT * FROM events ORDER BY id DESC LIMIT 50')
            rows = c.fetchall()
            conn.close()
            
            # Extract coordinates for mapping
            coordinates = extract_coordinates(rows)
        except Exception as e:
            print(f"Error accessing DB: {e}")
    
    return render_template_string(HTML_TEMPLATE, rows=rows, coordinates=coordinates)

if __name__ == '__main__':
    print("[*] Starting GhostStack Dashboard on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000)
