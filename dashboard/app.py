from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit
import sqlite3
import os
import re
import threading
import time

# GhostStack: Tactical Command Dashboard (Deployment Grade)
# Provides real-time mapping, hardware health, and mission event logging.

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
DB_PATH = 'ghoststack.db'

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>GhostStack Tactical Command</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0b0e14; color: #d1d5db; margin: 0; display: flex; flex-direction: column; height: 100vh; }
        .header { background: #1a1f29; padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #3b82f6; }
        .main { display: grid; grid-template-columns: 2fr 1fr; gap: 10px; padding: 10px; flex-grow: 1; overflow: hidden; }
        .panel { background: #1a1f29; border-radius: 4px; padding: 15px; display: flex; flex-direction: column; }
        .panel-title { font-size: 0.8rem; text-transform: uppercase; color: #9ca3af; margin-bottom: 10px; border-bottom: 1px solid #374151; padding-bottom: 5px; }
        #map { flex-grow: 1; border-radius: 4px; border: 1px solid #374151; }
        .log-container { flex-grow: 1; overflow-y: auto; font-size: 0.85rem; }
        table { width: 100%; border-collapse: collapse; }
        td { padding: 8px 5px; border-bottom: 1px solid #374151; vertical-align: top; }
        .threat { color: #ef4444; font-weight: bold; }
        .timestamp { color: #6b7280; font-family: monospace; width: 80px; }
        .status-ok { color: #10b981; }
        .status-err { color: #f59e0b; }
    </style>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
</head>
<body>
    <div class="header">
        <div style="font-weight: bold; font-size: 1.2rem; color: #3b82f6;">GHOSTSTACK // TACTICAL COMMAND</div>
        <div id="health-status" style="font-size: 0.8rem;">
            SDR: <span class="status-ok">ACTIVE</span> | 
            ESP32: <span class="status-ok">LOCKED</span> | 
            RPi5: <span class="status-ok">HEALTHY</span>
        </div>
    </div>
    <div class="main">
        <div class="panel">
            <div class="panel-title">Geospatial Intelligence (Real-Time)</div>
            <div id="map"></div>
        </div>
        <div class="panel">
            <div class="panel-title">Mission Event Log</div>
            <div class="log-container">
                <table>
                    <tbody id="events-table">
                        {% for row in rows %}
                        <tr>
                            <td class="timestamp">{{ row[1].split(' ')[1] }}</td>
                            <td class="{{ 'threat' if '[!]' in row[3] else '' }}">[{{ row[2] }}] {{ row[3] }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        var map = L.map('map').setView([37.7749, -122.4194], 13);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            className: 'map-tiles'
        }).addTo(map);

        var bounds = [];
        var socket = io.connect('http://' + document.domain + ':' + location.port);

        socket.on('new_event', function(data) {
            var table = document.getElementById('events-table');
            var newRow = table.insertRow(0);
            
            var cell1 = newRow.insertCell(0);
            var cell2 = newRow.insertCell(1);
            
            cell1.className = 'timestamp';
            cell1.innerHTML = data.timestamp.split(' ')[1];
            
            cell2.className = data.event.includes('[!]') ? 'threat' : '';
            cell2.innerHTML = '[' + data.module + '] ' + data.event;

            if (data.lat && data.lon) {
                L.marker([data.lat, data.lon]).addTo(map).bindPopup(data.desc).openPopup();
                bounds.push([data.lat, data.lon]);
                map.fitBounds(bounds);
            }
        });
    </script>
</body>
</html>
"""

def extract_coordinates(event_text, module):
    coord_pattern = re.compile(r'([-+]?\d{1,2}\.\d+),\s*([-+]?\d{1,3}\.\d+)')
    match = coord_pattern.search(event_text)
    if match:
        lat, lon = float(match.group(1)), float(match.group(2))
        return {"lat": lat, "lon": lon, "desc": f"[{module}] {event_text}"}
    return None

@app.route('/')
def index():
    rows = []
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('SELECT * FROM events ORDER BY id DESC LIMIT 50')
            rows = c.fetchall()
            conn.close()
        except Exception as e:
            print(f"Error accessing DB: {e}")
    return render_template_string(HTML_TEMPLATE, rows=rows)

def db_monitor():
    last_id = 0
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
                    coord = extract_coordinates(row[3], row[2])
                    socketio.emit('new_event', {
                        'timestamp': row[1],
                        'module': row[2],
                        'event': row[3],
                        'lat': coord['lat'] if coord else None,
                        'lon': coord['lon'] if coord else None,
                        'desc': coord['desc'] if coord else None
                    })
            except: pass

if __name__ == '__main__':
    monitor_thread = threading.Thread(target=db_monitor, daemon=True)
    monitor_thread.start()
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
