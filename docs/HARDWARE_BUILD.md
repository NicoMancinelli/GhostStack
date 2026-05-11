# Hardware Build: Optical Blinder Module

## Overview
This module uses a high-frequency IR strobe to disrupt UAV camera sensors (rolling shutter effects) and LiDAR navigation.

## Bill of Materials (BOM)
- **Controller:** ESP32-S3 DevKit
- **Emitter:** 4x High-Power IR LEDs (850nm or 940nm, 1W-3W)
- **Switch:** IRLZ44N N-Channel Logic-Level MOSFET
- **Resistors:** 
    - 1x 220Ω (Gate resistor)
    - 1x 10kΩ (Pull-down for Gate)
- **Power:** 7.4V - 11.1V LiPo Battery
- **Misc:** Heat sinks for MOSFET and LEDs, Buck converter (for ESP32 5V supply)

## Pinout Diagram
```text
ESP32 GPIO 4  ---> [220Ω Resistor] ---> MOSFET Gate
ESP32 GND     -------------------------> MOSFET Source
Battery (+)   ---> IR LED Array (+)
IR LED Array (-) ----------------------> MOSFET Drain
Battery (-)   -------------------------> MOSFET Source (Common GND)
```

## Bench Testing & Verification

Once assembled, follow this procedure to verify the effectiveness of the Optical Blinder:

### 1. Visual Verification (Non-Human Eye)
Since IR is invisible, use a smartphone camera (many front-facing cameras lack IR filters) or a dedicated IR detection card to confirm the emitters are strobing correctly.

### 2. Rolling Shutter Desync Test
- **Target:** Any CMOS camera with a rolling shutter (most webcams/smartphones).
- **Procedure:** 
    1. Point the camera at a scene.
    2. Activate the GhostStack Optical Module via `ghoststack_ctl.py`.
    3. Observe the video feed. A successful desync will manifest as **static or moving horizontal dark/light bands** across the frame, which disrupts object detection and auto-exposure.

### 3. LiDAR Interference Test
- **Target:** Consumer LiDAR sensor (e.g., iPhone Pro LiDAR, RPLiDAR).
- **Procedure:** Observe the point cloud in a visualizer. High-power IR pulses should manifest as "ghost points" or increased noise floor, potentially causing SLAM (Simultaneous Localization and Mapping) failures.
