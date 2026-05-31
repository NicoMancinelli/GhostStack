(function () {
    var center = window.GHOSTSTACK_MAP || { lat: 37.7749, lon: -122.4194 };
    var authCfg = window.GHOSTSTACK_AUTH || {};
    var map = L.map('map').setView([center.lat, center.lon], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        className: 'map-tiles'
    }).addTo(map);

    var bounds = [];
    var socketOpts = {};
    if (authCfg.enabled) {
        socketOpts.auth = authCfg.socketAuth || {};
    }
    var socket = io.connect(window.location.origin, socketOpts);

    function renderHealth(health) {
        var el = document.getElementById('health-status');
        var parts = [];
        for (var key in health) {
            var ok = !(health[key].includes('NOT FOUND') || health[key].includes('OFFLINE'));
            parts.push(
                key.toUpperCase() + ': <span class="' + (ok ? 'status-ok' : 'status-err') + '">' +
                health[key] + '</span>'
            );
        }
        el.innerHTML = parts.join(' | ');
    }

    socket.on('connect_error', function () {
        document.getElementById('health-status').innerHTML =
            '<span class="status-err">Socket auth failed — refresh and re-login</span>';
    });

    socket.on('health_update', function (data) { renderHealth(data); });

    socket.on('new_event', function (data) {
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
})();
