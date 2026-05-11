# GhostStack Demo: Live Threat Defense Protocol

This guide outlines a demonstration scenario for showcasing the GhostStack framework in a red-team or research presentation.

## Prerequisites
- A Raspberry Pi 5 running GhostStack (via Docker or Bare-Metal).
- An ESP32 Optical Blinder module connected via USB (`/dev/ttyUSB0`).
- A target to generate telemetry (e.g., `Damn Vulnerable Drone` simulator or ArduPilot SITL).

## The Scenario

### 1. Start the Environment
Begin by launching the Master Orchestrator with hardware triggering enabled, and spin up the dashboard.
```bash
# Terminal 1: Launch Dashboard
python3 dashboard/app.py

# Terminal 2: Launch GhostStack CTL with ESP32 attached
python3 scripts/ghoststack_ctl.py start-network --esp-port /dev/ttyUSB0
```
Open a browser to `http://localhost:5000` and show the empty Leaflet map.

### 2. Initiate the "Threat"
On a separate machine or terminal, run a MAVLink simulator or the `spoofing_node.py` to generate fake telemetry over UDP/14550.
```bash
ros2 run ghoststack_network spoofer
```

### 3. Observe the "Kill Chain"
1. **Detection:** GhostStack's `mavlink_sniff` or `remote_id_sniffer` will intercept the incoming packets.
2. **Visualization:** The Leaflet map on the Dashboard will automatically refresh, plotting a red marker at the exact coordinates extracted from the telemetry.
3. **Execution (Hardware Trigger):** Look at the physical ESP32 module. Within milliseconds of the dashboard logging the threat, `ghoststack_ctl.py` will send the `b'1'` command over Serial. The IR LED array will begin strobing violently.
4. **Timeout:** Stop the "Threat" simulator. Wait 10 seconds, and point out that the orchestrator automatically disengages the strobe (`b'0'`) after the threat timeout period.

## Conclusion
This visually demonstrates the automated, closed-loop nature of GhostStack: **Detect (Software) -> Visualize (Dashboard) -> Disrupt (Hardware Effectors).**
