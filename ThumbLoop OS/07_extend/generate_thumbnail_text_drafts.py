import csv
import random
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
SEED_CSV = BASE_DIR / "07_extend" / "thumbnail_text_seed_topics.csv"
PATTERN_CSV = BASE_DIR / "07_extend" / "ctr_pattern_library.csv"
OPERATIONS_CSV = BASE_DIR / "01_input" / "thumbnail_operations.csv"


TEMPLATES = {
    "warning": [
        "{topic} 모르면 손해봅니다",
        "{topic} 이거 모르고 쓰면 후회",
        "{topic} 아직도 이렇게 하면 손해",
    ],
    "mistake": [
        "{topic} 샀다가 많이 하는 실수",
        "{topic} 괜히 이렇게 쓰면 망합니다",
        "{topic} 대부분 여기서 후회함",
    ],
    "secret": [
        "{topic} 잘 팔리는 의외의 이유",
        "{topic} 아무도 안 알려주는 포인트",
        "{topic} 숨은 핵심만 보면 됩니다",
    ],
    "reason": [
        "{topic} 사람들이 찾는 이유",
        "{topic} 왜 이게 잘 팔릴까",
        "{topic} 계속 찾는 데는 이유가 있음",
    ],
    "comparison": [
        "{topic} 비슷해 보여도 차이 큼",
        "{topic} 싼 거랑 비교하면 다름",
        "{topic} 뭐가 더 나은지 바로 보임",
    ],
    "benefit": [
        "{topic} 진짜 편한 핵심 기능",
        "{topic} 엄마들이 많이 찾는 포인트",
        "{topic} 써보면 바로 체감되는 장점",
    ],
    "loss": [
        "{topic} 이 기능 없으면 돈 버림",
        "{topic} 잘못 사면 돈만 날림",
        "{topic} 이거 빠지면 다시 사게 됨",
    ],
    "curiosity": [
        "{topic} 왜 다들 이걸 찾을까",
        "{topic} 이거 하나로 반응 달라짐",
        "{topic} 진짜 차이 나는 부분은 따로 있음",
    ],
    "proof": [
        "{topic} 직접 보면 바로 이해됨",
        "{topic} 써본 사람들 반응이 갈림",
        "{topic} 실제로 비교해보니 달랐음",
    ],
    "reaction": [
        "{topic} 엄마들 반응이 달랐던 이유",
        "{topic} 후기에서 계속 나온 말",
        "{topic} 반응 좋은 제품들의 공통점",
    ],
}


def safe_str(v) -> str:
    return "" if v is None else str(v).strip()


def read_csv_rows(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv_rows(path: Path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_top_patterns():
    rows = read_csv_rows(PATTERN_CSV)
    if not rows:
        return ["curiosity", "benefit", "warning"]
    rows = sorted(rows, key=lambda r: float(r.get("avg_ctr", 0)), reverse=True)
    return [safe_str(r["pattern_name"]) for r in rows[:3] if safe_str(r.get("pattern_name"))]


def generate_pair(topic: str, patterns):
    usable = [p for p in patterns if p in TEMPLATES]
    if len(usable) < 2:
        usable = ["curiosity", "benefit", "warning"]

    p1, p2 = usable[0], usable[1]
    t1 = random.choice(TEMPLATES[p1]).format(topic=topic)
    t2 = random.choice(TEMPLATES[p2]).format(topic=topic)
    return p1, t1, p2, t2


def main() -> int:
    seed_rows = read_csv_rows(SEED_CSV)
    if not seed_rows:
        print("[안내] thumbnail_text_seed_topics.csv가 비어 있습니다.")
        return 0

    top_patterns = load_top_patterns()
    existing_rows = read_csv_rows(OPERATIONS_CSV)

    existing_ids = {safe_str(r.get("content_id")) for r in existing_rows}
    output_rows = existing_rows[:] if existing_rows else []

    fieldnames = [
        "content_id",
        "topic",
        "thumbnail_text_a",
        "thumbnail_text_b",
        "thumbnail_text_final",
        "style_preset",
        "text_layout_preset",
        "review_status",
        "generation_pattern_a",
        "generation_pattern_b",
    ]

    if output_rows:
        existing_fields = list(output_rows[0].keys())
        for f in fieldnames:
            if f not in existing_fields:
                existing_fields.append(f)
        fieldnames = existing_fields

    for row in seed_rows:
        content_id = safe_str(row.get("content_id"))
        topic = safe_str(row.get("topic"))
        style_preset = safe_str(row.get("style_preset")) or "default"
        layout_preset = safe_str(row.get("text_layout_preset")) or "bottom_big"

        if not content_id or not topic:
            continue
        if content_id in existing_ids:
            continue

        p1, text_a, p2, text_b = generate_pair(topic, top_patterns)

        output_rows.append({
            "content_id": content_id,
            "topic": topic,
            "thumbnail_text_a": text_a,
            "thumbnail_text_b": text_b,
            "thumbnail_text_final": "",
            "style_preset": style_preset,
            "text_layout_preset": layout_preset,
            "review_status": "draft_generated",
            "generation_pattern_a": p1,
            "generation_pattern_b": p2,
        })

    write_csv_rows(OPERATIONS_CSV, output_rows, fieldnames)
    print("[완료] thumbnail_operations.csv에 신규 문구 초안이 추가되었습니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())