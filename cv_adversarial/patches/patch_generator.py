import torch
import torch.nn as nn
from ultralytics import YOLO
import numpy as np
from PIL import Image
import torchvision.transforms as T
import logging

# GhostStack: CV Layer - Adversarial Patch Generator (Digital PoC)
# 
# This script generates a simple adversarial patch designed to suppress 
# 'person' detections in a YOLOv8 model. It uses a basic gradient descent 
# approach to optimize patch pixels to minimize the model's confidence scores.

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [PATCH_GEN] - %(message)s')

class PatchOptimizer:
    def __init__(self, model_name='yolov8n.pt', patch_size=100):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = YOLO(model_name).model.to(self.device)
        self.model.eval()
        self.patch_size = patch_size
        
        # Initialize a random patch
        self.patch = torch.rand((3, patch_size, patch_size), requires_grad=True, device=self.device)
        self.optimizer = torch.optim.Adam([self.patch], lr=0.01)

    def optimize(self, target_img_path, iterations=100):
        logging.info(f"[*] Starting patch optimization (with EOT) on {target_img_path}...")
        
        # Load and preprocess image
        img = Image.open(target_img_path).convert('RGB').resize((640, 640))
        img_tensor = T.ToTensor()(img).to(self.device).unsqueeze(0)

        for i in range(iterations):
            self.optimizer.zero_grad()
            
            # EOT: Random Transformations for the patch
            # Apply rotation and brightness jitter to the patch before placement
            trans_patch = self.patch.clone()
            if np.random.rand() > 0.5:
                angle = np.random.uniform(-15, 15)
                trans_patch = T.functional.rotate(trans_patch, angle)
            
            jitter = T.ColorJitter(brightness=0.2, contrast=0.2)
            trans_patch = jitter(trans_patch)

            # Place transformed patch on the image
            adv_img = img_tensor.clone()
            adv_img[:, :, :self.patch_size, :self.patch_size] = trans_patch
            
            # Forward pass through YOLOv8
            # YOLOv8 returns a list of tensors for different tasks
            # We target the objectness/class confidence scores
            output = self.model(adv_img)
            
            # Loss: Minimize the maximum confidence score in the output
            # (Simplified: Targetting the confidence scores in the output tensor)
            # YOLOv8 output structure: [1, 84, 8400] for nano
            # Classes like 'person' are at index 0 in the 80 classes
            confs = output[0][4:, :] # Take all class confidences
            loss = torch.max(confs) 
            
            loss.backward()
            self.optimizer.step()
            
            # Clamp patch to [0, 1]
            with torch.no_grad():
                self.patch.clamp_(0, 1)

            if i % 10 == 0:
                logging.info(f"    Iteration {i}: Loss = {loss.item():.4f}")

        logging.info("[+] Optimization complete.")
        self.save_patch()

    def save_patch(self, path='cv_adversarial/patches/adv_patch.png'):
        patch_img = T.ToPILImage()(self.patch.cpu())
        patch_img.save(path)
        logging.info(f"[+] Adversarial patch saved to {path}")

if __name__ == "__main__":
    # Note: Requires a target image to optimize against
    # Usage: python3 patch_generator.py <target_image.jpg>
    import sys
    if len(sys.argv) > 1:
        opt = PatchOptimizer()
        opt.optimize(sys.argv[1])
    else:
        logging.error("Please provide a target image path: python3 patch_generator.py test.jpg")
