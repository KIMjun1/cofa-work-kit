#!/usr/bin/env python3
"""
자료 요약 및 실행 환경 점검 (DATA_PROFILE.md 생성)
- Python 3.9+ / 기본: pandas, openpyxl / 없으면 해당 항목만 건너뜀
- 네트워크 사용 없음, 원본 수정 없음, 손상 파일은 해당 항목만 실패 처리
- 행 수는 실제로 읽은 값 기준. 표본이면 반드시 표본이라고 표시
- 판별이 불확실하면 "확인 필요"를 출력한다 (Codex가 그대로 믿지 않도록)
"""
import csv
import os
import subprocess
import sys
from pathlib import Path

BASE = {"pandas": "pandas", "openpyxl": "openpyxl", "pdfplumber": "pdfplumber",
        "PIL": "pillow", "matplotlib": "matplotlib", "koreanize_matplotlib": "koreanize-matplotlib"}
OPTIONAL = {"fitz": "pymupdf", "docx": "python-docx", "duckdb": "duckdb", "cv2": "opencv-python-headless"}


def _has(mod):
    try:
        __import__(mod)
        return True
    except Exception:
        return False


HAS = {m: _has(m) for m in list(BASE) + list(OPTIONAL)}

EXCLUDE_DIRS = {".git", "__pycache__", "node_modules", "venv", ".venv"}
KIT_FILES = {"AGENTS.md", "PROMPTS.md", "TOOLS.md", "PLAN.md", "PRD.md", "DECISIONS.md", "REVIEW.md",
             "DATA_PROFILE.md", "START_TIME.txt"}
SELF_FILE = Path(__file__).resolve()
ROW_LIMIT = 200000                # 표 하나당 이 행 수까지 전체 읽기, 넘으면 표본
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tif", ".tiff", ".webp"}
PER_EXT_LIMIT = 15


def check_env():
    git = "저장소 아님 (git init 필요)"
    try:
        r = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                           capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            git = "저장소 맞음"
    except Exception:
        git = "git 실행 불가"
    base = ", ".join(f"{m}({'설치됨' if HAS[m] else '미설치'})" for m in BASE)
    opt = ", ".join(f"{m}({'설치됨' if HAS[m] else '없음'})" for m in OPTIONAL)
    lines = ["## 0. 환경 점검", f"- Python: {sys.version.split()[0]}", f"- Git: {git}",
             f"- 기본 패키지: {base}", f"- 선택 패키지 (필요할 때만 제안): {opt}"]
    miss = [BASE[m] for m in ("pandas", "openpyxl", "pdfplumber", "PIL") if not HAS[m]]
    if miss:
        lines.append(f"- 기본 패키지 미설치: {' '.join(miss)} -> README 3) 설치 후 다시 실행")
    return "\n".join(lines) + "\n"


def warnings_for(df):
    """판별 오류 의심 신호. 하나라도 있으면 '확인 필요'로 출력."""
    import pandas as pd
    w = []
    if df.shape[1] == 1 and any(s in str(df.columns[0]) for s in [";", "\t", "|"]):
        w.append("열이 1개인데 헤더에 구분자 문자 포함 -> 구분자 판별 오류 의심")
    unnamed = [c for c in df.columns if str(c).startswith("Unnamed")]
    if df.shape[1] and len(unnamed) > df.shape[1] / 2:
        w.append("이름 없는 열이 절반 이상 -> 헤더가 첫 행이 아닐 수 있음")
    allnull = [str(c) for c in df.columns if len(df) and df[c].isnull().all()]
    if allnull:
        w.append(f"전부 비어 있는 열 {allnull[:5]} -> 수식 캐시값 없음/인코딩 오류 가능")
    text_cols = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])
                 and not pd.api.types.is_datetime64_any_dtype(df[c])]
    for c in text_cols[:30]:
        s = df[c].dropna().astype(str).str.replace(",", "", regex=False).str.strip()
        if len(s) >= 3:
            conv = pd.to_numeric(s, errors="coerce").notna().mean()
            if conv >= 0.7:
                w.append(f"열 '{c}'은 숫자로 보이나 문자로 읽힘 (천 단위 쉼표, '-' 등) -> 숫자 변환 필요")
    return w


