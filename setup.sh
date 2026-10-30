#!/usr/bin/env bash
# 사용법 (과제 폴더에서): bash /tmp/kit/setup.sh
KIT=/tmp/kit
echo "[1/5] 작업 폴더: $(pwd)"; ls
NFILES=$(ls -A | grep -v '^\.git$' | wc -l)
if [ "$NFILES" -eq 0 ]; then WARN_EMPTY=1; echo "  (과제 파일이 안 보임. 셋업은 계속합니다)"; fi

CONFLICT=""; COPIED=""
for f in AGENTS.md PROMPTS.md TOOLS.md; do
  if [ -e "$f" ] && ! cmp -s "$f" "$KIT/$f"; then CONFLICT="$CONFLICT $f"; else cp "$KIT/$f" . && COPIED="$COPIED $f"; fi
done
for f in PLAN.md PRD.md DECISIONS.md REVIEW.md; do
  if [ -e "$f" ] && ! cmp -s "$f" "$KIT/templates/$f"; then CONFLICT="$CONFLICT $f"; else cp "$KIT/templates/$f" . && COPIED="$COPIED $f"; fi
done
mkdir -p kit_tools && cp "$KIT/tools/profile_data.py" kit_tools/
echo "[2/5] 키트 파일 복사 완료"

{ python3 -m pip install -q pandas openpyxl pdfplumber pillow matplotlib || python3 -m pip install -q --break-system-packages pandas openpyxl pdfplumber pillow matplotlib; } >/dev/null 2>&1
{ python3 -m pip install -q koreanize-matplotlib || python3 -m pip install -q --break-system-packages koreanize-matplotlib; } >/dev/null 2>&1
if python3 -c "import pandas, openpyxl" 2>/dev/null; then PKG="정상"; else PKG="실패"; fi
echo "[3/5] 패키지 설치: $PKG"

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || git init -q
git config user.name >/dev/null 2>&1 || { git config user.name "candidate"; git config user.email "candidate@cofa.local"; }
python3 kit_tools/profile_data.py . >/dev/null 2>&1 && echo "[4/5] 자료 요약 생성 (DATA_PROFILE.md)" || echo "[4/5] 자료 요약 실패"

for f in $COPIED kit_tools DATA_PROFILE.md; do [ -e "$f" ] && git add "$f"; done
git commit -q -m "chore: apply pre-released work kit from https://github.com/KIMjun1/cofa-work-kit" && echo "[5/5] 커밋 완료"

echo
echo "===== 셋업 완료 ====="
[ "$PKG" = "실패" ] && echo "- Codex를 켠 뒤 첫 마디: '패키지 설치가 실패했어'"
[ -n "$CONFLICT" ] && echo "- 과제에 원래 있던 파일(덮어쓰지 않음):$CONFLICT" && echo "  Codex를 켠 뒤 첫 마디: '과제 파일과 /tmp/kit 키트 규칙이 충돌하는지 봐 주고, 과제 규칙을 우선해서 같이 따라 줘'"
git check-ignore -q out/ 2>/dev/null && echo "- 참고: out/ 폴더가 git에서 무시됨 (Codex가 처리)"
[ -n "$WARN_EMPTY" ] && echo "- 주의: 이 폴더에 과제 파일이 없었습니다. 왼쪽 파일 목록에 과제 파일이 보이면 터미널 위치가 다른 것이니, ls로 폴더 이름을 보고 cd 폴더이름 으로 이동한 뒤 셋업 한 줄을 다시 붙여넣으세요. 과제 설명이 화면에만 있다면 이대로 진행하고, Codex에게 원문을 붙여넣어 'TASK.md로 저장해 줘'라고 말하세요."
echo "- 다음: 터미널에 codex 입력 후 Enter"
