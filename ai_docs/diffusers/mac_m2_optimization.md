# Diffusers — MacBook Pro M2 Max 优化指南

Apple Silicon GPU = **MPS 加速**

## 1. 启用 MPS

```python
pipe = pipe.to("mps")
```

## 2. FP16 推荐

```python
torch_dtype=torch.float16
```

## 3. MPS Fallback

```bash
export PYTORCH_ENABLE_MPS_FALLBACK=1
```

## 4. 加速文本编码

```python
pipe.enable_model_cpu_offload()
```

## 5. 避免 VAE OOM

```python
pipe.enable_vae_slicing()
pipe.enable_xformers_memory_efficient_attention()
```

## M2 Max 大模型（SDXL）建议

| 设置             | 数值          |
| -------------- | ----------- |
| 分辨率            | ≤ 1024×1024 |
| steps          | 20–35       |
| guidance scale | 5–8         |
