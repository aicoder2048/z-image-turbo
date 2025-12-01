# Diffusers — 安装

推荐环境：

* macOS / Linux / Windows
* Python ≥ 3.9
* PyTorch ≥ 2.1
* MacBook Pro Apple Silicon（支持 MPS 加速）

## 1. 安装基础依赖

```bash
pip install diffusers transformers accelerate safetensors
```

Diffusers 某些模型依赖 xformers：

**Apple Silicon 不需要 xformers**，但可以用 MPS：

```bash
export PYTORCH_ENABLE_MPS_FALLBACK=1
```

## 2. 验证 MPS（Apple Silicon）

```python
import torch
print(torch.backends.mps.is_available())
```

输出 True 即可使用：

```python
pipe = pipe.to("mps")
```
