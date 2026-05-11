# GhostStack: Computer Vision Adversarial Research

## Overview
This module focuses on disrupting the "vision" of autonomous systems (UAV cameras, Quadruped ToF sensors, and ALPR cameras) using Adversarial Machine Learning.

---

## 1. Adversarial Patches for YOLOv8
Targeting the most common object detection model used in modern robotics.
- **Project Reference:** [NaturalisticAdversarialPatches](https://github.com/Bimo99B9/NaturalisticAdversarialPatches).
- **Technique:** Generating patches that exploit "Objectness Loss" to make a person or vehicle "invisible" to the AI detector.
- **EOT (Expectation over Transformation):** Ensuring patches work in the physical world across varying angles and lighting.

## 2. ALPR Disruption (Flock Safety)
- **PlateShapez:** Using mathematical perturbations to the license plate font that cause OCR errors while remaining human-readable.
- **IR Saturation:** (Refer to `optical_disruption/` module) for desyncing global shutter sensors.

## 3. Human Counter-Surveillance
- **Adversarial Clothing:** Researching patterns that trigger high-confidence false positives in person-detectors (e.g., "cloaking" by tricking the AI into seeing a chair or a dog instead of a human).

---

## Implementation Plan
- **Training:** Use the provided scripts in `cv_adversarial/patches/` to generate custom patches based on the `seba20-0/Adversarial-Attacks-on-YOLO` toolkit.
- **Verification:** Test generated patches against a local YOLOv8-nano instance running on the Raspberry Pi 5.
