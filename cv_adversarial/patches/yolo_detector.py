import cv2
from ultralytics import YOLO
import logging

# GhostStack: CV Layer - YOLOv8 Baseline Detector
# 
# This script serves as the baseline for testing adversarial patches.
# It runs a real-time YOLOv8-nano detector on the primary webcam.

logging.basicConfig(level=logging.INFO)

def main():
    # Load the YOLOv8n model
    logging.info("[*] Loading YOLOv8n model...")
    model = YOLO('yolov8n.pt')

    # Initialize webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logging.error("[-] Could not open webcam.")
        return

    logging.info("[*] Starting detector. Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Run inference
        results = model(frame, verbose=False)

        # Annotate frame
        annotated_frame = results[0].plot()

        # Display output
        cv2.imshow("GhostStack CV Baseline: YOLOv8", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
