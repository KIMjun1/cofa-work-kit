# TOOLS: 오픈소스 후보와 제안 규칙

원칙: 속도보다 정확한 읽기를 우선한다. 단, 설치는 필요가 확인된 뒤에만 한다.

## 0. 기본 패키지 (셋업 때 이미 설치함, 승인 불필요)
- pandas, openpyxl: 표와 엑셀 읽기·계산
- pdfplumber: PDF 텍스트와 표
- pillow: 이미지 형식·크기 확인
- matplotlib + koreanize-matplotlib: 그래프. 리눅스에서 한글이 네모로 깨지는 문제 방지 (`import koreanize_matplotlib`). 한글 폰트 설치가 실패하면 그래프 라벨을 영어로 쓴다

## 1. 상황별 추가 후보 (설치 전 2번 양식으로 제안하고 승인받는다)
| 상황 | 후보 | 쓰는 이유 | 주의 |
|---|---|---|---|
| 수십만 행 이상 표, 여러 표 결합 | duckdb | SQL로 정확하고 빠르게 집계 | 결과는 pandas로 3행 대조 |
| PDF 텍스트 대량·이미지 추출 | pymupdf | 빠르고 이미지 추출 가능 | 표는 pdfplumber 결과와 교차 확인 |
| 이미지 측정 (밝기, 영역, 결함 크기) | opencv-python-headless | 수치 측정 | 무엇이 찍혔는지는 모델이 보고, 읽은 값은 AGENTS.md 판독 규칙대로 기록 |
| 상관·회귀·검정으로 가정 판정 | scipy, statsmodels | 기각 조건을 p값·효과크기로 판정 | 표본 수와 가정(정규성 등)을 같이 보고 |
| 군집·이상치·분류 | scikit-learn | 패턴 분류 | 결과를 원본 사례 3개로 확인 |
| Word 출력 요구 | python-docx | 형식 요구가 있을 때만 | |
| PPT 출력 요구 | python-pptx | 형식 요구가 있을 때만 | |
| 앱·대시보드 구현형 | streamlit | 적은 코드로 화면 구현 | IDE 안에서 실행 확인 먼저 |

스캔 이미지가 수십 장 이상이라 직접 판독이 어려우면, 그때 OCR 패키지 후보를 2번 양식으로 제안한다.

쓰지 않는다: 외부 LLM API 키가 필요한 도구(LangGraph, CrewAI 등. 외부 AI 연결 금지), 결과물을 자동 생성하는 템플릿 레포.

## 2. 제안 양식 (Codex는 설치 전에 이 형식으로 보고하고 멈춘다)
```
[도구 제안]
- 막힌 지점: (파일명, 작업, 기본 패키지로 안 되는 이유. 수치로)
- 후보: A / B (각 장점 한 줄)
- 설치 없이 하는 방법과 그 한계:
- 추천: A (이유) / 실패 시 대안:
```
- 사용자가 고르면 DECISIONS.md에 D항목으로 기록하고, 사용자가 터미널에서 `python3 -m pip install 패키지` 로 설치한다.
- 설치가 2번 실패하면 재시도하지 말고 대안으로 간다.

## 3. 웹 화면 디자인 (구현형, PRD 6번에서 고른 경우만)
출처: github.com/Leonxlnx/taste-skill-classics (MIT). 각 스타일은 의존성 없는 SKILL.md 1개(90줄 안팎)다.
```bash
git clone --depth 1 https://github.com/Leonxlnx/taste-skill-classics /tmp/taste
mkdir -p design && cp /tmp/taste/LICENSE design/LICENSE-taste-skill
cp /tmp/taste/skills/minimalist-skill/SKILL.md design/minimalist-ui.md     # 권장: 업무 도구
# 또는: cp /tmp/taste/skills/soft-skill/SKILL.md design/high-end-visual-design.md
git add design && git commit -m "design: 공개 디자인 규칙 반영 (taste-skill-classics, MIT)"
```
- 화면을 만들거나 고칠 때 design/의 규칙을 따른다. 단, 과제 요구와 한글 가독성이 우선이며 사진·애니메이션은 넣지 않는다.
- 디자인은 P0 기능이 완성된 뒤 S 하나(20분 이내)로 적용한다.
- 쓰지 않는다: taste-skill 본체 v2(Node 22·Chrome 필요, 한 번에 30~45분·수십만 토큰), gpt-taste(애니메이션·실험적 레이아웃이 강해 업무 도구에 과함).

