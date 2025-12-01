# 📘 **ZImagePipeline 非官方完整文档（2025）**

* ZImagePipeline 的所有参数说明
* 推理输入/输出规范
* Z-Image 特有特性
* 支持的优化 backend
* Apple Silicon/MPS 使用说明
* CUDA 说明
* 最佳实践（Best Practices）
* 完整代码模板

---

# 1. 简介（Overview）

`ZImagePipeline` 是由阿里通义实验室（Tongyi-MAI）为 Diffusers 提供的单流 DiT（S3-DiT）文本到图像生成 Pipeline。

它支持：

* Z-Image Turbo（8 NFE）⚡
* 精确中英文渲染
* 长 prompt 理解
* 高速推理（Flash Attention）
* bfloat16 运算
* 指令对齐（Instruction following）

此 pipeline 的 API 与 StableDiffusionPipeline 基本一致，但有以下区别：

| 特性             | ZImagePipeline                  | SDXL     | 注释              |
| -------------- | ------------------------------- | -------- | --------------- |
| Text encoder   | Qwen2-VL tokenizer + text tower | CLIP     | 支持中文更好          |
| Model backbone | S3-DiT (Single-Stream DiT)      | UNet     | 更快、更现代          |
| Guidance scale | `0.0` 固定                        | 通常 6–9   | Turbo 模型不使用 CFG |
| Steps          | 固定 8~9                          | 通常 20–50 | 超高速生成           |
| Attention      | 支持 Flash2/Flash3                | 仅部分模型支持  | Turbo 做了优化      |

---

# 2. `ZImagePipeline.from_pretrained()` 文档

```python
ZImagePipeline.from_pretrained(
    pretrained_model_name_or_path,
    *,
    torch_dtype=None,
    revision=None,
    subfolder=None,
    low_cpu_mem_usage=True,
    use_safetensors=True,
    cache_dir=None,
    local_files_only=False,
    resume_download=False,
    force_download=False,
    proxies=None,
    token=None
)
```

下面是逐项解释：

---

## **参数详解**

### **pretrained_model_name_or_path**

字符串 | 必填

可以是：

* HuggingFace 模型 ID
  `"Tongyi-MAI/Z-Image-Turbo"`
* 本地模型目录
  `"/Users/sean/zimage_cache/Z-Image-Turbo"`

---

### **torch_dtype**

选择模型权重类型

推荐：

| 设备                       | 推荐 dtype         |
| ------------------------ | ---------------- |
| NVIDIA GPU               | `torch.bfloat16` |
| Apple Silicon (M1/M2/M3) | `torch.float16`  |
| CPU                      | `torch.float32`  |

示例：

```python
torch_dtype=torch.bfloat16
```

---

### **low_cpu_mem_usage**

是否分段加载模型以减少内存占用。

Z-Image 参数较大（6B），建议：

```python
low_cpu_mem_usage=True
```

---

### **cache_dir**

指定模型下载目录。

示例：

```python
cache_dir="/Users/sean/zimage_models"
```

---

### **local_files_only**

仅从本地加载，不联网。

```python
local_files_only=True
```

---

### **force_download**

强制重新下载模型。

---

## **返回值**

`ZImagePipeline` 实例，包含：

* `pipe.text_encoder`（Qwen2-VL 文本塔）
* `pipe.transformer`（S3-DiT backbone）
* `pipe.vae`（AutoEncoder KL）
* `pipe.tokenizer`
* `pipe.scheduler`（DMD 专用 scheduler）

---

# 3. `.to(device)` 说明

Z-ImagePipeline 支持：

| device   | 是否支持 | 备注            |
| -------- | ---- | ------------- |
| `"cuda"` | ✔️   | 全速            |
| `"mps"`  | ✔️   | Apple Silicon |
| `"cpu"`  | ✔️   | 慢             |

例：

```python
pipe.to("mps")  # Apple Silicon
pipe.to("cuda") # NVIDIA
```

---

# 4. Attention Backend

你可以切换 Flash Attention：

```python
pipe.transformer.set_attention_backend("flash")      # Flash-2
pipe.transformer.set_attention_backend("_flash_3")   # Flash-3
```

---

# 5. 推理接口（call）

```python
pipe(
    prompt: str,
    *,
    height: int = 1024,
    width: int = 1024,
    num_inference_steps: int = 9,
    guidance_scale: float = 0.0,
    generator=None,
)
```

### 参数说明

| 参数                  | 默认   | 说明              |
| ------------------- | ---- | --------------- |
| prompt              | 必填   | 文本 prompt（支持中英） |
| height              | 1024 | 生成图像高度          |
| width               | 1024 | 生成图像宽度          |
| num_inference_steps | 9    | DMD few-step    |
| guidance_scale      | 0.0  | Turbo 固定为 `0.0` |
| generator           | None | 控制随机 seed       |

例：

```python
image = pipe(
    prompt=prompt,
    height=1024,
    width=1024,
    num_inference_steps=9,
    guidance_scale=0.0,
    generator=torch.Generator("mps").manual_seed(42),
).images[0]
```

输出：

* `image` → PIL Image

---

# 6. Z-Image Turbo 推荐配置（Best Practice）

## ① dtype

| GPU           | 推荐 dtype |
| ------------- | -------- |
| NVIDIA        | bfloat16 |
| Apple Silicon | float16  |
| CPU           | float32  |

---

## ② steps

Turbo 固定：

```python
num_inference_steps=9  # 实际8 forward
```

---

## ③ guidance

Turbo 必须：

```python
guidance_scale=0.0
```

---

## ④ prompt engineering

短 prompt（10–40 tokens）效果最好。
长 prompt 也能处理，但 Turbo 是速推模型。

---

# 7. Apple Silicon 特别说明

M1/M2/M3 使用：

```python
pipe.to("mps")
```

最佳 dtype：

```python
torch_dtype=torch.float16
```

不支持 FlashAttention（Metal 无 Flash）。

推理速度约：

* M2 Max：每张 ~2.5–4 秒（1024×1024）
* M3 Max：可达 ~1.6–2.0 秒

---

# 8. 完整示例代码（可直接运行）

```python
import torch
from diffusers import ZImagePipeline

model_id = "Tongyi-MAI/Z-Image-Turbo"

pipe = ZImagePipeline.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16,
    low_cpu_mem_usage=True,
)

pipe.to("cuda")  # Apple Silicon 用 "mps"

prompt = "A young Chinese woman in red hanfu with phoenix hairpin, vivid neon lighting."

image = pipe(
    prompt=prompt,
    height=1024,
    width=1024,
    num_inference_steps=9,
    guidance_scale=0.0,
    generator=torch.Generator("cuda").manual_seed(42),
).images[0]

image.save("output.png")
```

---

# 9. Z-Image Turbo 目录结构

`from_pretrained` 加载的模型目录应包含：

```
config.json
model_index.json
tokenizer/
text_encoder/
vae/
transformer/
scheduler/
```

这与 ComfyUI 的 `.safetensors` checkpoint **完全不同**。
