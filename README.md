# Cofa Probe Hackathon Work Kit

본 저장소는 대회 시작 전 사전 제작·공개한 **작업 방식 및 의사결정 기록 도구(지침·템플릿·하네스)**입니다.
특정 과제를 위한 보고서, 분석 코드, 도메인 지식은 없습니다. 범용 자료 요약 스크립트 1개(tools/profile_data.py)만 포함합니다.

## 1. 셋업 (과제 시작 직후 터미널에 붙여넣기)

```bash
# 0) 과제 폴더인지 확인. 과제 파일이 안 보이면 cd 로 과제 폴더로 이동
pwd && ls

# 1) 시작 시각 기록, 키트를 작업 폴더 밖(/tmp)에 clone
date '+%Y-%m-%d %H:%M' > START_TIME.txt
git clone https://github.com/KIMjun1/cofa-work-kit.git /tmp/kit

# 2) 키트 파일 복사 (같은 이름이 있으면 덮어쓰지 않음). diff가 아무것도 안 나오면 정상
cp -n /tmp/kit/AGENTS.md /tmp/kit/PROMPTS.md /tmp/kit/TOOLS.md /tmp/kit/templates/*.md .
mkdir -p kit_tools && cp -n /tmp/kit/tools/profile_data.py kit_tools/
for f in AGENTS.md PROMPTS.md TOOLS.md; do diff -q $f /tmp/kit/$f; done; for f in PLAN.md PRD.md DECISIONS.md REVIEW.md; do diff -q $f /tmp/kit/templates/$f; done

# 3) 기본 패키지 설치. 한글 폰트는 따로 설치하고 실패해도 계속
python3 -m pip install pandas openpyxl pdfplumber pillow matplotlib || python3 -m pip install --break-system-packages pandas openpyxl pdfplumber pillow matplotlib
python3 -m pip install koreanize-matplotlib || python3 -m pip install --break-system-packages koreanize-matplotlib || echo "한글 폰트 생략"

# 4) 자료 요약 (DATA_PROFILE.md). '기본 패키지 미설치' 줄이 있으면 3)을 다시 확인
python3 kit_tools/profile_data.py .

# 5) 키트 파일만 커밋 (원본 자료는 커밋하지 않음)
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || git init
git config user.name >/dev/null 2>&1 || (git config user.name "candidate" && git config user.email "candidate@cofa.local")
git check-ignore -q out/ && echo "주의: out/이 git에서 무시됨. 산출물 위치를 PLAN에 정할 것"
git add AGENTS.md PROMPTS.md TOOLS.md PLAN.md PRD.md DECISIONS.md REVIEW.md kit_tools START_TIME.txt DATA_PROFILE.md
git commit -m "chore: apply pre-released work kit from https://github.com/KIMjun1/cofa-work-kit"
```

- 2)에서 "differ"가 나온 파일은 과제에 원래 있던 파일이라 덮어쓰지 않은 것입니다. 과제 파일을 먼저 읽고, 키트 파일은 `/tmp/kit`에서 참고합니다.
- **AGENTS.md가 "differ"이면 키트 규칙이 꺼진 상태입니다** (Codex는 AGENTS.md만 자동으로 읽음). 과제의 AGENTS.md를 읽고 충돌이 없으면 아래로 덧붙인 뒤, 그 결정을 DECISIONS.md D1에 남깁니다.
  `printf '\n# (사전 공개 키트 규칙 추가)\n' >> AGENTS.md && cat /tmp/kit/AGENTS.md >> AGENTS.md`
- `cp: warning: behavior of -n is non-portable` 경고는 무시합니다.
- 5)에서 `Please tell me who you are`가 나오면 `git config user.name "me" && git config user.email "me@example.com"` 후 git commit 줄만 다시 실행합니다.
- 6) 과제 설명이 화면이나 대화로만 주어지면, 에디터에서 새 파일 `TASK.md`를 만들어 원문을 붙여넣고 `git add TASK.md && git commit -m "task: 과제 원문 기록"` 합니다. 과제 README가 따로 있으면 그 파일을 TASK.md 대신 씁니다.

## 2. 타임라인 (180분)

