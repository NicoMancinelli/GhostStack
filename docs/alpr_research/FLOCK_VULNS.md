# ALPR & Flock Safety Research: Vulnerabilities & Disruption

## Overview
Automated License Plate Recognition (ALPR) systems, specifically those deployed by vendors like Flock Safety, represent a pervasive layer of persistent surveillance. This document summarizes known vulnerabilities and non-kinetic disruption techniques for research and defensive threat-modeling.

---

## 1. Known Vulnerabilities (CVE Research)
As documented by researchers like Jon Gaines (GainSec), several Flock devices have been found to have significant security lapses:

- **CVE-2025-47824:** Administrative endpoints lacking proper authentication.
- **Physical Access ADB:** Researchers demonstrated that a specific button sequence on the back panel of certain cameras can trigger a WiFi Access Point and allow **Android Debug Bridge (ADB)** access in under 30 seconds.
- **Outdated OS:** Many units run Android 8, which is past its end-of-life for security updates.
- **Exposed APIs:** Hardcoded ArcGIS API keys have been discovered in publicly accessible firmware, allowing for mapping of camera locations.

---

## 2. Disruption Techniques

### A. Optical Disruption (Infrared)
Most ALPR cameras rely on high-intensity IR illumination (usually 850nm) and global shutter sensors to capture clear plates at high speeds.
- **Retro-Reflective Saturation:** Using high-power IR LEDs (as implemented in the `optical_disruption` module) to create a "bloom" effect on the retro-reflective coating of the license plate.
- **Modulated Strobing:** Randomized IR strobing can desync the camera's auto-exposure, leading to over-exposed frames where the plate is a solid white block.

### B. Network/RF Disruption
- **Passive Detection:** Using the `flock_detector.py` script to identify cameras via WiFi probe requests and OUIs.
- **Deauthentication (Research Only):** Many ALPR cameras use LTE/5G for primary backhaul but fail back to hardcoded WiFi networks for maintenance. Identifying and deauthenticating these maintenance links can occasionally trigger reboot loops or diagnostic modes.

### C. Adversarial Physical Attacks
- **Adversarial Patches:** Small, printable patterns applied to license plate frames that exploit the weaknesses of object detection models (e.g., YOLOv5).
- **PlateShapez:** Using mathematical perturbations to modify the font or spacing of a plate in a way that is human-readable but causes OCR engines to fail or output incorrect strings (e.g., '0' vs '8').

---

## 3. Hardware Requirements for ALPR Research
- **WiFi Adapter:** ALFA AWUS036ACM (MT7612U chipset) for monitor mode.
- **SDR:** HackRF One for analyzing LTE backhaul signals (research phase).
- **Optical:** 850nm High-Power IR LED arrays (GhostStack Optical Module).

---

## ⚠️ Legal Notice
*Refer to the primary README.md for legal disclaimers. Testing against public infrastructure is illegal. Research should only be conducted on owned hardware in controlled environments.*
