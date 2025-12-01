# Diffusers — LoRA 微调（训练）

## 推荐：使用 accelerate

最小训练脚本：

```bash
accelerate launch train_lora.py \
 --pretrained_model_name_or_path=stabilityai/stable-diffusion-xl-base-1.0 \
 --dataset_name=/Users/sean/datasets/cats \
 --rank=8 \
 --output_dir=./lora_output \
 --resolution=1024 \
 --train_batch_size=1 \
 --gradient_accumulation_steps=4 \
 --learning_rate=1e-4 \
 --max_train_steps=2000
```

## LoRA 目录结构

```
lora_output/
 ├─ adapter_config.json
 ├─ adapter_model.safetensors
```

## 加载训练结果

```python
pipe.load_lora_weights("./lora_output")
```
