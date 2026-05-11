import SoapySDR
from SoapySDR import *
import numpy as np
import time
import logging

# GhostStack: RF/EW Layer - 2.4GHz Power Scanner
# Target: Identify potential UAV control links and FHSS activity

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    # Initialize SDR (HackRF or RTL-SDR via SoapySDR)
    try:
        sdr = SoapySDR.Device(dict(driver=None)) # Auto-detect
    except Exception as e:
        logging.error(f"Failed to find SDR: {e}")
        return

    # Configuration
    sample_rate = 10e6
    center_freq = 2.44e9
    gain = 40

    sdr.setSampleRate(SOAPY_SDR_RX, 0, sample_rate)
    sdr.setFrequency(SOAPY_SDR_RX, 0, center_freq)
    sdr.setGain(SOAPY_SDR_RX, 0, gain)

    rx_stream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
    sdr.activateStream(rx_stream)

    buff = np.array([0]*1024, np.complex64)
    logging.info(f"Scanning 2.4GHz ISM band at {center_freq/1e9} GHz...")

    try:
        while True:
            sr = sdr.readStream(rx_stream, [buff], len(buff))
            if sr.ret > 0:
                power = 10 * np.log10(np.mean(np.abs(buff)**2) + 1e-12)
                if power > -35: # Detection Threshold
                    logging.info(f"[!] Activity Detected: Power {power:.2f} dB")
            time.sleep(0.01)
    except KeyboardInterrupt:
        logging.info("Scanning halted.")
    finally:
        sdr.deactivateStream(rx_stream)
        sdr.closeStream(rx_stream)

if __name__ == '__main__':
    main()
