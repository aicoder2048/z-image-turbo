# Diffusers — Pipeline 核心结构

所有 Pipeline 的父类：

```python
from diffusers import DiffusionPipeline
```

典型组件：

| 组件             | 功能                 |
| -------------- | ------------------ |
| unet           | 主推理网络              |
| vae            | 编码/解码 latent space |
| text_encoder   | 文本编码               |
| tokenizer      | 文本 tokenizer       |
| scheduler      | 调度器                |
| controlnet（可选） | 控制条件模块             |
| safety_checker | 安全检查               |

## 最小推理示例

```python
image = pipe(
    prompt="a dragon flying over mountains",
    num_inference_steps=30,
    guidance_scale=7.5
).images[0]
```

## 设置随机种子

```python
import torch
generator = torch.Generator("mps").manual_seed(1234)

image = pipe(prompt="robot cat", generator=generator).images[0]
```
