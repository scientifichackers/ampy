# ampy v2 — Development Plan

This document tracks what has been done, decisions made, and what remains for the future.

---

## Completed

### Phase 1 — Bug Fixes

| Fix | Files | Details |
|-----|-------|---------|
| Remove debug print in `reset` | `cli.py` | `print("here we are", repr(r))` was left in production code |
| Fix `reset` exit code on failure | `cli.py` | `reset --safe/--bootloader` now exits 1 on MicroPython (unsupported) |
| Fix `run` exit code on missing file | `cli.py` | Now exits 1 instead of 0 when local file not found |
| Clean error messages (no tracebacks) | `cli.py` | `AmypGroup` catches `RuntimeError`/`DirectoryExistsError` at top level |
| Fix `rm` error handling | `files.py` | Conditions used `!= 1` instead of `!= -1`; errno 13 was wrong for ENOTEMPTY (should be 39); now parses errno numerically |
| Fix `ls -l` directory display | `files.py` | Shows `<dir>` instead of meaningless block-size byte count for directories |
| Add `import re` | `files.py` | Required by new errno parsing |

### Phase 2 — PR Merges (small/docs)

| PR | Change |
|----|--------|
| #115 | Added `mkdir`, `rmdir`, `reset` to README command list |
| #121 | Added `ampy/__main__.py` — enables `python -m ampy` |
| #129 | Raw string fix: `r"^COM(\d+)$"` — eliminates `SyntaxWarning` on every invocation |

### Phase 3 — PR Merges (features)

| PR | Change |
|----|--------|
| #111 | `ubinascii` → `binascii` fallback in the MicroPython-side `get` command |
| #109 | `auto_envvar_prefix='AMPY'` on the Click group — future options get env vars automatically |
| #107 | `get` accepts multiple files via `nargs=-1` + `--output/-o`; `rm` accepts multiple files |
| #93 | Progress bar for `put` using `click.progressbar` (no extra dep); suppress with `--no-progress` |
| #69 | Drain available serial bytes before Ctrl-C when `--delay > 0`, for Feather52 compatibility |

### Phase 4 — Cherry-picks

| Source | Change |
|--------|--------|
| PR #85 | `logging.debug()` calls at the start of every `Files` method — silent by default |
| PR #88 (decision) | EISDIR auto-rmdir was **intentionally skipped** — silently deleting directory contents is destructive. Current "Is a directory (use rmdir to remove)" error is correct. |

---

## Skipped PRs — Reasons

| PR | Reason |
|----|--------|
| **#130** | Superseded: regex fix done by #129, binascii fix done by #111 |
| **#123** | Superseded by #128; `progress_bar.py` module doesn't exist in this repo |
| **#128** | A separate fork/product (1059 lines, interactive shell, references non-existent `lsi()` method, calls external `tio` binary). Not a targeted patch. |
| **#106** | Critical runtime bug: iterating `bytes` yields `int`, so `b'' + b` raises `TypeError`. Concept (UTF-8 streaming) is right but needs a full rewrite. See Future Work. |
| **#108** | `put --strip`: undefined variable bug (`filepath` vs `local_filepath`), `ast.unparse()` requires Python 3.9+, and it only strips docstrings (not inline comments despite the name). See Future Work. |
| **#88 (EISDIR auto-rmdir)** | Destructive — auto-deleting directory contents without confirmation is unsafe. |

---

## Future Work

### High Priority

- **RTS/DTR pin control** (Issue #124, PR #126)
  - Root cause of ESP32-CAM and many other board failures
  - PR #126 replaces all of `pyboard.py` with upstream MicroPython's version — too large to merge cleanly
  - Recommended: extract only the `exclusive` param and RTS/DTR init options from PR #126's `Pyboard.__init__` and apply them to the existing `pyboard.py`
  - Add `--rts` / `--dts` CLI flags and env vars `AMPY_RTS` / `AMPY_DTR`

- **UTF-8 streaming output fix** (PR #106)
  - `run` can produce mojibake for non-ASCII board output
  - PR #106's implementation has a `TypeError` (`b'' + int` in a bytes loop)
  - Fix: replace `stdout_write_bytes` with a proper UTF-8 state machine using `bytes([i])` for each byte

- **Port not released after exit** (Issue #112)
  - On Linux, the serial port is sometimes not released after ampy exits
  - Investigate: add `serial.close()` in a `finally` block in the CLI entry point (currently only in `if __name__ == "__main__"`, not the console_scripts path)

### Medium Priority

- **`put --strip`** (PR #108)
  - Strip docstrings and optionally comments from `.py` files before upload to save flash
  - Fix the undefined `filepath` → `local_filepath` variable bug
  - Gate on Python ≥ 3.9 (`ast.unparse` requirement) or use `tokenize` for broader compat
  - Rename to `put --minify` or `put --strip-docstrings` to be accurate about what's removed

- **`mv` / rename command** (Issue #61, marked Good First Issue)
  - No rename command exists; users must `get` + `put` + `rm`
  - MicroPython has `os.rename()` — straightforward to add as a new `mv` CLI command

- **JSON output for `ls`** (Issue #59)
  - Add `--json` flag to `ls` for machine-readable output
  - Useful for scripting and GUI tools built on top of ampy

- **Hidden file filtering in `put`** (Issue #113)
  - Recursive `put` currently copies `.git`, `__pycache__`, `.DS_Store` etc.
  - Add default exclusion list; allow override with `--include-hidden`

- **Increase `BUFFER_SIZE`** (`files.py`)
  - Currently 32 bytes per write — extremely conservative
  - Modern boards and USB-serial bridges handle 256–512 bytes safely
  - Would significantly speed up large file uploads

### Low Priority

- **`python -m ampy` console_scripts alignment** (Issue #112 related)
  - The `if __name__ == "__main__"` block in `cli.py` closes the board connection in `finally`
  - The console_scripts entry point does not — if Click exits abnormally the port may stay open
  - Fix: move close logic into `AmypGroup.invoke`'s `finally`

- **Windows COM port hanging** (Issues #71, #72)
  - Commands hang indefinitely on Windows 10 for some boards
  - Likely a serial timeout issue — needs investigation on Windows hardware

- **`BUFFER_SIZE` as a CLI option** 
  - Allow `--buffer-size` or `AMPY_BUFFER_SIZE` env var for power users

- **Interactive shell** (PR #128 concept)
  - The PR #128 interactive frontend is a full fork, but the concept is valid
  - Could be implemented as a separate `ampy shell` subcommand that wraps the existing API
