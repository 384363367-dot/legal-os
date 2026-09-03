# CLI contract

All commands use the Python standard library and can be run without installing a dependency. Live commands require an environment with permission to access the selected official site; tests use mock clients and do not make network requests.

Common options:

- `--search KEYWORD`: title or source-specific keyword search;
- `--range title|content`: choose title or content search when supported;
- `--size N` and `--page N`: bound the result window;
- `--info URL`: fetch one official detail page;
- `--output-dir DIR`: write explicitly requested JSON/result files;
- `--cache-dir DIR`: opt into a caller-owned cache directory;
- `--no-cache`: disable an explicitly configured cache;
- `--cache-stats` / `--cache-clear`: inspect or clear an explicitly configured cache without making a source request;
- `--log-file PATH`: write an explicit JSON-lines request audit log; no log path is selected implicitly;
- `--timeout SECONDS`: bound one request;
- `--json`: emit structured output where supported.

The NPC adapter additionally supports `--preview BBBS`, `--article BBBS [ARTICLE]`, `--grep KEYWORD`, `--download BBBS --output PATH`, and `--urls-only`. Source-specific adapters expose `--category`, `--year`, `--department`, `--status`, `--max-pages`, and `--output-dir` where the selected official source supports them. All result and download paths must be supplied by the caller.

An error from an official source is returned as structured `BLOCKED_BY_SOURCE`/`SOURCE_ERROR` information or a non-zero process exit. The command does not silently substitute a search-engine result or an unregistered mirror.
