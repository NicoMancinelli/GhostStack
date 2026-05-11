# The Mathematics of Adversarial Patches

GhostStack's CV Layer utilizes "Naturalistic Adversarial Patches" to blind object detectors like YOLOv8. Here is the foundational math behind the PoC.

## 1. The Objective Function
Object detectors aim to minimize a loss function $L(\theta, x, y)$ where $\theta$ are the model weights, $x$ is the input image, and $y$ is the ground truth bounding box.

To create an adversarial patch $p$, we want to *maximize* the loss for the target class (e.g., 'person'), causing the detector to fail. We hold $\theta$ constant and optimize $p$:

$$ p^* = \arg \max_{p} \mathbb{E}_{x \sim X} [ L(\theta, A(p, x, l), y_{target}) ] $$

Where $A(p, x, l)$ is an application function that overlays patch $p$ onto image $x$ at location $l$.

## 2. Expectation over Transformation (EOT)
A digital patch fails in the real world because of lighting, scaling, and rotation. We use EOT to optimize the patch over a distribution of physical transformations $T$:

$$ p^* = \arg \max_{p} \mathbb{E}_{x \sim X, t \sim T} [ L(\theta, A(t(p), x, l), y_{target}) ] $$

In `patch_generator.py`, $t \sim T$ represents our `ColorJitter` and `RandomRotation` applications during the Adam optimization loop. By averaging the gradient updates across these noisy transformations, the resulting patch geometry becomes physically robust.
