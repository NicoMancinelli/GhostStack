import json
import logging
import os
import time

import paho.mqtt.client as mqtt

from ghoststack.events import format_threat

# GhostStack: GamutRF MQTT Connector
# Emits structured threat lines for the policy engine (module name: gamutrf).

logging.basicConfig(level=logging.INFO, format="%(message)s")

MQTT_BROKER = os.environ.get("GHOSTSTACK_MQTT_BROKER", "127.0.0.1")
MQTT_PORT = int(os.environ.get("GHOSTSTACK_MQTT_PORT", "1883"))
MQTT_TOPIC = os.environ.get("GHOSTSTACK_MQTT_TOPIC", "gamutrf/inference")
CONFIDENCE_THRESHOLD = float(
    os.environ.get(
        "GHOSTSTACK_GAMUTRF_CONFIDENCE",
        "0.75" if os.environ.get("GHOSTSTACK_SENTRY") == "1" else "0.85",
    )
)

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
        predictions = payload.get("predictions", {})
        center_freq = payload.get("center_freq", 0) / 1e6

        for tgt in TARGET_CLASSES:
            if tgt in predictions and predictions[tgt] >= CONFIDENCE_THRESHOLD:
                conf = float(predictions[tgt])
                logging.info(
                    format_threat(
                        f"GamutRF Detection: '{tgt}' at {center_freq:.1f} MHz",
                        confidence=conf,
                    )
                )
    except json.JSONDecodeError:
        pass
    except Exception as exc:
        logging.error(f"Error parsing message: {exc}")


def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    logging.info(f"[*] Starting GamutRF Connector. Connecting to {MQTT_BROKER}:{MQTT_PORT}...")
    logging.info(f"[*] Confidence threshold: {CONFIDENCE_THRESHOLD}")

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
