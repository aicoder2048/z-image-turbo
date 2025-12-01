# Diffusers — 指定模型下载目录（Cache Directory）

可通过环境变量 **HF_HOME** 和 **HUGGINGFACE_HUB_CACHE** 修改默认缓存路径。

## 1. 临时指定（当前 shell）

```bash
export HF_HOME=/Users/sean/hf_cache
export HUGGINGFACE_HUB_CACHE=/Users/sean/hf_cache
```

## 2. 永久指定（写入 ~/.zshrc）

```bash
echo 'export HF_HOME=~/hf_cache' >> ~/.zshrc
echo 'export HUGGINGFACE_HUB_CACHE=~/hf_cache' >> ~/.zshrc
source ~/.zshrc
```

## 3. Python 中指定 cache_dir（最灵活）

```python
pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    cache_dir="/Users/sean/diffusers_models"
)
```

## 4. 检查缓存文件

```bash
ls -lh ~/hf_cache/hub
```
