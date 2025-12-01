# Diffusers — 常见错误与解决

## 1. MPS: out of memory

解决：

```python
pipe.enable_vae_slicing()
pipe.enable_xformers_memory_efficient_attention()
```

## 2. dtype 不匹配

```
RuntimeError: expected dtype float16 but got float32
```

解决：

* 统一 dtype：

```python
torch_dtype=torch.float16
```

## 3. 权重未下载完全

删除缓存：

```bash
rm -rf ~/.cache/huggingface/hub
```

## 4. controlnet 输入尺寸错误

控制图片必须与生成尺寸一致。
