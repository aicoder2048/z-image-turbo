"""CLI 模块测试"""

import json
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from z_image.cli import (
    ASPECT_RATIOS,
    get_interactive_help,
    load_prompts,
    load_prompts_from_json,
    load_prompts_from_text,
    parse_interactive_input,
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


# ============ Device Resolution Tests ============


def test_resolve_device_cuda_available():
    """测试 CUDA 可用时的设备选择"""
    from z_image.generator import resolve_device

    with patch("z_image.generator.torch.cuda.is_available", return_value=True):
        with patch("z_image.generator.torch.backends.mps.is_available", return_value=False):
            with patch("z_image.generator.platform.system", return_value="Windows"):
                # auto 模式下优先选择 CUDA
                assert resolve_device("auto", 1024, 1024) == "cuda"
                # 显式指定 cuda
                assert resolve_device("cuda", 1024, 1024) == "cuda"
                # 显式指定 cpu
                assert resolve_device("cpu", 1024, 1024) == "cpu"


def test_resolve_device_cuda_not_available():
    """测试 CUDA 不可用时显式指定 cuda 应报错"""
    from z_image.generator import resolve_device

    with patch("z_image.generator.torch.cuda.is_available", return_value=False):
        with patch("z_image.generator.torch.backends.mps.is_available", return_value=False):
            with patch("z_image.generator.platform.system", return_value="Windows"):
                with pytest.raises(ValueError, match="CUDA 不可用"):
                    resolve_device("cuda", 1024, 1024)


def test_resolve_device_auto_fallback_to_cpu():
    """测试无 GPU 时 auto 模式回退到 CPU"""
    from z_image.generator import resolve_device

    with patch("z_image.generator.torch.cuda.is_available", return_value=False):
        with patch("z_image.generator.torch.backends.mps.is_available", return_value=False):
            with patch("z_image.generator.platform.system", return_value="Linux"):
                assert resolve_device("auto", 1024, 1024) == "cpu"


def test_resolve_device_mps_on_mac():
    """测试 Mac 上 MPS 设备选择"""
    from z_image.generator import resolve_device

    with patch("z_image.generator.torch.cuda.is_available", return_value=False):
        with patch("z_image.generator.torch.backends.mps.is_available", return_value=True):
            with patch("z_image.generator.platform.system", return_value="Darwin"):
                # auto 模式下选择 MPS
                assert resolve_device("auto", 1024, 1024) == "mps"
                # 显式指定 mps
                assert resolve_device("mps", 1024, 1024) == "mps"


def test_resolve_device_cuda_priority_over_mps():
    """测试 CUDA 优先级高于 MPS（理论上不会同时可用，但测试逻辑正确性）"""
    from z_image.generator import resolve_device

    with patch("z_image.generator.torch.cuda.is_available", return_value=True):
        with patch("z_image.generator.torch.backends.mps.is_available", return_value=True):
            with patch("z_image.generator.platform.system", return_value="Darwin"):
                # auto 模式下 CUDA 优先
                assert resolve_device("auto", 1024, 1024) == "cuda"


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


# ============ Keyboard Interrupt Tests ============


def test_keyboard_interrupt_with_no_completed_images(capsys):
    """测试在没有完成任何图像时按 Ctrl+C 的处理"""
    from z_image.__main__ import main

    with patch("z_image.__main__.parse_args") as mock_args:
        mock_args.return_value = MagicMock(
            model_dir="models",
            output_dir="output",
            ratio="1:1",
            resolution=None,
            device="cpu",
            force_mps=False,
            download_only=False,
            interactive=False,
            prompts_file=None,
            prompt="test prompt",
            count=3,
            seed=42,
        )

        with patch("z_image.__main__.resolve_device", return_value="cpu"):
            with patch("z_image.__main__.download_model", return_value=Path("models/test")):
                with patch("z_image.__main__.load_pipeline", return_value=(MagicMock(), "cpu")):
                    with patch("z_image.__main__.sanitize_prompt", return_value="test prompt"):
                        with patch("z_image.__main__.is_prompt_problematic", return_value=False):
                            # generate_image 立即抛出 KeyboardInterrupt
                            with patch("z_image.__main__.generate_image", side_effect=KeyboardInterrupt):
                                with pytest.raises(SystemExit) as exc_info:
                                    main()

                                assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "用户中断" in captured.out
    # 没有完成任何图像，不应显示进度
    assert "已完成" not in captured.out


def test_keyboard_interrupt_with_some_completed_images(capsys, tmp_path: Path):
    """测试在完成部分图像后按 Ctrl+C 的处理"""
    from z_image.__main__ import main

    call_count = 0

    def mock_generate_image(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count >= 3:
            raise KeyboardInterrupt
        # 返回模拟的图像结果
        mock_image = MagicMock()
        return mock_image, 12345, tmp_path / f"test_{call_count}.png"

    with patch("z_image.__main__.parse_args") as mock_args:
        mock_args.return_value = MagicMock(
            model_dir="models",
            output_dir=str(tmp_path),
            ratio="1:1",
            resolution=None,
            device="cpu",
            force_mps=False,
            download_only=False,
            interactive=False,
            prompts_file=None,
            prompt="test prompt",
            count=5,
            seed=42,
        )

        with patch("z_image.__main__.resolve_device", return_value="cpu"):
            with patch("z_image.__main__.download_model", return_value=Path("models/test")):
                with patch("z_image.__main__.load_pipeline", return_value=(MagicMock(), "cpu")):
                    with patch("z_image.__main__.sanitize_prompt", return_value="test prompt"):
                        with patch("z_image.__main__.is_prompt_problematic", return_value=False):
                            with patch("z_image.__main__.generate_image", side_effect=mock_generate_image):
                                with pytest.raises(SystemExit) as exc_info:
                                    main()

                                assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "用户中断" in captured.out


# ============ Interactive Mode Tests ============


class TestParseInteractiveInput:
    """Tests for parse_interactive_input function."""

    def test_empty_input(self):
        """测试空输入"""
        result = parse_interactive_input("")
        assert result["command"] == "empty"

        result = parse_interactive_input("   ")
        assert result["command"] == "empty"

    def test_quit_command(self):
        """测试退出命令"""
        assert parse_interactive_input("quit")["command"] == "quit"
        assert parse_interactive_input("QUIT")["command"] == "quit"
        assert parse_interactive_input("exit")["command"] == "quit"
        assert parse_interactive_input("EXIT")["command"] == "quit"

    def test_help_command(self):
        """测试帮助命令"""
        assert parse_interactive_input("help")["command"] == "help"
        assert parse_interactive_input("HELP")["command"] == "help"

    def test_status_command(self):
        """测试状态命令"""
        assert parse_interactive_input("status")["command"] == "status"
        assert parse_interactive_input("STATUS")["command"] == "status"

    def test_direct_prompt_input(self):
        """测试直接输入 prompt（不带选项）"""
        result = parse_interactive_input("一只猫在太空中")
        assert result["command"] == "generate"
        assert result["prompt"] == "一只猫在太空中"
        assert result["ratio"] == "1:1"
        assert result["count"] == 1

    def test_prompt_with_quotes(self):
        """测试带引号的 prompt"""
        result = parse_interactive_input('"a cat in space"')
        assert result["command"] == "generate"
        assert result["prompt"] == "a cat in space"

    def test_prompt_with_p_option(self):
        """测试使用 -p 选项"""
        result = parse_interactive_input('-p "山水风景"')
        assert result["command"] == "generate"
        assert result["prompt"] == "山水风景"

    def test_prompt_with_ratio(self):
        """测试带宽高比选项"""
        result = parse_interactive_input('-p "test" -r 16:9')
        assert result["command"] == "generate"
        assert result["prompt"] == "test"
        assert result["ratio"] == "16:9"

    def test_prompt_with_resolution(self):
        """测试带分辨率选项"""
        result = parse_interactive_input('-p "test" --resolution 1920x1080')
        assert result["command"] == "generate"
        assert result["prompt"] == "test"
        assert result["resolution"] == "1920x1080"

    def test_prompt_with_count(self):
        """测试带数量选项"""
        result = parse_interactive_input('-p "test" -n 3')
        assert result["command"] == "generate"
        assert result["prompt"] == "test"
        assert result["count"] == 3

    def test_prompt_with_seed(self):
        """测试带种子选项"""
        result = parse_interactive_input('-p "test" -s 42')
        assert result["command"] == "generate"
        assert result["prompt"] == "test"
        assert result["seed"] == 42

    def test_prompt_with_all_options(self):
        """测试带所有选项"""
        result = parse_interactive_input('-p "风景画" -r 16:9 -n 2 -s 123')
        assert result["command"] == "generate"
        assert result["prompt"] == "风景画"
        assert result["ratio"] == "16:9"
        assert result["count"] == 2
        assert result["seed"] == 123

    def test_invalid_ratio(self):
        """测试无效的宽高比"""
        result = parse_interactive_input('-p "test" -r invalid')
        assert result["command"] == "error"
        assert "无效的宽高比" in result["error"]

    def test_missing_prompt_value(self):
        """测试缺少 prompt 值"""
        result = parse_interactive_input("-p")
        assert result["command"] == "error"
        assert "需要参数" in result["error"]

    def test_missing_prompt_option(self):
        """测试缺少 prompt 选项"""
        result = parse_interactive_input("-r 16:9")
        assert result["command"] == "error"
        assert "缺少 prompt" in result["error"]

    def test_unknown_option(self):
        """测试未知选项"""
        result = parse_interactive_input("-p test --unknown value")
        assert result["command"] == "error"
        assert "未知选项" in result["error"]

    def test_chinese_prompt_preserved(self):
        """测试中文 prompt 被正确保留"""
        result = parse_interactive_input("一只可爱的猫咪在花园里玩耍")
        assert result["command"] == "generate"
        assert result["prompt"] == "一只可爱的猫咪在花园里玩耍"

    def test_prompts_file_option(self):
        """测试 -f 选项"""
        result = parse_interactive_input('-f prompts.json')
        assert result["command"] == "generate"
        assert result["prompts_file"] == "prompts.json"
        assert result["prompt"] is None

    def test_prompts_file_with_options(self):
        """测试 -f 带其他选项"""
        result = parse_interactive_input('-f prompts.txt -r 16:9 -n 2')
        assert result["command"] == "generate"
        assert result["prompts_file"] == "prompts.txt"
        assert result["ratio"] == "16:9"
        assert result["count"] == 2

    def test_prompts_file_long_option(self):
        """测试 --prompts-file 长选项"""
        result = parse_interactive_input('--prompts-file input/prompts.json')
        assert result["command"] == "generate"
        assert result["prompts_file"] == "input/prompts.json"

    def test_prompt_and_file_conflict(self):
        """测试 -p 和 -f 不能同时使用"""
        result = parse_interactive_input('-p "test" -f prompts.json')
        assert result["command"] == "error"
        assert "-p 和 -f 不能同时使用" in result["error"]

    def test_prompts_file_missing_value(self):
        """测试 -f 缺少参数"""
        result = parse_interactive_input("-f")
        assert result["command"] == "error"
        assert "需要参数" in result["error"]

    def test_force_mps_option(self):
        """测试 --force-mps 选项"""
        result = parse_interactive_input('-p "test" --force-mps')
        assert result["command"] == "generate"
        assert result["prompt"] == "test"
        assert result["force_mps"] is True

    def test_force_mps_with_resolution(self):
        """测试 --force-mps 带高分辨率"""
        result = parse_interactive_input('-p "test" --resolution 1920x1080 --force-mps')
        assert result["command"] == "generate"
        assert result["resolution"] == "1920x1080"
        assert result["force_mps"] is True

    def test_default_force_mps_is_false(self):
        """测试默认 force_mps 为 False"""
        result = parse_interactive_input('-p "test"')
        assert result["force_mps"] is False


class TestGetInteractiveHelp:
    """Tests for get_interactive_help function."""

    def test_help_contains_commands(self):
        """测试帮助信息包含命令说明"""
        help_text = get_interactive_help()
        assert "help" in help_text
        assert "quit" in help_text
        assert "exit" in help_text
        assert "status" in help_text

    def test_help_contains_options(self):
        """测试帮助信息包含选项说明"""
        help_text = get_interactive_help()
        assert "-p" in help_text
        assert "-f" in help_text
        assert "-r" in help_text
        assert "-n" in help_text
        assert "-s" in help_text
        assert "--force-mps" in help_text

    def test_help_contains_examples(self):
        """测试帮助信息包含示例"""
        help_text = get_interactive_help()
        assert "示例" in help_text
