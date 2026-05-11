import os
import sys
from ultralytics import YOLO

# GhostStack: CV Layer - Edge Optimization Utility
#
# Converts trained YOLOv8 PyTorch models (.pt) to TFLite format
# for high-performance inference on the Raspberry Pi 5.

def convert_to_tflite(model_path):
    if not os.path.exists(model_path):
        print(f"[-] Model not found at {model_path}")
        return

    print(f"[*] Loading YOLOv8 model: {model_path}...")
    model = YOLO(model_path)

    print("[*] Exporting to TFLite (INT8 quantization recommended for RPi5)...")
    # TFLite export requires specific dependencies (tensorflow, etc.)
    try:
        model.export(format='tflite', int8=True)
        print(f"[+] Export successful. TFLite model generated in {os.path.dirname(model_path)}")
    except Exception as e:
        print(f"[-] Export failed: {e}")
        print("[!] Ensure you have the required export dependencies: pip install tensorflow-cpu tflite-support")

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else 'yolov8n.pt'
    convert_to_tflite(path)
