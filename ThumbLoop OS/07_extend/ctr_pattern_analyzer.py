import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean


BASE_DIR = Path(__file__).resolve().parent.parent
EXPERIMENTS_CSV = BASE_DIR / "03_experiment" / "thumbnail_experiments.csv"
OUTPUT_CSV = BASE_DIR / "07_extend" / "ctr_pattern_library.csv"


PATTERN_RULES = {
    "warning": [r"조심", r"주의", r"위험", r"큰일", r"절대", r"모르면"],
    "mistake": [r"실수", r"후회", r"망", r"괜히", r"잘못"],
    "secret": [r"비밀", r"의외", r"숨은", r"몰랐", r"아무도"],
    "reason": [r"이유", r"때문", r"원인", r"왜"],
    "comparison": [r"vs", r"차이", r"비교", r"보다", r"더"],
    "benefit": [r"좋은", r"편한", r"잘 팔", r"추천", r"핵심"],
    "loss": [r"손해", r"버림", r"낭비", r"돈 샌", r"돈 버림"],
    "curiosity": [r"이거", r"이것", r"이 한", r"진짜", r"정체"],
    "proof": [r"직접", r"써보", r"검증", r"실험", r"확인"],
    "reaction": [r"반응", r"후기", r"엄마들", r"다들", r"난리"],
}


def safe_str(v) -> str:
    return "" if v is None else str(v).strip()


def read_csv_rows(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"파일이 없습니다: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv_rows(path: Path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def to_float(v: str) -> float:
    try:
        return float(str(v).replace("%", "").strip())
    except Exception:
        return 0.0


def classify_pattern(text: str) -> str:
    t = safe_str(text)
    for pattern_name, rules in PATTERN_RULES.items():
        for rule in rules:
            if re.search(rule, t):
                return pattern_name
    return "curiosity"


def tokenize(text: str):
    text = safe_str(text)
    text = re.sub(r"[^가-힣a-zA-Z0-9\s]", " ", text)
    tokens = [x for x in text.split() if len(x) >= 2]
    return tokens


def main() -> int:
    try:
        rows = read_csv_rows(EXPERIMENTS_CSV)
    except Exception as e:
        print(f"[오류] {e}")
        return 1

    winner_rows = [r for r in rows if safe_str(r.get("winner")) == "Y"]
    if not winner_rows:
        print("[안내] winner=Y 데이터가 없습니다.")
        return 0

    pattern_ctrs = defaultdict(list)
    pattern_lengths = defaultdict(list)
    pattern_words = defaultdict(Counter)

    for row in winner_rows:
        text = safe_str(row.get("thumbnail_text"))
        ctr = to_float(row.get("ctr"))
        pattern = classify_pattern(text)

        pattern_ctrs[pattern].append(ctr)
        pattern_lengths[pattern].append(len(text))

        for token in tokenize(text):
            pattern_words[pattern][token] += 1

    output_rows = []
    for pattern_name, ctrs in pattern_ctrs.items():
        top_words = [w for w, _ in pattern_words[pattern_name].most_common(8)]
        avg_ctr = round(mean(ctrs), 4) if ctrs else 0.0
        avg_len = round(mean(pattern_lengths[pattern_name]), 1) if pattern_lengths[pattern_name] else 0.0

        output_rows.append({
            "pattern_name": pattern_name,
            "winner_count": len(ctrs),
            "avg_ctr": avg_ctr,
            "avg_length": avg_len,
            "top_words": ", ".join(top_words),
        })

    output_rows = sorted(output_rows, key=lambda x: float(x["avg_ctr"]), reverse=True)

    fieldnames = ["pattern_name", "winner_count", "avg_ctr", "avg_length", "top_words"]
    write_csv_rows(OUTPUT_CSV, output_rows, fieldnames)

    print("[완료] ctr_pattern_library.csv 생성 완료")
    for row in output_rows:
        print(
            f"- {row['pattern_name']} | "
            f"winner_count={row['winner_count']} | "
            f"avg_ctr={row['avg_ctr']} | "
            f"top_words={row['top_words']}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())