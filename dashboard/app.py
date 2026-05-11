from flask import Flask, render_template_string
import sqlite3
import os

# GhostStack: Live Threat Dashboard
# 
# A lightweight Flask application that reads the local SQLite database
# populated by ghoststack_ctl.py and visualizes detected threats.

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
    </style>
    <!-- Auto-refresh page every 5 seconds -->
    <meta http-equiv="refresh" content="5">
</head>
<body>
    <h1>📡 GhostStack Live Threat Dashboard</h1>
    <p>Monitoring active RF, Network, and CV alerts.</p>
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
</body>
</html>
"""

@app.route('/')
def index():
    rows = []
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            # Fetch the 50 most recent events
            c.execute('SELECT * FROM events ORDER BY id DESC LIMIT 50')
            rows = c.fetchall()
            conn.close()
        except Exception as e:
            print(f"Error accessing DB: {e}")
    
    return render_template_string(HTML_TEMPLATE, rows=rows)

if __name__ == '__main__':
    print("[*] Starting GhostStack Dashboard on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000)
