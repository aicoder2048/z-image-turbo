"""CLI 模块测试"""

import json
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from z_image.cli import (
    ASPECT_RATIOS,
    load_prompts,
    load_prompts_from_json,
    load_prompts_from_text,
    parse_resolution,
)


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


# ============ Prompt Loading Tests ============


def test_load_prompts_from_json_valid(tmp_path: Path):
    """测试从有效 JSON 文件加载 prompts"""
    json_file = tmp_path / "prompts.json"
    data = [
        {"id": "1", "description": "a cat in space"},
        {"id": "2", "description": "a dog on the beach"},
        {"id": "3", "description": "一只猫在太空中"},
    ]
    json_file.write_text(json.dumps(data), encoding="utf-8")

    result = load_prompts_from_json(json_file)

    assert len(result) == 3
    assert result[0] == "a cat in space"
    assert result[1] == "a dog on the beach"
    assert result[2] == "一只猫在太空中"


def test_load_prompts_from_json_missing_description(tmp_path: Path, capsys):
    """测试缺少 description 字段的 JSON 对象会被跳过"""
    json_file = tmp_path / "prompts.json"
    data = [
        {"id": "1", "description": "valid prompt"},
        {"id": "2", "name": "missing description"},
        {"id": "3", "description": "another valid"},
    ]
    json_file.write_text(json.dumps(data), encoding="utf-8")

    result = load_prompts_from_json(json_file)

    assert len(result) == 2
    assert result[0] == "valid prompt"
    assert result[1] == "another valid"

    captured = capsys.readouterr()
    assert "跳过第 2 项" in captured.out


def test_load_prompts_from_json_empty_array(tmp_path: Path):
    """测试空 JSON 数组"""
    json_file = tmp_path / "prompts.json"
    json_file.write_text("[]", encoding="utf-8")

    result = load_prompts_from_json(json_file)

    assert result == []


def test_load_prompts_from_text_multiline(tmp_path: Path):
    """测试从多行文本文件加载 prompts"""
    txt_file = tmp_path / "prompts.txt"
    txt_file.write_text("a cat in space\na dog on beach\n一只猫\n", encoding="utf-8")

    result = load_prompts_from_text(txt_file)

    assert len(result) == 3
    assert result[0] == "a cat in space"
    assert result[1] == "a dog on beach"
    assert result[2] == "一只猫"


def test_load_prompts_from_text_empty_lines(tmp_path: Path):
    """测试空行会被过滤"""
    txt_file = tmp_path / "prompts.txt"
    txt_file.write_text("prompt one\n\n  \nprompt two\n   \n", encoding="utf-8")

    result = load_prompts_from_text(txt_file)

    assert len(result) == 2
    assert result[0] == "prompt one"
    assert result[1] == "prompt two"


def test_load_prompts_from_text_whitespace_stripped(tmp_path: Path):
    """测试前后空格会被去除"""
    txt_file = tmp_path / "prompts.txt"
    txt_file.write_text("  prompt with spaces  \n\ttabbed prompt\t\n", encoding="utf-8")

    result = load_prompts_from_text(txt_file)

    assert len(result) == 2
    assert result[0] == "prompt with spaces"
    assert result[1] == "tabbed prompt"


def test_load_prompts_dispatcher_json(tmp_path: Path):
    """测试 dispatcher 正确处理 .json 文件"""
    json_file = tmp_path / "test.json"
    json_file.write_text('[{"description": "test prompt"}]', encoding="utf-8")

    result = load_prompts(json_file)

    assert result == ["test prompt"]


def test_load_prompts_dispatcher_txt(tmp_path: Path):
    """测试 dispatcher 正确处理 .txt 文件"""
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("test prompt\n", encoding="utf-8")

    result = load_prompts(txt_file)

    assert result == ["test prompt"]


def test_load_prompts_unsupported_extension(tmp_path: Path):
    """测试不支持的文件扩展名抛出错误"""
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("a,b,c\n", encoding="utf-8")

    with pytest.raises(ValueError, match="不支持的文件格式"):
        load_prompts(csv_file)
