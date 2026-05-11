# Legal and Ethical Mandate

**GhostStack is strictly an educational research platform.** 

The intersection of Software Defined Radio, Electronic Warfare, and Physical Disruption carries severe legal liabilities if misused.

## 1. The FCC (USA) and OFCOM (UK)
- **Jamming:** Transmitting RF noise to block legitimate communications (Wi-Fi, GPS, Control Links) is a federal crime in the United States, punishable by severe fines and imprisonment. GhostStack focuses on *passive detection* and *classification*.
- **GPS Simulation:** Projects like `gps-sdr-sim` must ONLY be used over direct, RF-shielded coaxial cables with inline attenuators (at least 60dB) directly into a receiver. Radiating fake GPS signals over the air endangers commercial aviation and emergency services.

## 2. Aviation Law (FAA)
- **Unauthorized Interference:** Injecting MAVLink commands (like the `disarm_poc.py`) into an aircraft you do not own or have authorization to test is a violation of FAA regulations regarding the safe operation of aircraft.

## 3. Asymmetric Defense Research
GhostStack exists to study the **vulnerabilities** of these systems so that better, more resilient protocols (like cryptographically signed MAVLink v2.0) can be widely adopted by the industry. All red-teaming must occur in closed, controlled laboratory environments.