def summarize_df(df, basis):
    out = [f"- 통계 기준: {basis}"]
    cols = [f"{c}({t})" for c, t in df.dtypes.astype(str).items()]
    out.append(f"- 열({len(cols)}): {', '.join(cols[:40])}" + (" ..." if len(cols) > 40 else ""))
    nulls = df.isnull().mean()
    nulls = {str(c): f"{v:.1%}" for c, v in nulls[nulls > 0].items()}
    out.append(f"- 결측 비율: {nulls if nulls else '결측 없음'}")
    num = df.select_dtypes(include="number")
    if not num.empty:
        desc = num.iloc[:, :20].agg(["min", "mean", "max"]).T.round(4)
        out.append("- 숫자열 min/mean/max:\n```\n" + desc.to_string() + "\n```")
    out.append("- 앞 3행:\n```\n" + df.head(3).to_string(max_colwidth=30) + "\n```")
    for w in warnings_for(df):
        out.append(f"- 확인 필요: {w}")
    return out


def detect_encoding(raw):
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return ["utf-16"]
    return ["utf-8-sig", "cp949", "euc-kr", "latin-1"]


def detect_sep(text, suffix):
    if suffix == ".tsv":
        return "\t"
    try:
        return csv.Sniffer().sniff(text[:65536], delimiters=",;\t|").delimiter
    except Exception:
        return ","


def profile_csv(path):
    if not HAS["pandas"]:
        return f"- {path.name} (pandas 미설치)"
    import pandas as pd
    raw = path.read_bytes()[:65536]
    last = ""
    for enc in detect_encoding(raw):
        try:
            sample = raw.decode(enc, errors="strict") if enc != "utf-16" else raw.decode("utf-16", errors="ignore")
        except UnicodeDecodeError as e:
            last = str(e)
            continue
        sep = detect_sep(sample, path.suffix.lower())
        try:
            df = pd.read_csv(path, encoding=enc, sep=sep, nrows=ROW_LIMIT + 1)
            break
        except UnicodeDecodeError as e:
            last = str(e)
            continue
        except Exception as e:
            return f"- {path.name} (처리 실패: {str(e)[:100]})"
    else:
        return f"- {path.name} (인코딩 판별 실패: {last[:80]})"
    if len(df) > ROW_LIMIT:
        df = df.iloc[:ROW_LIMIT]
        rows, basis = f"{ROW_LIMIT}행 초과", f"앞 {ROW_LIMIT}행 표본 (전체 아님, 최종 수치에 쓰지 말 것)"
    else:
        rows, basis = f"{len(df)}행 (전체, 헤더 제외)", "전체 행"
    sep_name = {"\t": "탭", ",": "쉼표", ";": "세미콜론", "|": "세로막대"}.get(sep, sep)
    res = [f"### 표: {path.name}",
           f"- 인코딩: {enc} / 구분자: {sep_name} / 크기: {path.stat().st_size/1024**2:.1f}MB / {rows} x {df.shape[1]}열"]
    if enc == "latin-1":
        res.append("- 확인 필요: latin-1로 읽힘 -> 한글이면 인코딩 오류 가능")
    return "\n".join(res + summarize_df(df, basis))


