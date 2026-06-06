#!/usr/bin/env bash
# changelog skill — git 커밋을 일자별 정리용으로 수집한다.
# 사용법: gather.sh [<git log 옵션...>]   예) gather.sh --since=2026-06-01
set -euo pipefail

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: git 저장소가 아닙니다." >&2
  exit 1
fi

echo "branch: $(git branch --show-current 2>/dev/null || echo '(detached)')"
echo "commits: $(git rev-list --count HEAD 2>/dev/null || echo 0)"
echo "---log---"
# 날짜<TAB>짧은해시<TAB>제목<TAB>작성자  (최신순)
git log --date=short --pretty=format:'%ad%x09%h%x09%s%x09%an' "$@"
echo
