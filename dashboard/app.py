from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit
import threading
import time

from ghoststack.config_loader import load_targets
from ghoststack.database import EventStore
from ghoststack.geo import extract_coordinates

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
store = EventStore()
targets = load_targets()
map_center = targets.get("default_map_center", {"lat": 37.7749, "lon": -122.4194})

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
        <div id="health-status" style="font-size: 0.8rem;">Loading health...</div>
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
                            <td class="timestamp">{{ row[1].split(' ')[1] if row[1] else '' }}</td>
                            <td class="{{ 'threat' if '[!]' in row[3] else '' }}">[{{ row[2] }}] {{ row[3] }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        var map = L.map('map').setView([{{ map_lat }}, {{ map_lon }}], 13);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            className: 'map-tiles'
        }).addTo(map);

        var bounds = [];
        var socket = io.connect('http://' + document.domain + ':' + location.port);

        function renderHealth(health) {
            var el = document.getElementById('health-status');
            var parts = [];
            for (var key in health) {
                var ok = !(health[key].includes('NOT FOUND') || health[key].includes('OFFLINE'));
                parts.push(key.toUpperCase() + ': <span class="' + (ok ? 'status-ok' : 'status-err') + '">' + health[key] + '</span>');
            }
            el.innerHTML = parts.join(' | ');
        }

        socket.on('health_update', function(data) { renderHealth(data); });

        socket.on('new_event', function(data) {
            var table = document.getElementById('events-table');
            var newRow = table.insertRow(0);
            var cell1 = newRow.insertCell(0);
            var cell2 = newRow.insertCell(1);
            cell1.className = 'timestamp';
            cell1.innerHTML = (data.timestamp || '').split(' ')[1] || '';
            cell2.className = data.event.includes('[!]') ? 'threat' : '';
            cell2.innerHTML = '[' + data.module + '] ' + data.event;
            if (data.lat && data.lon) {
                L.marker([data.lat, data.lon]).addTo(map).bindPopup(data.desc).openPopup();
                bounds.push([data.lat, data.lon]);
                if (bounds.length) map.fitBounds(bounds);
            }
        });
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    rows = store.get_recent_events(50)
    return render_template_string(
        HTML_TEMPLATE,
        rows=rows,
        map_lat=map_center.get("lat", 37.7749),
        map_lon=map_center.get("lon", -122.4194),
    )


def db_monitor():
    last_id = 0
    while True:
        time.sleep(1)
        for row in store.get_events_after(last_id):
            last_id = row[0]
            coord = extract_coordinates(row[3])
            socketio.emit(
                "new_event",
                {
                    "timestamp": row[1],
                    "module": row[2],
                    "event": row[3],
                    "lat": coord["lat"] if coord else None,
                    "lon": coord["lon"] if coord else None,
                    "desc": f"[{row[2]}] {row[3]}" if coord else None,
                },
            )


def health_monitor():
    while True:
        time.sleep(5)
        socketio.emit("health_update", store.get_latest_health())


if __name__ == "__main__":
    threading.Thread(target=db_monitor, daemon=True).start()
    threading.Thread(target=health_monitor, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)
