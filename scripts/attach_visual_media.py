from __future__ import annotations

import json
import re
from pathlib import Path

import fitz
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS_DIR = ROOT / "Questions"
DATA_DIR = ROOT / "data"
ASSETS_DIR = ROOT / "assets" / "questions"
REPORT_PATH = ROOT / "scripts" / "visual_questions_report.json"

QUESTION_PDFS = {
    "A": "ISTQB_CTFL_v4.0_Sample-Exam-A-Questions_v1.7.pdf",
    "B": "ISTQB_CTFL_v4.0_Sample-Exam-B-Questions_v1.7.pdf",
    "C": "ISTQB_CTFL_v4.0_Sample-Exam-C-Questions_v1.6.pdf",
    "D": "ISTQB_CTFL_v4.0_Sample-Exam-D-Questions_v1.5.pdf",
    "ADV1": "ISTQB-CTAL-TA-Sample-Exam-Questions-v4.1.pdf",
}

HEADER_RE = re.compile(r"Question #(\d+) \(\d+ Point\)")

ADV1_PAGE_HINTS = {
    10: 12,
    18: 18,
    21: 21,
    22: 22,
    23: 23,
}


def get_question_span(page: fitz.Page, question_id: int) -> fitz.Rect | None:
    text = page.get_text("dict")

    # Gather line positions with question markers.
    lines = []
    for block in text.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            if not spans:
                continue
            line_text = "".join(span.get("text", "") for span in spans).strip()
            if not line_text:
                continue
            y0 = min(span.get("bbox", [0, 0, 0, 0])[1] for span in spans)
            y1 = max(span.get("bbox", [0, 0, 0, 0])[3] for span in spans)
            lines.append((y0, y1, line_text))

    lines.sort(key=lambda item: item[0])

    q_headers = []
    for y0, y1, line_text in lines:
        m = HEADER_RE.search(line_text)
        if m:
            q_headers.append((int(m.group(1)), y0, y1))

    for idx, (qid, y0, _y1) in enumerate(q_headers):
        if qid != question_id:
            continue

        next_y = q_headers[idx + 1][1] if idx + 1 < len(q_headers) else page.rect.height - 24

        top = max(24, y0 + 24)
        bottom = max(top + 40, next_y - 6)

        # Attempt to end crop at select-options line so we focus on scenario/table/diagram
        select_line_bottom = None
        for ly0, ly1, lt in lines:
            if ly0 < top or ly1 > bottom:
                continue
            if "Select ONE option" in lt or "Select TWO options" in lt:
                select_line_bottom = ly0 - 8
                break

        if select_line_bottom is not None and select_line_bottom > top + 40:
            bottom = select_line_bottom

        rect = fitz.Rect(28, top, page.rect.width - 28, bottom)
        if rect.height < 40:
            return None
        return rect

    return None


def get_visual_rect_in_span(page: fitz.Page, span_rect: fitz.Rect) -> fitz.Rect | None:
    candidates: list[fitz.Rect] = []

    for drawing in page.get_drawings():
        rect = drawing.get("rect")
        if rect is None:
            continue
        if rect.intersects(span_rect):
            inter = rect & span_rect
            if inter.width >= 6 or inter.height >= 6:
                candidates.append(inter)

    page_dict = page.get_text("dict")
    for block in page_dict.get("blocks", []):
        if block.get("type") != 1:
            continue
        bbox = block.get("bbox", [0, 0, 0, 0])
        rect = fitz.Rect(bbox)
        if rect.intersects(span_rect):
            inter = rect & span_rect
            if inter.width >= 8 and inter.height >= 8:
                candidates.append(inter)

    if not candidates:
        return None

    # Cluster nearby primitives and pick the biggest visual block.
    clusters: list[list[fitz.Rect]] = []
    for rect in sorted(candidates, key=lambda r: (r.y0, r.x0)):
        placed = False
        for cluster in clusters:
            cluster_union = fitz.Rect(cluster[0])
            for crect in cluster[1:]:
                cluster_union.include_rect(crect)

            vertical_close = not (rect.y0 > cluster_union.y1 + 8 or rect.y1 < cluster_union.y0 - 8)
            horizontal_overlap = not (rect.x0 > cluster_union.x1 + 20 or rect.x1 < cluster_union.x0 - 20)
            if vertical_close and horizontal_overlap:
                cluster.append(rect)
                placed = True
                break

        if not placed:
            clusters.append([rect])

    best_union = None
    best_area = -1.0
    for cluster in clusters:
        union = fitz.Rect(cluster[0])
        for crect in cluster[1:]:
            union.include_rect(crect)
        area = union.width * union.height
        if area > best_area:
            best_area = area
            best_union = union

    if best_union is None:
        return None

    # Expand slightly to include labels around diagrams/tables.
    union_rect = best_union
    union_rect.x0 = max(span_rect.x0, union_rect.x0 - 4)
    union_rect.y0 = max(span_rect.y0, union_rect.y0 - 4)
    union_rect.x1 = min(span_rect.x1, union_rect.x1 + 4)
    union_rect.y1 = min(span_rect.y1, union_rect.y1 + 4)

    if union_rect.width < 80 or union_rect.height < 40:
        return None

    return union_rect


