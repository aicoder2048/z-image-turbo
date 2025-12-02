"""模型下载模块 - 支持断点续传和进度显示"""

from pathlib import Path

from huggingface_hub import snapshot_download

MODEL_ID = "Tongyi-MAI/Z-Image-Turbo"
DEFAULT_MODELS_DIR = Path("models")


def download_model(
    model_id: str = MODEL_ID,
    cache_dir: Path = DEFAULT_MODELS_DIR,
) -> Path:
    """
    下载模型到指定目录，支持断点续传和进度显示。

    Args:
        model_id: HuggingFace 模型 ID
        cache_dir: 模型缓存目录

    Returns:
        本地模型路径
    """
    cache_dir.mkdir(parents=True, exist_ok=True)

    local_path = snapshot_download(
        repo_id=model_id,
        cache_dir=str(cache_dir),
        # resume_download 已弃用，huggingface_hub 1.0+ 默认自动续传
        # tqdm 进度条默认启用
    )
    return Path(local_path)
