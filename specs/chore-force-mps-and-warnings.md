# Chore: Add --force-mps flag and improve CPU fallback warnings

## Chore Description
1. Add `--force-mps` flag for advanced users who want to try higher resolutions on MPS despite the known limitations (may crash)
2. Document workarounds for power users in the README (environment variables, experimental options)
3. Add a visible warning when CPU mode is auto-selected due to MPS resolution limits

## Relevant Files
Use these files to resolve the chore:

- `src/z_image/cli.py` - Add the `--force-mps` argument to argparse and update help text
- `src/z_image/generator.py` - Modify `resolve_device()` to handle `force_mps` parameter
- `src/z_image/__main__.py` - Pass `force_mps` flag and display warning when CPU is auto-selected
- `README.md` - Add "Power User Workarounds" section with advanced options

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add --force-mps argument to cli.py

- Add a new `--force-mps` boolean flag argument after the `--device` argument
- Help text should warn users that this bypasses safety checks and may cause crashes
- Update the epilog tips section to mention the new flag

### Step 2: Update resolve_device() in generator.py

- Add `force_mps: bool = False` parameter to `resolve_device()` function
- When `force_mps=True` and `device="auto"`, always return "mps" regardless of resolution
- When `force_mps=True` and `device="mps"`, skip the resolution check (don't raise ValueError)
- Keep the warning logic in `__main__.py` for displaying appropriate messages

### Step 3: Update __main__.py for warnings and force_mps

- Pass `args.force_mps` to `resolve_device()`
- Add a prominent warning (using print with visual markers like `⚠️` or `[WARNING]`) when:
  - CPU mode is auto-selected due to MPS limits
  - force_mps is used with high resolution (warn about potential crash)
- Update the device status line to show when force_mps is active

### Step 4: Add Power User Workarounds section to README.md

- Add a new section "### Power User Workarounds" under "Mac MPS Resolution Limitation"
- Document the `--force-mps` flag usage and risks
- Document environment variable `PYTORCH_ENABLE_MPS_FALLBACK=1` for partial CPU fallback
- Add examples of experimental usage
- Warn about potential crashes and data loss

### Step 5: Run validation commands

- Run pytest to ensure no regressions
- Test `--help` output to verify new flag appears
- Test the warning messages appear correctly

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `cd /Users/szou/Python/Playground/Z_Image_HF && uv run pytest tests/ -v` - Run tests to ensure no regressions
- `cd /Users/szou/Python/Playground/Z_Image_HF && uv run z-image --help 2>/dev/null | grep -A2 "force-mps"` - Verify --force-mps flag appears in help
- `cd /Users/szou/Python/Playground/Z_Image_HF && uv run python -c "from z_image.generator import resolve_device; print(resolve_device('auto', 1920, 1080, force_mps=True))"` - Verify force_mps returns mps

## Notes
- The `--force-mps` flag should be considered experimental and for advanced users only
- The warning messages should be clear and visible but not overly alarming
- Consider using ANSI colors if terminal supports it, but fall back gracefully
- The force_mps flag only affects auto mode - if user explicitly sets --device cpu, respect that choice
