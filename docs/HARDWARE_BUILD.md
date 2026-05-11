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

## Safety Precautions
1. **Eye Safety:** High-power IR is invisible. Do not stare directly at the emitters. Use IR-detecting cards or a phone camera (without IR filter) to verify operation.
2. **Thermal Management:** High-power LEDs generate significant heat. Always use aluminum heat sinks.
3. **Current Limits:** Ensure the MOSFET is logic-level (IRL series) to allow full switching from the ESP32 3.3V logic.