def ensure_media_for_exam(exam_id: str, question_ids: list[int]) -> dict[int, str]:
    pdf_path = QUESTIONS_DIR / QUESTION_PDFS[exam_id]
    doc = fitz.open(pdf_path)

    out_dir = ASSETS_DIR / exam_id
    out_dir.mkdir(parents=True, exist_ok=True)

    q_to_src: dict[int, str] = {}

    # Build page->question ids from report (question id might appear once there)
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    report_items = {item["questionId"]: item for item in report.get(exam_id, [])}
    page_map = {qid: item["page"] - 1 for qid, item in report_items.items()}

    if exam_id == "ADV1":
        for qid, page_index in ADV1_PAGE_HINTS.items():
            if qid not in question_ids:
                continue
            if not (0 <= page_index < len(doc)):
                continue

            page = doc[page_index]
            visual_rect = get_visual_rect_in_span(page, page.rect)
            if visual_rect is None:
                continue

            pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0), clip=visual_rect, alpha=False)
            file_path = out_dir / f"q{qid}.png"
            pix.save(file_path)
            q_to_src[qid] = f"assets/questions/{exam_id}/q{qid}.png"

        return q_to_src

    for qid in question_ids:
        item_meta = report_items.get(qid)
        if item_meta is None:
            continue

        # Skip weak detections that usually correspond to plain text questions.
        if not (
            item_meta.get("imageHit")
            or item_meta.get("keywordHit")
            or int(item_meta.get("drawingCount", 0)) >= 20
        ):
            continue

        page_index = page_map.get(qid)
        if page_index is None or not (0 <= page_index < len(doc)):
            continue

        page = doc[page_index]
        span_rect = get_question_span(page, qid)
        if span_rect is None:
            continue

        visual_rect = get_visual_rect_in_span(page, span_rect)
        if visual_rect is None:
            continue

        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0), clip=visual_rect, alpha=False)
        file_path = out_dir / f"q{qid}.png"
        pix.save(file_path)

        if item_meta.get("imageHit"):
            trim_image_tail(file_path)

        q_to_src[qid] = f"assets/questions/{exam_id}/q{qid}.png"

    return q_to_src


def merge_media_into_exam_json(exam_id: str, q_to_src: dict[int, str]):
    if exam_id == "ADV1":
        path = DATA_DIR / "exam_advanced_1.json"
    else:
        path = DATA_DIR / f"exam_{exam_id}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))

    for question in payload["questions"]:
        qid = int(question["id"])
        src = q_to_src.get(qid)
        if not src:
            question.pop("media", None)
            continue

        question["media"] = [
            {
                "type": "image",
                "src": src,
                "alt": f"Question {qid} reference image",
            }
        ]

    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def trim_image_tail(file_path: Path) -> None:
    img = Image.open(file_path).convert("RGB")
    width, height = img.size
    pixels = img.load()

    bg = pixels[0, 0]

    def row_ratio(y: int) -> float:
        changed = 0
        for x in range(width):
            r, g, b = pixels[x, y]
            if abs(r - bg[0]) > 18 or abs(g - bg[1]) > 18 or abs(b - bg[2]) > 18:
                changed += 1
        return changed / width

    ratios = [row_ratio(y) for y in range(height)]

    active = [r >= 0.001 for r in ratios]

    runs: list[tuple[int, int, float]] = []
    i = 0
    while i < height:
        if not active[i]:
            i += 1
            continue

        start = i
        mass = 0.0
        while i < height and active[i]:
            mass += ratios[i]
            i += 1
        end = i - 1
        runs.append((start, end, mass))

    if not runs:
        return

    # Keep the dominant visual run and drop detached tails.
    top, bottom, _ = max(runs, key=lambda r: ((r[1] - r[0] + 1), r[2]))

    # Small breathing room.
    top = max(0, top - 1)
    bottom = min(height - 1, bottom + 1)

    crop = img.crop((0, top, width, bottom + 1))
    crop.save(file_path)


def main():
    qids = sorted(ADV1_PAGE_HINTS)
    mapping = ensure_media_for_exam("ADV1", qids)
    merge_media_into_exam_json("ADV1", mapping)
    print("ADV1", "media questions:", sorted(mapping.keys()))


if __name__ == "__main__":
    main()
