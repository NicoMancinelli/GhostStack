import cv2
from ultralytics import YOLO
import logging
import os

# GhostStack: CV Layer - YOLOv8 Baseline Detector
# 
# This script serves as the baseline for testing adversarial patches.
# It runs a real-time YOLOv8 detector on the primary webcam.
# Automatically utilizes TFLite models if available for optimized edge performance.

logging.basicConfig(level=logging.INFO)

def main():
    # Prefer TFLite optimized model
    model_path = 'yolov8n.tflite'
    if not os.path.exists(model_path):
        logging.info("[!] TFLite model not found. Falling back to PyTorch (.pt).")
        model_path = 'yolov8n.pt'
        logging.info("[*] Consider running 'python3 cv_adversarial/utils/convert_model.py' to optimize performance.")

    logging.info(f"[*] Loading YOLOv8 model: {model_path}...")
    model = YOLO(model_path)

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
