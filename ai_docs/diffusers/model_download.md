# Diffusers — 下载模型（含下载进度）

Diffusers 通过 `from_pretrained()` 下载模型权重。

## 下载 Stable Diffusion v1.5

```python
from diffusers import StableDiffusionPipeline
import torch

pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16
)
pipe = pipe.to("mps")
```

## 下载 SDXL

```python
from diffusers import StableDiffusionXLPipeline
pipe = StableDiffusionXLPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=torch.float16
).to("mps")
```

## 下载 ControlNet + SD1.5

```python
from diffusers import ControlNetModel, StableDiffusionControlNetPipeline

controlnet = ControlNetModel.from_pretrained(
    "lllyasviel/control_v11p_sd15_canny"
)

pipe = StableDiffusionControlNetPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    controlnet=controlnet
)
```

所有模型会自动缓存至：

```
~/.cache/huggingface/hub
```
