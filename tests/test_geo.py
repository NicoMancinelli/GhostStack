from ghoststack.geo import SafeZoneChecker, extract_coordinates, haversine_meters


def test_haversine_zero_distance():
    assert haversine_meters(37.7749, -122.4194, 37.7749, -122.4194) < 1.0


def test_extract_coordinates_keyed():
    text = "[!] TELEMETRY lat=37.7749, lon=-122.4194"
    coords = extract_coordinates(text)
    assert coords["lat"] == 37.7749
    assert coords["lon"] == -122.4194


def test_safe_zone_inside():
    zones = [{"name": "Base", "lat": 37.7749, "lon": -122.4194, "radius_meters": 500}]
    checker = SafeZoneChecker(zones)
    inside, name = checker.is_inside(37.7750, -122.4195)
    assert inside
    assert name == "Base"


def test_safe_zone_outside():
    zones = [{"name": "Base", "lat": 37.7749, "lon": -122.4194, "radius_meters": 10}]
    checker = SafeZoneChecker(zones)
    inside, _ = checker.is_inside(34.0, -118.0)
    assert not inside
