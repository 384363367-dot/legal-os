#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${CODEX_HOME:-$HOME/.codex}/skills"
DRY_RUN=0
REPLACE=0
SETUP_RUNTIME=0
usage(){ cat <<EOF
Usage: ./install.sh [--dry-run] [--replace] [--setup-runtime] [--target DIR]
  --dry-run        Show actions without copying.
  --replace        Backup and replace an existing Skill directory.
  --setup-runtime  Install/upgrade root requirements with the active Python.
  --target DIR     Override destination Skills directory.
EOF
}
while [[ $# -gt 0 ]]; do
 case "$1" in
  --dry-run) DRY_RUN=1;;
  --replace) REPLACE=1;;
  --setup-runtime) SETUP_RUNTIME=1;;
  --target) shift; [[ $# -gt 0 ]] || { echo "--target requires DIR" >&2; exit 2; }; TARGET="$1";;
  -h|--help) usage; exit 0;;
  *) echo "Unknown option: $1" >&2; usage >&2; exit 2;;
 esac
 shift
done
[[ -d "$ROOT/skills" ]] || { echo "Missing repository skills/ directory" >&2; exit 3; }
SKILLS=()
while IFS= read -r skill_dir; do
 SKILLS[${#SKILLS[@]}]="${skill_dir##*/}"
done < <(find "$ROOT/skills" -mindepth 1 -maxdepth 1 -type d -print | LC_ALL=C sort)
[[ ${#SKILLS[@]} -gt 0 ]] || { echo "No Skills found" >&2; exit 3; }
if [[ $DRY_RUN -eq 0 ]]; then mkdir -p "$TARGET"; fi
STAMP="$(date +%Y%m%d-%H%M%S)"
for name in "${SKILLS[@]}"; do
 src="$ROOT/skills/$name"; dst="$TARGET/$name"
 [[ -f "$src/SKILL.md" ]] || { echo "Invalid Skill (missing SKILL.md): $name" >&2; exit 4; }
 if [[ -e "$dst" ]]; then
  if [[ $REPLACE -ne 1 ]]; then echo "EXISTS: $dst (use --replace)" >&2; exit 5; fi
  backup="$TARGET/.backup/$STAMP/$name"
  echo "BACKUP $dst -> $backup"
  if [[ $DRY_RUN -eq 0 ]]; then mkdir -p "$(dirname "$backup")"; mv "$dst" "$backup"; fi
 fi
 echo "INSTALL $name -> $dst"
 if [[ $DRY_RUN -eq 0 ]]; then cp -a "$src" "$dst"; fi
done
if [[ $SETUP_RUNTIME -eq 1 ]]; then
 echo "PYTHON REQUIREMENTS $ROOT/requirements.txt"
 PYTHON_CMD="${PYTHON:-python3}"
 command -v "$PYTHON_CMD" >/dev/null 2>&1 || { echo "Python command not found: $PYTHON_CMD" >&2; exit 6; }
 if [[ $DRY_RUN -eq 0 ]]; then "$PYTHON_CMD" -m pip install -r "$ROOT/requirements.txt"; fi
fi
echo "OK: ${#SKILLS[@]} Skill(s) processed"
