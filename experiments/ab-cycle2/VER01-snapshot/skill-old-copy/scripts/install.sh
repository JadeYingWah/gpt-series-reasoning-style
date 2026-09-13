#!/usr/bin/env bash
set -euo pipefail

SKILL_NAME="gpt-series-reasoning-style"
SOURCE="$(cd "$(dirname "$0")/.." && pwd)"
PLATFORM="${1:-agents}"
FORCE="${FORCE:-0}"

case "$PLATFORM" in
  agents|antigravity) DEST="$HOME/.agents/skills/$SKILL_NAME" ;;
  codex) DEST="$HOME/.codex/skills/$SKILL_NAME" ;;
  claude) DEST="$HOME/.claude/skills/$SKILL_NAME" ;;
  cursor) DEST="$(pwd)/.cursor/rules/$SKILL_NAME" ;;
  windsurf) DEST="$(pwd)/.windsurf/rules/$SKILL_NAME" ;;
  cline) DEST="$(pwd)/.clinerules/$SKILL_NAME" ;;
  gemini) DEST="$HOME/.gemini/skills/$SKILL_NAME" ;;
  kiro) DEST="$HOME/.kiro/skills/$SKILL_NAME" ;;
  trae) DEST="$(pwd)/.trae/rules/$SKILL_NAME" ;;
  goose) DEST="$HOME/.config/goose/skills/$SKILL_NAME" ;;
  opencode) DEST="$HOME/.config/opencode/skills/$SKILL_NAME" ;;
  roo) DEST="$(pwd)/.roo/rules/$SKILL_NAME" ;;
  *)
    echo "Unknown platform: $PLATFORM" >&2
    exit 1
    ;;
esac

if [ -e "$DEST" ] && [ "$FORCE" != "1" ]; then
  echo "Destination already exists: $DEST. Set FORCE=1 to overwrite." >&2
  exit 1
fi

mkdir -p "$(dirname "$DEST")"
rm -rf "$DEST"
cp -R "$SOURCE" "$DEST"
echo "Installed $SKILL_NAME to $DEST"
