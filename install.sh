#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${CODEX_HOME:-$HOME/.codex}/skills"
DRY_RUN=0
REPLACE=0
SETUP_RUNTIME=0
STAGE_ROOT=""
BACKUP_DIR=""
TARGET_CREATED=0
BACKUP_PARENT_CREATED=0
TRANSACTION_STARTED=0
TRANSACTION_COMMITTED=0
INSTALLED=()
BACKED_UP=()

usage(){ cat <<EOF
Usage: ./install.sh [--dry-run] [--replace] [--setup-runtime] [--target DIR]
  --dry-run        Validate and show actions without copying.
  --replace        Back up and transactionally replace existing Skill directories.
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
[[ -n "$TARGET" ]] || { echo "Refusing an empty target" >&2; exit 3; }
if [[ -L "$TARGET" ]]; then echo "Refusing a symlink target: $TARGET" >&2; exit 3; fi
command -v python3 >/dev/null 2>&1 || { echo "python3 is required to safely normalize --target" >&2; exit 3; }
if ! NORMALIZED_TARGET="$(python3 - "$TARGET" "${HOME:-}" <<'PY'
import os
import sys

target = os.path.realpath(sys.argv[1])
home = os.path.realpath(sys.argv[2]) if sys.argv[2] else None
protected = {
    "/", "/Applications", "/Library", "/System", "/Users", "/Volumes",
    "/bin", "/boot", "/dev", "/etc", "/home", "/lib", "/lib64",
    "/media", "/mnt", "/opt", "/proc", "/root", "/run", "/sbin",
    "/srv", "/sys", "/usr", "/var", "/private", "/private/tmp",
    "/private/var",
}
if home:
    protected.add(home)
if target in {os.path.realpath(path) for path in protected} or os.path.dirname(target) == os.path.sep:
    sys.exit(1)

if os.path.lexists(target):
    if not os.path.isdir(target):
        sys.exit(1)
else:
    ancestor = os.path.dirname(target)
    while not os.path.lexists(ancestor):
        parent = os.path.dirname(ancestor)
        if parent == ancestor:
            break
        ancestor = parent
    if not os.path.isdir(ancestor):
        sys.exit(1)
print(target)
PY
)"; then
 echo "Refusing an unsafe --target path (root/protected directory or invalid ancestor)" >&2
 exit 3
fi
TARGET="$NORMALIZED_TARGET"
if [[ -e "$TARGET" && ! -d "$TARGET" ]]; then echo "Target is not a directory: $TARGET" >&2; exit 3; fi

