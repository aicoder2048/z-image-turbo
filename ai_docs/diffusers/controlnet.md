# Diffusers — ControlNet

ControlNet 可添加结构化控制输入（如 Canny、Depth、Pose）。

## 示例：Canny ControlNet

```python
from diffusers import (
    ControlNetModel,
    StableDiffusionControlNetPipeline
)
import cv2

controlnet = ControlNetModel.from_pretrained(
    "lllyasviel/control_v11p_sd15_canny"
)

pipe = StableDiffusionControlNetPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    controlnet=controlnet
).to("mps")

canny = cv2.Canny(img, 80, 100)
result = pipe(prompt="robot dog", image=canny).images[0]
```
