# Chore: Add Windows CUDA GPU Support

## Chore Description
Currently, the z-image-turbo tool only supports Mac MPS (Metal Performance Shaders) for GPU acceleration. On non-Mac systems (Windows/Linux), it falls back to CPU mode. This chore adds CUDA GPU support for Windows users with NVIDIA graphics cards, enabling much faster image generation.

Key changes needed:
1. Detect CUDA availability on Windows/Linux systems
2. Add "cuda" as a valid device option in CLI
3. Update device resolution logic to support CUDA
4. Use appropriate dtype (bfloat16) for CUDA for optimal performance
5. Handle CUDA-specific synchronization

## Relevant Files
Use these files to resolve the chore:

- `src/z_image/generator.py` - Contains device selection logic (`resolve_device`), pipeline loading (`load_pipeline`), and image generation (`generate_image`). This is the main file that needs CUDA support.
- `src/z_image/cli.py` - Contains CLI argument parsing. Need to add "cuda" to device choices.
- `src/z_image/__main__.py` - Contains main entry point with device info display. Need to update messages for CUDA.
- `tests/test_cli.py` - Add tests for CUDA device selection logic.
- `README.md` - Update documentation for Windows CUDA support.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update CLI Device Choices
- In `src/z_image/cli.py`, update `--device` argument choices from `["auto", "mps", "cpu"]` to `["auto", "cuda", "mps", "cpu"]`
- Update help text to include CUDA option

### Step 2: Update Device Resolution Logic
- In `src/z_image/generator.py`, modify `resolve_device()` function:
  - Check for CUDA availability using `torch.cuda.is_available()`
  - For "auto" mode: prefer CUDA on Windows/Linux if available, MPS on Mac, fallback to CPU
  - For "cuda" mode: return "cuda" if available, raise error otherwise
  - Keep existing MPS logic for Mac
  - Note: CUDA doesn't have the same resolution limits as MPS

### Step 3: Update Pipeline Loading for CUDA
- In `src/z_image/generator.py`, modify `load_pipeline()` function:
  - Use `torch.bfloat16` dtype for CUDA (better performance than float32)
  - Keep `torch.float32` for MPS and CPU (MPS has issues with float16/bfloat16)
  - CUDA doesn't need attention slicing (has better memory management)

### Step 4: Update Image Generation for CUDA
- In `src/z_image/generator.py`, modify `generate_image()` function:
  - Add CUDA synchronization using `torch.cuda.synchronize()` after generation
  - Keep existing MPS synchronization

### Step 5: Update Main Entry Point
- In `src/z_image/__main__.py`, update device info display to handle CUDA
- Remove MPS-specific warnings when using CUDA (no resolution limit)

### Step 6: Add Unit Tests
- Add test for `resolve_device()` with CUDA available (mock)
- Add test for `resolve_device()` with CUDA not available
- Add test for CUDA as explicit device choice

### Step 7: Update README Documentation
- Add Windows CUDA installation section
- Update device options table
- Add performance comparison including CUDA

### Step 8: Run Validation Commands
- Run all tests to ensure no regressions

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest tests/ -v` - Run all tests to validate the chore is complete with zero regressions
- `uv run z-image --help` - Verify CUDA appears in device choices
- `uv run python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"` - Check CUDA detection works

## Notes
- CUDA support requires PyTorch with CUDA backend installed (`pip install torch --index-url https://download.pytorch.org/whl/cu121`)
- The current PyTorch installation may be CPU-only; users need to install CUDA-enabled PyTorch separately
- bfloat16 is preferred for CUDA as it provides better performance without the precision issues of float16
- CUDA doesn't have the 2^32 byte NDArray limitation that MPS has, so no resolution limits needed
- On systems without CUDA, the "cuda" device option should gracefully fail with a helpful message