| 분 | 할 일 | 사용 |
|---|---|---|
| 0~10 | 셋업, `/model`에서 Sol 6.1과 effort 확인 | 1장 |
| 10~20 | 과제 파악과 유형 확정, 애매한 점 정리 (실무자 에이전트가 있으면 질문) | P1, P2 |
| 20~35 | (구현형) 서비스 설계 확정 → 계획 확정(Codex 초안 + 위험 3개를 보고 **내가 확정**) → 커밋. 분석형은 30분까지 | P2b, P3 |
| 35~140 | S#마다 실행 → 커밋. 결정은 DECISIONS.md. **130분에 남은 S를 점검하고 줄인다** | P4 |
| 140~160 | 독립 검증 → 반영, 일치 검사 | P5, P6 |
| 160~172 | 외워 둘 메모 작성과 암기, 최종 산출물 위치 확인, 최종 커밋 | P7 |
| 172~180 | 제출 (여유 8분) | |

## 3. 말하는 법 (번호 대신 목적과 기준을 내 말로)
Codex는 셋업이 끝난 뒤 켭니다(AGENTS.md를 시작할 때 읽음). 예시이며 그대로 외울 필요는 없습니다.
| 단계 | 예시 문장 |
|---|---|
| P1 | 과제랑 자료부터 파악하자. 유형 후보와 근거를 보여 주고, 확정은 내가 할게 |
| P2 | 애매하거나 자료끼리 안 맞는 부분만 뽑아 줘. 해석은 빼고 |
| P2b | 구현형으로 간다. 서비스 설계는 추천 조합으로 한 번에 보여 줘 |
| P3 | 계획 세워 줘. 제일 위험한 곳도 같이 |
| P4 | "다음" 또는 "진행해" (Codex가 제안한 다음 단계를 실행. 번호를 몰라도 됨) |
| P5 | 독립 검증해 줘 (같은 창에서 진행. 새 창을 원하면 "새 창에서") |
| P6, P7 | 끝내자 (제출 전 점검과 서술형 준비가 이어서 진행) |
- Codex가 `적용 예정:`으로 물으면 맞는지 보고 답합니다. `건너뛰기 제안`이 오면 진행 여부를 내가 정합니다.
- **외울 것은 세 마디뿐입니다**
  1. 시작: "과제랑 자료부터 파악하자. 유형은 내가 정할게"
  2. 진행: "다음" / "진행해" / "추천대로" / "1번" (Codex가 제안한 것을 실행)
  3. 막힐 때: "이제 뭐 해?"
- Codex가 유형·계획·결론을 정할 때 "이유 한 마디"를 물으면 짧게 답합니다(예: "원문 그대로라서"). 그 말이 DECISIONS.md에 인용됩니다. 그 밖에도 여유가 있으면 짧은 답에 내 판단을 한 마디 붙입니다. 예) "진행해. 단 그래프는 빼고", "2번. 시간이 부족해서". 이것이 의도 점수의 근거가 됩니다.
- **순서가 기억나지 않으면 "이제 뭐 해?"라고만 물으면 됩니다.** Codex는 매 보고 마지막 줄에 `위치 · 경과 시간 · 다음 할 일 · 결정 필요`를 붙이고, 130·140·160분에 다음 단계를 먼저 제안합니다.

## 4. 구성 파일
- `AGENTS.md`: Codex 작업 규칙 (길잡이 역할, 대화 원칙, 단계 판단, 코드 계산, 설치 승인)
- `PLAN.md`: 과제 유형과 검증 방식, 문제, 성공 기준(R), 제출물, 가정(H)과 기각 조건, 단계(S)
- `PRD.md`: 구현형 과제일 때만. 3·6·7번은 역질문, 나머지는 가정 후 확인
- `DECISIONS.md`: 결정 기록 (선택, 근거, 버린 대안, 영향)
- `REVIEW.md`: 독립 검증표, 불일치 목록, 서술형 대비 메모
- `PROMPTS.md`: 국면별 지시문 P1~P7 (구현형은 P2b)
- `TOOLS.md`: 기본 패키지, 상황별 오픈소스 후보, 설치 제안 양식
- `tools/profile_data.py`: 환경 점검과 자료 요약 (당일엔 kit_tools/로 복사). 판별이 불확실하면 "확인 필요" 표시
- `tests/test_profile.py`: 스크립트 검증 (`python3 tests/test_profile.py`, 당일엔 복사하지 않음)
