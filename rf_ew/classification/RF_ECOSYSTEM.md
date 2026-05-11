# GhostStack: Advanced RF Analysis & Signal Classification

## Overview
This module integrates research-grade signal classification techniques to identify and track autonomous system telemetry and control links.

---

## 1. GamutRF Integration (Real-Time Classification)
[GamutRF](https://github.com/IQTLabs/gamutrf) is a high-performance spectrum analyzer and classifier.
- **Role in GhostStack:** Acts as the primary "ear" for the Raspberry Pi 5, performing real-time FFT and classification of signals in the 2.4GHz and 5.8GHz bands.
- **Setup:** See `config/gamutrf/` for initial deployment configurations.

## 2. Protocol Analysis (Drone-ID & Remote ID)
For identifying specific drone models and locations:
- **Drone-ID (DJI):** Utilizes the research from `RUB-SysSec/Drone-ID` to decode OcuSync telemetry.
- **Remote ID:** Passive monitoring of FAA-mandated Remote ID broadcasts using `phantom-proof` or `sigint`.

## 3. GNSS Resilience Research
Using `gps-sdr-sim` and `ghostsignal` for testing receiver robustness.
- **Goal:** Analyzing how autonomous systems respond to GNSS signal degradation or inconsistency (e.g., "GPS Jumping").
- **Safety:** All GNSS research MUST be performed using direct-cable connections with 60dB+ attenuators to prevent over-the-air transmission.

---

## Technical Specs
- **Supported Hardware:** HackRF One, Ettus USRP, RTL-SDR.
- **Key Libraries:** SoapySDR, GNU Radio 3.10, PyTorch (for custom ML classification).
