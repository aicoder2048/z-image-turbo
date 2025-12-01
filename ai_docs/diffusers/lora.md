# Diffusers — LoRA 使用

## 加载 LoRA

```python
pipe.load_lora_weights("/Users/sean/lora/my_lora")
```

## 调整 LoRA 强度（scale）

```python
pipe.set_adapters("my_lora", weights=0.7)
```

## 多 LoRA 叠加

```python
pipe.load_lora_weights("lora1")
pipe.load_lora_weights("lora2")

pipe.set_adapters(["lora1", "lora2"], [0.7, 0.3])
```

## 融合到 UNet（提高推理速度）

```python
pipe.fuse_lora()
```

## 移除

```python
pipe.unfuse_lora()
```
