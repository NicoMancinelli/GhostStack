import paho.mqtt.client as mqtt
import json
import logging
import time

# GhostStack: GamutRF MQTT Connector
#
# Connects to the local GamutRF inference stream via MQTT.
# When GamutRF identifies a specific RF signature (e.g., 'dji_mavic'),
# it prints an alert that ghoststack_ctl.py logs to the database.

logging.basicConfig(level=logging.INFO, format='%(message)s')

MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "gamutrf/inference"
CONFIDENCE_THRESHOLD = 0.85

TARGET_CLASSES = ["dji_mavic", "dji_phantom", "parrot", "generic_uav"]

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("[*] GamutRF Connector connected to MQTT broker.")
        client.subscribe(MQTT_TOPIC)
    else:
        logging.error(f"[-] Failed to connect to MQTT broker. Code: {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        
        # Expected GamutRF JSON Structure (simplified)
        # {"predictions": {"dji_mavic": 0.92, "wifi": 0.1}, "center_freq": 2440000000}
        
        predictions = payload.get("predictions", {})
        center_freq = payload.get("center_freq", 0) / 1e6 # Convert to MHz
        
        for tgt in TARGET_CLASSES:
            if tgt in predictions and predictions[tgt] >= CONFIDENCE_THRESHOLD:
                conf = predictions[tgt]
                # The '[!]' prefix flags this as a threat to ghoststack_ctl.py
                logging.info(f"[!] GamutRF Detection: '{tgt}' at {center_freq} MHz (Conf: {conf:.2f})")
                
    except json.JSONDecodeError:
        pass
    except Exception as e:
        logging.error(f"Error parsing message: {e}")

def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    logging.info(f"[*] Starting GamutRF Connector. Connecting to {MQTT_BROKER}:{MQTT_PORT}...")
    
    # Retry loop in case GamutRF is still spinning up
    while True:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            break
        except ConnectionRefusedError:
            logging.info("[*] Broker not available yet. Retrying in 5 seconds...")
            time.sleep(5)

    client.loop_forever()

if __name__ == "__main__":
    main()
