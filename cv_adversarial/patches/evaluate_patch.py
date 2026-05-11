import torch
from ultralytics import YOLO
import torchvision.transforms as T
from PIL import Image
import os
import glob
import logging

# GhostStack: CV Layer - Automated Patch Evaluation
# 
# Evaluates the effectiveness of an adversarial patch against a dataset of images.
# It calculates the average drop in confidence for the target class ('person').

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [EVALUATE] - %(message)s')

class PatchEvaluator:
    def __init__(self, model_name='yolov8n.pt', target_class=0):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = YOLO(model_name)
        self.target_class = target_class

    def evaluate(self, dataset_dir, patch_path):
        if not os.path.exists(dataset_dir) or not os.path.exists(patch_path):
            logging.error("Dataset directory or patch file not found.")
            return

        patch_img = Image.open(patch_path).convert('RGB')
        patch_tensor = T.ToTensor()(patch_img).to(self.device)
        _, p_h, p_w = patch_tensor.shape

        image_files = glob.glob(os.path.join(dataset_dir, '*.jpg')) + glob.glob(os.path.join(dataset_dir, '*.png'))
        if not image_files:
            logging.error(f"No images found in {dataset_dir}")
            return

        baseline_confs = []
        patched_confs = []

        logging.info(f"[*] Evaluating patch on {len(image_files)} images...")

        for img_path in image_files:
            # Load Original Image
            img = Image.open(img_path).convert('RGB').resize((640, 640))
            img_tensor = T.ToTensor()(img).to(self.device)

            # Baseline Inference
            results_base = self.model(img, verbose=False)
            base_conf = self._get_max_conf(results_base)
            baseline_confs.append(base_conf)

            # Apply Patch (simplified overlay on center)
            c_y, c_x = 320, 320
            start_y, start_x = c_y - p_h//2, c_x - p_w//2
            patched_tensor = img_tensor.clone()
            patched_tensor[:, start_y:start_y+p_h, start_x:start_x+p_w] = patch_tensor

            patched_img = T.ToPILImage()(patched_tensor.cpu())

            # Patched Inference
            results_patched = self.model(patched_img, verbose=False)
            patched_conf = self._get_max_conf(results_patched)
            patched_confs.append(patched_conf)

        avg_base = sum(baseline_confs) / len(baseline_confs)
        avg_patched = sum(patched_confs) / len(patched_confs)
        drop = avg_base - avg_patched

        logging.info("=== Evaluation Report ===")
        logging.info(f"Total Images: {len(image_files)}")
        logging.info(f"Average Baseline Confidence: {avg_base:.4f}")
        logging.info(f"Average Patched Confidence:  {avg_patched:.4f}")
        logging.info(f"Absolute Confidence Drop:    {drop:.4f}")
        logging.info("=========================")

    def _get_max_conf(self, results):
        """Extract the maximum confidence score for the target class."""
        max_conf = 0.0
        for r in results:
            boxes = r.boxes
            if boxes is not None:
                for cls, conf in zip(boxes.cls, boxes.conf):
                    if int(cls.item()) == self.target_class:
                        if conf.item() > max_conf:
                            max_conf = conf.item()
        return max_conf

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3:
        dataset = sys.argv[1]
        patch = sys.argv[2]
        evaluator = PatchEvaluator()
        evaluator.evaluate(dataset, patch)
    else:
        print("Usage: python3 evaluate_patch.py <dataset_directory> <patch_image.png>")
        print("Example: python3 evaluate_patch.py ./test_images cv_adversarial/patches/adv_patch.png")