def profile_excel(path):
    if not (HAS["pandas"] and HAS["openpyxl"]):
        return f"- Excel: {path.name} (pandas 또는 openpyxl 미설치)"
    import pandas as pd
    try:
        sheets = pd.ExcelFile(path).sheet_names
    except Exception as e:
        return f"- Excel: {path.name} (처리 실패: {str(e)[:100]})"
    res = [f"### Excel: {path.name}", f"- 시트 {len(sheets)}개: {sheets}"]
    for i, name in enumerate(sheets):
        if i >= 10:
            res.append(f"- 나머지 시트 {len(sheets) - 10}개 생략")
            break
        try:
            df = pd.read_excel(path, sheet_name=name, nrows=ROW_LIMIT + 1)
        except Exception as e:
            res.append(f"#### 시트 [{name}] 처리 실패: {str(e)[:100]}")
            continue
        df = df.dropna(how="all")  # 서식만 있는 빈 행 제외
        if len(df) > ROW_LIMIT:
            df = df.iloc[:ROW_LIMIT]
            head, basis = f"{ROW_LIMIT}행 초과", f"앞 {ROW_LIMIT}행 표본 (전체 아님)"
        else:
            head, basis = f"{len(df)}행 (전체, 헤더·빈 행 제외)", "전체 행"
        res.append(f"#### 시트 [{name}] {head} x {df.shape[1]}열")
        res += summarize_df(df, basis)
    return "\n".join(res)


def profile_pdf(path):
    if not HAS["pdfplumber"]:
        return f"- PDF: {path.name} (pdfplumber 미설치)"
    import pdfplumber
    try:
        with pdfplumber.open(path) as pdf:
            n = len(pdf.pages)
            info = [f"{p.page_number}쪽 글자 {len(p.extract_text() or '')} 표 {len(p.find_tables())}"
                    for p in pdf.pages[:5]]
        res = f"- PDF: {path.name} 총 {n}쪽{' (앞 5쪽만)' if n > 5 else ''} | " + " / ".join(info)
        if all(" 글자 0 " in s for s in info):
            res += "\n- 확인 필요: 글자가 없음 -> 스캔 PDF일 수 있음 (이미지로 읽어야 함)"
        return res
    except Exception as e:
        return f"- PDF: {path.name} (처리 실패: {str(e)[:100]})"


def profile_image(path):
    if not HAS["PIL"]:
        return f"- 이미지: {path.name} (Pillow 미설치)"
    from PIL import Image
    try:
        with Image.open(path) as img:
            return f"- 이미지: {path.name} ({img.format}, {img.size[0]}x{img.size[1]}, {img.mode})"
    except Exception as e:
        return f"- 이미지: {path.name} (처리 실패: {str(e)[:100]})"


def profile_json(path):
    import json
    try:
        size_mb = path.stat().st_size / 1024**2
        if path.suffix.lower() == ".jsonl":
            with path.open("r", encoding="utf-8", errors="replace") as f:
                lines = [f.readline() for _ in range(5)]
            lines = [l.strip() for l in lines if l.strip()]
            sample = json.loads(lines[0]) if lines else {}
            keys = list(sample.keys())[:20] if isinstance(sample, dict) else type(sample).__name__
            return f"### JSONL: {path.name} ({size_mb:.1f}MB)\n- 첫 줄 키/타입: {keys}\n- 첫 줄 예시: `{str(sample)[:200]}`"
        raw = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        if isinstance(raw, list):
            k = list(raw[0].keys())[:20] if raw and isinstance(raw[0], dict) else (type(raw[0]).__name__ if raw else "빈 배열")
            return f"### JSON 배열: {path.name} ({size_mb:.1f}MB, 총 {len(raw)}건)\n- 원소 키/타입: {k}\n- 첫 원소: `{str(raw[0])[:200] if raw else ''}`"
        elif isinstance(raw, dict):
            return f"### JSON 객체: {path.name} ({size_mb:.1f}MB)\n- 최상위 키({len(raw)}개): {list(raw.keys())[:30]}"
        return f"### JSON: {path.name} ({type(raw).__name__})"
    except Exception as e:
        return f"- JSON: {path.name} (처리 실패: {str(e)[:100]})"


