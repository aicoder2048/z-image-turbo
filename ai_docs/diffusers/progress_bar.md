# Diffusers — 展示下载进度 & 推理进度条

Diffusers 默认使用 `tqdm` 展示进度。

## 1. 下载模型时的进度显示

`from_pretrained()` 自动显示：

```
Downloading (…)main/model.safetensors: 100%
```

## 2. 关闭下载进度条

```python
from huggingface_hub import hf_hub_download
hf_hub_download(..., tqdm_class=None)
```

## 3. 推理进度条

### 显示进度条

```python
pipe.enable_progress_bar()
```

### 隐藏进度条

```python
pipe.disable_progress_bar()
```

## 4. 自定义进度回调

```python
def callback(step, timestep, latents):
    print("Step:", step)

pipe(
    prompt="a cat astronaut",
    callback=callback,
    callback_steps=5
)
```
