import json
import os
import threading

from flask import Flask, jsonify, render_template, request, session

from ghoststack.auth import check_http_auth, check_socket_auth, credentials_valid, require_http_auth
from ghoststack.config_loader import load_targets
from ghoststack.database import EventStore
from ghoststack.geo import extract_coordinates
app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "static"),
)
app.secret_key = os.environ.get("GHOSTSTACK_FLASK_SECRET", "ghoststack-dev-secret-change-me")

store = EventStore()
targets = load_targets()
map_center = targets.get("default_map_center", {"lat": 37.7749, "lon": -122.4194})


def _auth_client_config():
    from ghoststack.auth import _dashboard_config

    cfg = _dashboard_config()
    token = cfg["token"] or f"{cfg['username']}:{cfg['password']}"
    return {
        "enabled": cfg["auth_enabled"],
        "socketAuth": {"token": token} if cfg["auth_enabled"] else {},
    }


def _init_socketio():
    global socketio
    from flask_socketio import SocketIO

    socketio = SocketIO(app, cors_allowed_origins="*")

    @socketio.on("connect")
    def on_connect(auth=None):
        if not check_socket_auth(auth):
            return False

    return socketio


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username", "")
        password = request.form.get("password", "")
        if credentials_valid(user, password):
            session["authenticated"] = True
            return render_template("login.html", success=True)
        return render_template("login.html", error="Invalid credentials"), 401
    return render_template("login.html")


@app.route("/")
@require_http_auth
def index():
    rows = store.get_recent_events(50)
    return render_template(
        "index.html",
        rows=rows,
        map_lat=map_center.get("lat", 37.7749),
        map_lon=map_center.get("lon", -122.4194),
        auth_json=json.dumps(_auth_client_config()),
    )


@app.route("/api/health")
@require_http_auth
def api_health():
    return jsonify(store.get_latest_health())


def db_monitor():
    last_id = 0
    while True:
        import time

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
    import time

    while True:
        time.sleep(5)
        socketio.emit("health_update", store.get_latest_health())


socketio = _init_socketio()

if __name__ == "__main__":
    threading.Thread(target=db_monitor, daemon=True).start()
    threading.Thread(target=health_monitor, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)