def profile_sqlite(path):
    import sqlite3
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        cur = conn.cursor()
        tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        info = [f"### SQLite: {path.name} (테이블 {len(tables)}개: {tables})"]
        for t in tables[:10]:
            cnt = cur.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
            cols = [f"{c[1]}({c[2]})" for c in cur.execute(f'PRAGMA table_info("{t}")').fetchall()]
            info.append(f"- [{t}] {cnt}행 | 열: {', '.join(cols[:20])}")
        conn.close()
        return "\n".join(info)
    except Exception as e:
        return f"- SQLite: {path.name} (처리 실패: {str(e)[:100]})"


def profile_parquet(path):
    try:
        import pandas as pd
        df = pd.read_parquet(path)
        size_mb = path.stat().st_size / 1024**2
        return f"### Parquet: {path.name} ({size_mb:.1f}MB, 총 {len(df)}행 x {len(df.columns)}열)\n- 열: {', '.join(list(df.columns)[:20])}"
    except Exception:
        return f"- Parquet: {path.name} (파싱 실패 또는 pyarrow 미설치)"


def main():
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    files, skipped = [], []
    for root, dirs, names in os.walk(target):
        skipped += [d for d in dirs if d in EXCLUDE_DIRS]
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for n in names:
            p = Path(root) / n
            if p.resolve() == SELF_FILE or (n in KIT_FILES and Path(root).resolve() == target.resolve()):
                continue
            files.append(p)
    files.sort()

    by_ext = {}
    for f in files:
        by_ext.setdefault(f.suffix.lower() or "(없음)", []).append(f)
    report = ["# DATA_PROFILE", check_env(), "## 1. 파일 목록",
              "- 확장자별: " + ", ".join(f"{e} {len(v)}개" for e, v in sorted(by_ext.items()))]
    listing = [f"  - {f.relative_to(target)} ({f.stat().st_size/1024:.0f}KB)" for f in files[:80]]
    if len(files) > 80:
        listing.append(f"  - 외 {len(files) - 80}개 생략")
    report.append("\n".join(listing))
    if skipped:
        report.append(f"- 탐색 제외 폴더: {sorted(set(skipped))}")

    report.append("\n## 2. 형식별 요약")
    handlers = [
        ({".csv", ".tsv", ".txt"}, profile_csv),
        ({".xlsx", ".xlsm"}, profile_excel),
        ({".pdf"}, profile_pdf),
        (IMAGE_EXTS, profile_image),
        ({".json", ".jsonl"}, profile_json),
        ({".sqlite", ".sqlite3", ".db"}, profile_sqlite),
        ({".parquet"}, profile_parquet),
    ]
    for exts, fn in handlers:
        targets = [f for f in files if f.suffix.lower() in exts]
        if fn is profile_csv:  # .txt는 표처럼 보일 때만
            targets = [f for f in targets if f.suffix.lower() != ".txt" or _looks_tabular(f)]
        for f in targets[:PER_EXT_LIMIT]:
            report.append(fn(f))
        if len(targets) > PER_EXT_LIMIT:
            report.append(f"- ({'/'.join(sorted(exts))}) {len(targets) - PER_EXT_LIMIT}개는 요약 생략")
    handled = set().union(*(e for e, _ in handlers))
    others = [f.name for f in files if f.suffix.lower() not in handled or
              (f.suffix.lower() == ".txt" and not _looks_tabular(f))]
    if others:
        report.append(f"- 자동 요약 대상 아님 (직접 확인): {', '.join(others[:30])}")

    out = Path("DATA_PROFILE.md")
    out.write_text("\n\n".join(report) + "\n", encoding="utf-8")
    print(f"[완료] {out.resolve()} 생성 (파일 {len(files)}개)")


def _looks_tabular(path):
    try:
        head = path.read_bytes()[:4096].decode("utf-8", errors="ignore").splitlines()[:5]
        return len(head) >= 2 and all(any(s in l for s in ",\t;|") for l in head)
    except Exception:
        return False


if __name__ == "__main__":
    main()
