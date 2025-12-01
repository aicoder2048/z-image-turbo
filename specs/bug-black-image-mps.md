# Bug: Z-Image float16 导致黑色图像

## Bug Description
使用 Z-Image-Turbo 图像生成器在 MacBook Pro M2 Max 上运行时，生成的图像是纯黑色的。用户执行 `uv run z-image -p '山水风景'` 后，输出的图像文件是一张完全黑色的图像（文件大小仅 3.1KB，正常应为数 MB）。

**预期行为**：生成一张与 prompt "山水风景" 相关的图像
**实际行为**：生成的图像是纯黑色的（RGB 全为 0）

## Problem Statement
Z-Image-Turbo 模型在 float16 精度下推理会产生 NaN (Not a Number) latents，导致输出全黑图像。这是一个 [已知问题](https://github.com/Tongyi-MAI/Z-Image/issues/14)，影响多种 GPU 架构。

## Solution Statement
将模型加载时的 `torch_dtype` 从 `torch.float16` 改为 `torch.float32`。虽然 float32 推理速度较慢，但这是目前唯一可靠的解决方案。

## Steps to Reproduce
1. 在 MacBook Pro M2 Max 上安装项目：`uv sync`
2. 确保模型已下载：`uv run z-image --download-only`
3. 运行图像生成：`uv run z-image -p '山水风景'`
4. 查看生成的图像 → 图像是黑色的，文件大小异常小

## Root Cause Analysis
**根本原因**：Z-Image 模型在 float16 精度下推理会产生 NaN latents

根据 [Z-Image GitHub Issue #14](https://github.com/Tongyi-MAI/Z-Image/issues/14)，Z-Image-Turbo 模型在 float16 精度下会因数值不稳定产生 NaN (Not a Number) 值。这些 NaN 值传播到整个推理过程，最终导致全黑图像输出。

**关键发现**：
- 模型文件本身存储为 **float32** 格式
- 当指定 `torch_dtype=torch.float16` 时，PyTorch 会将 float32 权重向下转换 (downcast) 为 float16
- 这个转换或后续推理中产生了数值不稳定（NaN）
- 不需要重新下载模型，只需保持原始 float32 精度即可

**问题代码**：
```python
pipe = ZImagePipeline.from_pretrained(
    model_path,
    torch_dtype=torch.float16,  # 向下转换导致 NaN latents
    ...
)
```

**修复后代码**：
```python
pipe = ZImagePipeline.from_pretrained(
    model_path,
    torch_dtype=torch.float32,  # 保持原始精度，避免 NaN
    ...
)
```

## Relevant Files
用于修复此 bug 的文件：

- `src/z_image/generator.py` - 图像生成逻辑所在文件，需要修改 `load_pipeline()` 函数中的 `torch_dtype` 参数

## Step by Step Tasks

### 1. 修改 generator.py 使用 float32

- 在 `load_pipeline()` 函数中，将 `torch_dtype=torch.float16` 改为 `torch_dtype=torch.float32`
- 代码修改位置：`src/z_image/generator.py:25`

### 2. 运行验证命令

- 运行所有测试确保无回归
- 手动运行图像生成验证修复

## Validation Commands

- `uv run pytest tests/` - 运行所有测试，确保无回归
- `uv run z-image -p '山水风景' --seed 42` - 验证生成的图像不再是黑色（用固定 seed 便于复现）

## Resolution

**状态**：已修复 ✅

**修改的文件**：
- `src/z_image/generator.py:25` - 将 `torch_dtype=torch.float16` 改为 `torch_dtype=torch.float32`

**验证结果**：
- 生成的图像正常显示，不再是黑色
- 文件大小正常（数 MB）

## Notes
- 使用 float32 推理会比 float16 慢，但这是 Z-Image 模型目前唯一可靠的解决方案
- 模型文件本身是 float32 存储，所以不需要重新下载模型
- 即使下载 fp16 variant 的模型（如果存在），float16 推理仍然会产生黑色图像，因为问题在于模型架构对 float16 数值不稳定
- 参考资料：
  - [Z-Image GitHub Issue #14: FP16 inference produces black images](https://github.com/Tongyi-MAI/Z-Image/issues/14)
  - [Stack Overflow: Black images on M1 Pro](https://stackoverflow.com/questions/75987248/black-images-or-memory-issue-with-hugging-face-stablediffusion-pipleline-m1-pro)
