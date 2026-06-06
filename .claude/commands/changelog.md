---
description: git 커밋을 일자별(YYYY-MM-DD)로 정리해 CHANGELOG.md를 생성/갱신한다
argument-hint: "[<git log 옵션>] 예) --since=2026-06-01  또는  v1.0..HEAD (생략 가능)"
allowed-tools: Bash(git log:*), Bash(git rev-list:*), Bash(git branch:*), Read, Write, Edit
---

## 컨텍스트 (자동 수집)

- 현재 브랜치: !`git branch --show-current`
- 총 커밋 수: !`git rev-list --count HEAD 2>/dev/null || echo 0`
- 커밋 로그 (날짜<TAB>해시<TAB>제목<TAB>작성자): !`git log --date=short --pretty=format:'%ad%x09%h%x09%s%x09%an' $ARGUMENTS`

## 작업

위에서 자동 수집한 git 커밋 로그를 바탕으로 저장소 루트의 `CHANGELOG.md`를
**작성하거나 갱신**한다.

### 규칙

1. **일자별 그룹화**: 커밋을 `YYYY-MM-DD` 날짜별로 묶는다. **최신 날짜가 맨 위**.
2. **날짜 안에서 분류**: 같은 날짜의 커밋들을 커밋 제목을 보고 아래 카테고리로
   나눈다. 비어 있는 카테고리는 출력하지 않는다.
   - **Added** — 새 기능/파일/엔드포인트 (feat, add, 신규 등)
   - **Changed** — 동작/구조 변경, 리팩터링 (refactor, change, update 등)
   - **Fixed** — 버그 수정 (fix, bugfix 등)
   - **Removed** — 삭제/제거 (remove, delete 등)
   - **Docs** — 문서 변경 (docs, 문서 등)
   - **Other** — 위에 해당하지 않는 나머지
3. **한 줄 형식**: `- <사람이 읽기 좋은 설명> (`<짧은 해시>`)`.
   커밋 제목의 `feat:`, `fix:` 같은 접두어는 떼고 자연스러운 한국어 설명으로 다듬는다.
4. **멱등성(갱신 시)**: `CHANGELOG.md`가 이미 있으면 통째로 덮어쓰지 말고,
   **아직 없는 날짜/커밋만 추가**한다. 사용자가 손으로 적은 내용은 보존한다.
   같은 해시가 이미 기록돼 있으면 중복 추가하지 않는다.
5. 커밋이 하나도 없으면 그 사실을 알리고 빈 템플릿만 만든다.

### 출력 형식 (예시)

```markdown
# Changelog

이 프로젝트의 주요 변경 사항을 일자별로 기록한다.

## 2026-06-06

### Added
- items CRUD 엔드포인트와 인메모리 저장소 추가 (`433d265`)

### Docs
- PLAN_SPEC.md 계획 명세서 작성 (`a1b2c3d`)
```

### 인자(`$ARGUMENTS`) 사용법

- 인자 없이 `/changelog` → 전체 히스토리.
- `/changelog --since=2026-06-01` → 해당 날짜 이후 커밋만.
- `/changelog v1.0..HEAD` → 특정 범위만.

작업을 마치면 **추가/갱신된 날짜와 커밋 수를 요약**해서 보고한다.