SKILLS=()
while IFS= read -r skill_dir; do
 SKILLS[${#SKILLS[@]}]="${skill_dir##*/}"
done < <(find "$ROOT/skills" -mindepth 1 -maxdepth 1 -type d -print | LC_ALL=C sort)
[[ ${#SKILLS[@]} -gt 0 ]] || { echo "No Skills found" >&2; exit 3; }

for name in "${SKILLS[@]}"; do
 src="$ROOT/skills/$name"
 dst="$TARGET/$name"
 [[ -f "$src/SKILL.md" ]] || { echo "Invalid Skill (missing SKILL.md): $name" >&2; exit 4; }
 if [[ -e "$dst" || -L "$dst" ]]; then
  [[ -d "$dst" && ! -L "$dst" ]] || { echo "Existing Skill path is not a directory: $dst" >&2; exit 5; }
  [[ $REPLACE -eq 1 ]] || { echo "EXISTS: $dst (use --replace)" >&2; exit 5; }
 fi
done
if [[ -e "$TARGET/.backup" || -L "$TARGET/.backup" ]]; then
 [[ -d "$TARGET/.backup" && ! -L "$TARGET/.backup" ]] || { echo "Backup path is not a directory: $TARGET/.backup" >&2; exit 5; }
fi

if [[ $DRY_RUN -eq 1 ]]; then
 for name in "${SKILLS[@]}"; do
  dst="$TARGET/$name"
  if [[ -e "$dst" || -L "$dst" ]]; then echo "BACKUP $dst -> $TARGET/.backup/<transaction>/$name"; fi
  echo "INSTALL $name -> $dst"
 done
 echo "DRY-RUN: ${#SKILLS[@]} Skill(s) validated; no files changed"
 exit 0
fi

if [[ $SETUP_RUNTIME -eq 1 ]]; then
 echo "PYTHON REQUIREMENTS $ROOT/requirements.txt"
 PYTHON_CMD="${PYTHON:-python3}"
 command -v "$PYTHON_CMD" >/dev/null 2>&1 || { echo "Python command not found: $PYTHON_CMD" >&2; exit 6; }
 "$PYTHON_CMD" -m pip install -r "$ROOT/requirements.txt"
fi

TARGET_PARENT="$(dirname "$TARGET")"
mkdir -p "$TARGET_PARENT"
STAGE_ROOT="$(mktemp -d "$TARGET_PARENT/.legal-os-stage.XXXXXXXX")"
cleanup_stage(){
 if [[ -n "$STAGE_ROOT" && -d "$STAGE_ROOT" ]]; then
  rm -rf "$STAGE_ROOT" || echo "STAGING_CLEANUP_FAILED: $STAGE_ROOT" >&2
 fi
}
trap cleanup_stage EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
STAGE_SKILLS="$STAGE_ROOT/skills"
mkdir -p "$STAGE_SKILLS"
for name in "${SKILLS[@]}"; do
 src="$ROOT/skills/$name"
 staged="$STAGE_SKILLS/$name"
 cp -a "$src" "$staged"
 diff -qr "$src" "$staged" >/dev/null || { echo "Staged Skill verification failed: $name" >&2; exit 8; }
done

rollback(){
 local failed=0 i name dst backup
 set +e
 for ((i=${#INSTALLED[@]}-1; i>=0; i--)); do
  name="${INSTALLED[$i]}"
  dst="$TARGET/$name"
  if [[ -e "$dst" || -L "$dst" ]]; then rm -rf "$dst" || failed=1; fi
 done
 for ((i=${#BACKED_UP[@]}-1; i>=0; i--)); do
  name="${BACKED_UP[$i]}"
  dst="$TARGET/$name"
  backup="$BACKUP_DIR/$name"
  if [[ -e "$backup" || -L "$backup" ]]; then
   if [[ -e "$dst" || -L "$dst" ]]; then
    echo "Rollback conflict; prior Skill retained at $backup" >&2
    failed=1
   else
    mv "$backup" "$dst" || failed=1
   fi
  fi
 done
 if [[ -n "$BACKUP_DIR" && -d "$BACKUP_DIR" ]]; then rmdir "$BACKUP_DIR" 2>/dev/null; fi
 if [[ $BACKUP_PARENT_CREATED -eq 1 && -d "$TARGET/.backup" ]]; then rmdir "$TARGET/.backup" 2>/dev/null; fi
 if [[ $TARGET_CREATED -eq 1 && -d "$TARGET" ]]; then rmdir "$TARGET" 2>/dev/null; fi
 set -e
 return "$failed"
}

on_exit(){
 local rc=$?
 trap - EXIT
 if [[ $TRANSACTION_STARTED -eq 1 && $TRANSACTION_COMMITTED -eq 0 ]]; then
  if rollback; then
   echo "ROLLBACK: complete" >&2
  else
   echo "ROLLBACK_INCOMPLETE: prior copies may remain under $BACKUP_DIR" >&2
   rc=7
  fi
 fi
 if [[ -n "$STAGE_ROOT" && -d "$STAGE_ROOT" ]]; then
  rm -rf "$STAGE_ROOT" || { echo "STAGING_CLEANUP_FAILED: $STAGE_ROOT" >&2; [[ $rc -ne 0 ]] || rc=8; }
 fi
 exit "$rc"
}
trap on_exit EXIT

TRANSACTION_STARTED=1
if [[ ! -e "$TARGET" ]]; then
 mkdir -p "$TARGET"
 TARGET_CREATED=1
fi

STAMP="$(date +%Y%m%d-%H%M%S)-$$"
for name in "${SKILLS[@]}"; do
 dst="$TARGET/$name"
 staged="$STAGE_SKILLS/$name"
 if [[ -e "$dst" || -L "$dst" ]]; then
  [[ $REPLACE -eq 1 && -d "$dst" && ! -L "$dst" ]] || { echo "Target changed during install: $dst" >&2; exit 5; }
  if [[ -z "$BACKUP_DIR" ]]; then
   if [[ ! -e "$TARGET/.backup" ]]; then mkdir "$TARGET/.backup"; BACKUP_PARENT_CREATED=1; fi
   BACKUP_DIR="$(mktemp -d "$TARGET/.backup/${STAMP}.XXXXXXXX")"
  fi
  BACKED_UP[${#BACKED_UP[@]}]="$name"
  mv "$dst" "$BACKUP_DIR/$name"
  echo "BACKUP $dst -> $BACKUP_DIR/$name"
 fi
 INSTALLED[${#INSTALLED[@]}]="$name"
 mv "$staged" "$dst"
 echo "INSTALL $name -> $dst"
done

rm -rf "$STAGE_ROOT"
STAGE_ROOT=""
TRANSACTION_COMMITTED=1
if [[ -n "$BACKUP_DIR" ]]; then echo "ROLLBACK MATERIAL: $BACKUP_DIR"; fi
echo "OK: ${#SKILLS[@]} Skill(s) installed transactionally"
