from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit
import sqlite3
import os
import re
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
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
    <!-- SocketIO -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
</head>
<body>
    <h1>📡 GhostStack Live Threat Dashboard</h1>
    <p>Monitoring active RF, Network, and CV alerts.</p>
    
    <div id="map"></div>

    <table>
        <thead>
            <tr>
                <th>Timestamp</th>
                <th>Module</th>
                <th>Event Details</th>
            </tr>
        </thead>
        <tbody id="events-table">
            {% for row in rows %}
            <tr>
                <td>{{ row[1] }}</td>
                <td>[{{ row[2] }}]</td>
                <td class="threat">{{ row[3] }}</td>
            </tr>
            {% else %}
            <tr id="no-threats"><td colspan="3" style="text-align: center;">No threats detected... yet.</td></tr>
            {% endfor %}
        </tbody>
    </table>

    <script>
        var map = L.map('map').setView([37.7749, -122.4194], 10);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            className: 'map-tiles'
        }).addTo(map);

        var bounds = [];
        var markers = {};

        var initialCoordinates = {{ coordinates | tojson | safe }};
        if (initialCoordinates && initialCoordinates.length > 0) {
            initialCoordinates.forEach(function(coord) {
                var marker = L.marker([coord.lat, coord.lon]).addTo(map)
                    .bindPopup(coord.desc);
                bounds.push([coord.lat, coord.lon]);
            });
            map.fitBounds(bounds);
        }

        var socket = io.connect('http://' + document.domain + ':' + location.port);

        socket.on('new_event', function(data) {
            var noThreatsRow = document.getElementById('no-threats');
            if (noThreatsRow) {
                noThreatsRow.remove();
            }

            var table = document.getElementById('events-table');
            var newRow = table.insertRow(0); // Insert at top
            
            var cell1 = newRow.insertCell(0);
            var cell2 = newRow.insertCell(1);
            var cell3 = newRow.insertCell(2);
            
            cell1.innerHTML = data.timestamp;
            cell2.innerHTML = '[' + data.module + ']';
            cell3.innerHTML = data.event;
            cell3.className = 'threat';

            // Add marker if coordinates exist
            if (data.lat && data.lon) {
                var marker = L.marker([data.lat, data.lon]).addTo(map)
                    .bindPopup(data.desc);
                bounds.push([data.lat, data.lon]);
                map.fitBounds(bounds);
            }
        });
    </script>
</body>
</html>
"""

def extract_coordinates(event_text, module, timestamp):
    coords = []
    coord_pattern = re.compile(r'([-+]?\d{1,2}\.\d+),\s*([-+]?\d{1,3}\.\d+)')
    match = coord_pattern.search(event_text)
    if match:
        lat, lon = float(match.group(1)), float(match.group(2))
        return {"lat": lat, "lon": lon, "desc": f"[{module}] {event_text}"}
    return None

def extract_coordinates_from_rows(rows):
    coords = []
    for row in rows:
        coord = extract_coordinates(row[3], row[2], row[1])
        if coord:
            coords.append(coord)
    return coords

@app.route('/')
def index():
    rows = []
    coordinates = []
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('SELECT * FROM events ORDER BY id DESC LIMIT 50')
            rows = c.fetchall()
            conn.close()
            coordinates = extract_coordinates_from_rows(rows)
        except Exception as e:
            print(f"Error accessing DB: {e}")
    
    return render_template_string(HTML_TEMPLATE, rows=rows, coordinates=coordinates)

def db_monitor():
    last_id = 0
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('SELECT MAX(id) FROM events')
            res = c.fetchone()
            if res and res[0]:
                last_id = res[0]
            conn.close()
        except:
            pass

    while True:
        time.sleep(1)
        if os.path.exists(DB_PATH):
            try:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute('SELECT * FROM events WHERE id > ? ORDER BY id ASC', (last_id,))
                new_rows = c.fetchall()
                conn.close()
                
                for row in new_rows:
                    last_id = row[0]
                    coord = extract_coordinates(row[3], row[2], row[1])
                    event_data = {
                        'timestamp': row[1],
                        'module': row[2],
                        'event': row[3],
                        'lat': coord['lat'] if coord else None,
                        'lon': coord['lon'] if coord else None,
                        'desc': coord['desc'] if coord else None
                    }
                    socketio.emit('new_event', event_data)
            except Exception as e:
                print(f"Monitor error: {e}")

@socketio.on('connect')
def test_connect():
    print('Client connected')

if __name__ == '__main__':
    print("[*] Starting GhostStack WebSocket Dashboard on http://0.0.0.0:5000")
    monitor_thread = threading.Thread(target=db_monitor, daemon=True)
    monitor_thread.start()
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
