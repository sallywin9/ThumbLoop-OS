import csv
import os
import sys
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
from PIL import Image, ImageDraw, ImageFont
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


CANVAS_SIZE = (1080, 1920)

def ensure_dirs() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_font(size: int) -> ImageFont.FreeTypeFont:
    if FONT_PATH.exists():
        return ImageFont.truetype(str(FONT_PATH), size=size)
    return ImageFont.load_default()


def safe_str(v) -> str:
    return "" if v is None else str(v).strip()


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"운영 CSV가 없습니다: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def append_csv_row(path: Path, fieldnames: List[str], row: Dict[str, str]) -> None:
    file_exists = path.exists()
    with path.open("a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def get_background_path(style_preset: str) -> Path:
    style_key = safe_str(style_preset).lower()
    candidate = ASSETS_DIR / "backgrounds" / f"{style_key}.jpg"
    if candidate.exists():
        return candidate
    return DEFAULT_BG


def open_background(style_preset: str) -> Image.Image:
    bg_path = get_background_path(style_preset)
    if bg_path.exists():
        img = Image.open(bg_path).convert("RGB")
        return img.resize(CANVAS_SIZE)
    return Image.new("RGB", CANVAS_SIZE, color=(30, 30, 30))


def draw_overlay(draw: ImageDraw.ImageDraw, layout: str) -> None:
    w, h = CANVAS_SIZE
    layout = safe_str(layout).lower()

    if layout == "top_big":
        draw.rectangle([(0, 0), (w, int(h * 0.38))], fill=(0, 0, 0, 160))
    elif layout == "center_focus":
        draw.rectangle([(60, int(h * 0.35)), (w - 60, int(h * 0.68))], fill=(0, 0, 0, 170))
    else:  # bottom_big
        draw.rectangle([(0, int(h * 0.58)), (w, h)], fill=(0, 0, 0, 170))


def wrap_text(text: str, width: int) -> str:
    lines = textwrap.wrap(text, width=width, break_long_words=False, replace_whitespace=False)
    return "\n".join(lines[:3])


def text_block_position(layout: str) -> Tuple[int, int]:
    w, h = CANVAS_SIZE
    layout = safe_str(layout).lower()

    if layout == "top_big":
        return 70, 110
    if layout == "center_focus":
        return 90, int(h * 0.41)
    return 70, int(h * 0.68)


def draw_text_with_outline(draw: ImageDraw.ImageDraw, position: Tuple[int, int], text: str, font, fill="white") -> None:
    x, y = position
    outline_color = "black"
    for ox in (-3, -2, -1, 0, 1, 2, 3):
        for oy in (-3, -2, -1, 0, 1, 2, 3):
            if ox == 0 and oy == 0:
                continue
            draw.multiline_text((x + ox, y + oy), text, font=font, fill=outline_color, spacing=12)
    draw.multiline_text((x, y), text, font=font, fill=fill, spacing=12)


def render_thumbnail(
    content_id: str,
    text_value: str,
    style_preset: str,
    layout_preset: str,
    variant: str,
) -> str:
    img = open_background(style_preset)
    draw = ImageDraw.Draw(img, "RGBA")
    draw_overlay(draw, layout_preset)

    font = load_font(92)
    wrapped = wrap_text(text_value, width=10)
    pos = text_block_position(layout_preset)
    draw_text_with_outline(draw, pos, wrapped, font)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{content_id}_{variant}_{timestamp}.jpg"
    output_path = OUTPUT_DIR / filename
    img.save(output_path, quality=95)
    return str(output_path.relative_to(BASE_DIR))


def ensure_experiments_csv() -> None:
    if EXPERIMENTS_CSV.exists():
        return

    fieldnames = [
        "experiment_id",
        "content_id",
        "variant",
        "thumbnail_path",
        "thumbnail_text",
        "style_preset",
        "text_layout_preset",
        "status",
        "impressions",
        "views",
        "ctr",
        "winner",
        "notes",
        "created_at",
        "updated_at",
    ]
    with EXPERIMENTS_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()


def register_experiment(
    content_id: str,
    variant: str,
    thumbnail_path: str,
    thumbnail_text: str,
    style_preset: str,
    layout_preset: str,
) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    experiment_id = f"{content_id}_{variant}"
    fieldnames = [
        "experiment_id",
        "content_id",
        "variant",
        "thumbnail_path",
        "thumbnail_text",
        "style_preset",
        "text_layout_preset",
        "status",
        "impressions",
        "views",
        "ctr",
        "winner",
        "notes",
        "created_at",
        "updated_at",
    ]
    row = {
        "experiment_id": experiment_id,
        "content_id": content_id,
        "variant": variant,
        "thumbnail_path": thumbnail_path,
        "thumbnail_text": thumbnail_text,
        "style_preset": style_preset,
        "text_layout_preset": layout_preset,
        "status": "rendered",
        "impressions": "",
        "views": "",
        "ctr": "",
        "winner": "",
        "notes": "",
        "created_at": now,
        "updated_at": now,
    }
    append_csv_row(EXPERIMENTS_CSV, fieldnames, row)


def pick_texts(row: Dict[str, str]) -> Tuple[str, str]:
    a = safe_str(row.get("thumbnail_text_a"))
    b = safe_str(row.get("thumbnail_text_b"))
    final_text = safe_str(row.get("thumbnail_text_final"))

    if not a and final_text:
        a = final_text
    if not b and final_text:
        b = final_text

    if not a:
        a = "기본 문구 A"
    if not b:
        b = "기본 문구 B"
    return a, b


def should_render(row: Dict[str, str]) -> bool:
    status = safe_str(row.get("review_status")).lower()
    if status in {"approved", "ready", "render_ready", "confirmed"}:
        return True
    return False


def main() -> int:
    ensure_dirs()
    ensure_experiments_csv()

    try:
        rows = read_csv_rows(OPERATIONS_CSV)
    except Exception as e:
        print(f"[오류] {e}")
        return 1

    rendered_count = 0

    for row in rows:
        if not should_render(row):
            continue

        content_id = safe_str(row.get("content_id"))
        style_preset = safe_str(row.get("style_preset")) or "default"
        layout_preset = safe_str(row.get("text_layout_preset")) or "bottom_big"

        if not content_id:
            print("[건너뜀] content_id 없음")
            continue

        text_a, text_b = pick_texts(row)

        try:
            path_a = render_thumbnail(content_id, text_a, style_preset, layout_preset, "A")
            register_experiment(content_id, "A", path_a, text_a, style_preset, layout_preset)

            path_b = render_thumbnail(content_id, text_b, style_preset, layout_preset, "B")
            register_experiment(content_id, "B", path_b, text_b, style_preset, layout_preset)

            rendered_count += 2
            print(f"[완료] {content_id} → A/B 2장 생성 및 실험 등록")
        except Exception as e:
            print(f"[오류] {content_id}: {e}")

    print(f"\n총 생성 수: {rendered_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())