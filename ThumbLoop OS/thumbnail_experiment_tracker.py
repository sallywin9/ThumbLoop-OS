import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from project_config import (
    BASE_DIR,
    OPERATIONS_CSV,
    EXPERIMENTS_CSV,
    OUTPUT_DIR,
    ASSETS_DIR,
    FONT_PATH,
    DEFAULT_BG,
    DEFAULT_STYLE,
    DEFAULT_LAYOUT,
)


def safe_str(v) -> str:
    return "" if v is None else str(v).strip()


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"파일이 없습니다: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv_rows(path: Path, rows: List[Dict[str, str]], fieldnames: List[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def to_float(v: str) -> float:
    try:
        return float(str(v).replace("%", "").strip())
    except Exception:
        return 0.0


def calculate_ctr(impressions: str, views: str) -> float:
    imp = to_float(impressions)
    vw = to_float(views)
    if imp <= 0:
        return 0.0
    return round((vw / imp) * 100, 4)


def update_ctr(rows: List[Dict[str, str]]) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    for row in rows:
        impressions = safe_str(row.get("impressions"))
        views = safe_str(row.get("views"))
        ctr = calculate_ctr(impressions, views)
        row["ctr"] = str(ctr)
        row["updated_at"] = now


def decide_winners(rows: List[Dict[str, str]]) -> None:
    grouped = {}
    for row in rows:
        content_id = safe_str(row.get("content_id"))
        grouped.setdefault(content_id, []).append(row)

    now = datetime.now().isoformat(timespec="seconds")

    for content_id, items in grouped.items():
        if len(items) < 2:
            continue

        items_sorted = sorted(items, key=lambda r: to_float(r.get("ctr", "0")), reverse=True)
        top = items_sorted[0]
        second = items_sorted[1]

        top_ctr = to_float(top.get("ctr", "0"))
        second_ctr = to_float(second.get("ctr", "0"))

        winner_variant = ""
        if top_ctr > 0 and top_ctr > second_ctr:
            winner_variant = safe_str(top.get("variant"))

        for item in items:
            item["winner"] = "Y" if safe_str(item.get("variant")) == winner_variant and winner_variant else ""
            item["status"] = "winner_decided" if winner_variant else "metrics_pending"
            item["updated_at"] = now


def reflect_winner_to_operations(experiment_rows: List[Dict[str, str]]) -> None:
    if not OPERATIONS_CSV.exists():
        return

    op_rows = read_csv_rows(OPERATIONS_CSV)
    if not op_rows:
        return

    winner_map = {}
    for row in experiment_rows:
        if safe_str(row.get("winner")) == "Y":
            winner_map[safe_str(row.get("content_id"))] = {
                "winner_variant": safe_str(row.get("variant")),
                "winner_text": safe_str(row.get("thumbnail_text")),
                "winner_ctr": safe_str(row.get("ctr")),
            }

    if not winner_map:
        return

    fieldnames = list(op_rows[0].keys())
    extra_fields = ["last_winner_variant", "last_winner_text", "last_winner_ctr"]
    for ef in extra_fields:
        if ef not in fieldnames:
            fieldnames.append(ef)

    for row in op_rows:
        cid = safe_str(row.get("content_id"))
        if cid in winner_map:
            row["last_winner_variant"] = winner_map[cid]["winner_variant"]
            row["last_winner_text"] = winner_map[cid]["winner_text"]
            row["last_winner_ctr"] = winner_map[cid]["winner_ctr"]

    write_csv_rows(OPERATIONS_CSV, op_rows, fieldnames)


def print_summary(rows: List[Dict[str, str]]) -> None:
    grouped = {}
    for row in rows:
        content_id = safe_str(row.get("content_id"))
        grouped.setdefault(content_id, []).append(row)

    print("\n=== 썸네일 실험 요약 ===")
    for content_id, items in grouped.items():
        print(f"\n[content_id] {content_id}")
        for item in sorted(items, key=lambda r: safe_str(r.get("variant"))):
            print(
                f"  - variant={item.get('variant')} | "
                f"impressions={item.get('impressions')} | "
                f"views={item.get('views')} | "
                f"ctr={item.get('ctr')} | "
                f"winner={item.get('winner')}"
            )


def main() -> int:
    try:
        rows = read_csv_rows(EXPERIMENTS_CSV)
    except Exception as e:
        print(f"[오류] {e}")
        return 1

    if not rows:
        print("[안내] 실험 데이터가 없습니다.")
        return 0

    fieldnames = list(rows[0].keys())

    update_ctr(rows)
    decide_winners(rows)
    write_csv_rows(EXPERIMENTS_CSV, rows, fieldnames)
    reflect_winner_to_operations(rows)
    print_summary(rows)

    print("\n[완료] CTR 계산, 승자 결정, 운영 CSV 반영까지 끝났습니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())