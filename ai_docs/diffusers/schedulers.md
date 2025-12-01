# Diffusers — Scheduler 调度器

调度器控制采样路径，常影响画面风格、锐度、速度。

## 更换调度器

```python
from diffusers import EulerAncestralDiscreteScheduler

pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(
    pipe.scheduler.config
)
```

## 常用调度器对比

| 调度器                    | 特点       |
| ---------------------- | -------- |
| EulerAncestralDiscrete | 较锐利、速度快  |
| DPMSolverMultistep     | 高质量、广泛使用 |
| DDIM                   | 稳定、偏柔和   |
| HeunDiscreteScheduler  | 柔和、连续感强  |
| KDPM2 Ancestral        | 细节强      |

## 推荐配置

* SD1.5：`Euler A`、`DPMSolverMultistep`
* SDXL：`DPMSolverMultistep`
