"""CLI 模块测试"""

import re
from pathlib import Path
from unittest.mock import MagicMock, patch

from z_image.cli import ASPECT_RATIOS, parse_resolution


def test_parse_resolution_with_explicit_resolution():
    """测试自定义分辨率解析"""
    assert parse_resolution(None, "1024x768") == (1024, 768)
    assert parse_resolution(None, "768x1344") == (768, 1344)
    assert parse_resolution("16:9", "512x512") == (512, 512)  # resolution 优先


def test_parse_resolution_with_ratio():
    """测试宽高比解析"""
    assert parse_resolution("16:9", None) == (1344, 768)
    assert parse_resolution("9:16", None) == (768, 1344)
    assert parse_resolution("1:1", None) == (1024, 1024)
    assert parse_resolution("4:3", None) == (1152, 896)


def test_parse_resolution_default():
    """测试默认分辨率"""
    assert parse_resolution(None, None) == (1024, 1024)


def test_aspect_ratios_defined():
    """验证所有预设宽高比都已定义"""
    expected_ratios = ["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3"]
    for ratio in expected_ratios:
        assert ratio in ASPECT_RATIOS


def test_output_filename_format():
    """验证输出文件名格式: hhmmss_<seed>_nbp.png"""
    pattern = r"^\d{6}_\d+_nbp\.png$"
    assert re.match(pattern, "143052_42_nbp.png")
    assert re.match(pattern, "000000_1234567890_nbp.png")
    assert not re.match(pattern, "14305_42_nbp.png")  # 时间格式错误
    assert not re.match(pattern, "143052_42.png")  # 缺少 _nbp


def test_generate_image_calls_mps_sync(tmp_path: Path):
    """验证 generate_image 调用 torch.mps.synchronize() 以防止黑色图像"""
    from z_image.generator import generate_image

    mock_image = MagicMock()
    mock_pipe_result = MagicMock()
    mock_pipe_result.images = [mock_image]
    mock_pipe = MagicMock(return_value=mock_pipe_result)

    with patch("z_image.generator.torch.mps.synchronize") as mock_sync:
        with patch("z_image.generator.torch.Generator"):
            with patch("z_image.generator.torch.randint", return_value=MagicMock(item=lambda: 12345)):
                generate_image(
                    pipe=mock_pipe,
                    prompt="test prompt",
                    width=512,
                    height=512,
                    seed=42,
                    output_dir=tmp_path,
                )

        mock_sync.assert_called_once()
