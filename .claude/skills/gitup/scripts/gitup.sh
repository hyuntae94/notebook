#!/usr/bin/env bash
# gitup skill — git add → commit → (브랜치 전환/생성) → push 자동화
# 사용법: gitup.sh "<커밋 메시지>" "<브랜치명>"
set -euo pipefail

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: git 저장소가 아닙니다." >&2
  exit 1
fi

MSG="${1:-}"
BRANCH="${2:-}"

if [ -z "$MSG" ]; then
  echo "ERROR: 커밋 메시지가 비어 있습니다." >&2
  exit 1
fi
if [ -z "$BRANCH" ]; then
  echo "ERROR: 브랜치명이 비어 있습니다." >&2
  exit 1
fi

# 1) 모든 변경사항 스테이징
git add -A

# 스테이징된 변경이 없으면 중단(빈 커밋 방지)
if git diff --cached --quiet; then
  echo "ERROR: 스테이징된 변경사항이 없습니다. 푸쉬할 내용이 없습니다." >&2
  exit 1
fi

# 2) 브랜치 전환 또는 생성 (스테이징된 변경은 그대로 따라감)
if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  git checkout "$BRANCH"
else
  git checkout -b "$BRANCH"
fi

# 3) 커밋
git commit -m "$MSG"

# 4) 푸쉬 (upstream 없으면 -u 로 설정)
git push -u origin "$BRANCH"

echo "---done---"
echo "branch: $BRANCH"
echo "commit: $(git rev-parse --short HEAD)"
