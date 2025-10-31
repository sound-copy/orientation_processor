# Repository Guidelines

## Project Structure & Module Organization
Source code lives in `stage1/` and `stage2/`. `stage1/midi_and_wav_to_json.py` ingests paired MIDI/WAV files defined in `stage1/config_stage1.yaml`, producing JSON summaries under the configured output directory. `stage2/` hosts follow-up analysis (I/O helpers, feature miners, plotting utilities) and `stage2.py` wires those modules for smoke checks. Top-level files such as `config.yaml`, `requirements.txt`, and `pyproject.toml` capture runtime settings and dependency locks.

## Build, Test, and Development Commands
Create an isolated environment before installing libraries: `python -m venv .venv && source .venv/bin/activate`. Install dependencies with `pip install -r requirements.txt` (or `pip install -e .` while iterating on the package). Regenerate Stage 1 artifacts with `python stage1/midi_and_wav_to_json.py --cfg stage1/config_stage1.yaml`; adjust the config path when experimenting. Use `python stage2.py` to confirm Stage 2 imports succeed and to spot missing dependencies early.

## Coding Style & Naming Conventions
Follow standard Python 3 conventions: 4-space indentation, `snake_case` for functions and modules, `PascalCase` for classes, and descriptive variable names. Prefer explicit type hints when new APIs surface. Keep logging/debug output behind a verbosity flag or helper, since the current Stage 1 script prints diagnostic context. Update YAML configs in lockstep with code and store sample assets beside their stage to keep paths predictable.

## Testing Guidelines
There is no automated test suite yet; new work should introduce `pytest` tests under a `tests/` directory that mirrors the stage layout (for example, `tests/stage1/test_midi_and_wav_to_json.py`). Prefer fixture data stashed inside `tests/data/` so Stage 1 runs do not overwrite production JSON. Gate expensive audio analysis with markers (e.g., `@pytest.mark.slow`) and document minimum coverage expectations in future PRs.

## Commit & Pull Request Guidelines
Recent history follows Conventional Commits (`chore:`, `docs:`, `ci:`). Keep subject lines under 72 characters, describe user-visible changes in the body, and reference issues with `(#123)` when applicable. For pull requests, supply a concise summary, note which configs or artifacts changed, and include before/after snippets or JSON samples when behavior shifts. Add a checklist of validation steps (Stage 1 conversion, Stage 2 smoke run, relevant tests) so reviewers can reproduce results quickly.

## Audio & Configuration Tips
External libraries such as `librosa`, `soundfile`, and `madmom` may require system packages—note platform-specific steps in PRs as you encounter them. Favor relative directories (as in `stage1/config_stage1.yaml`) or environment variables resolved inside the scripts to keep YAML portable.
