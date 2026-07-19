from __future__ import annotations

import json
import re
from pathlib import Path

import fitz

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
}

HEADER_RE = re.compile(r"Question #(\d+) \(1 Point\)")


def get_question_rect(page: fitz.Page, question_id: int) -> fitz.Rect | None:
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


def ensure_media_for_exam(exam_id: str, question_ids: list[int]) -> dict[int, str]:
    pdf_path = QUESTIONS_DIR / QUESTION_PDFS[exam_id]
    doc = fitz.open(pdf_path)

    out_dir = ASSETS_DIR / exam_id
    out_dir.mkdir(parents=True, exist_ok=True)

    q_to_src: dict[int, str] = {}

    # Build page->question ids from report (question id might appear once there)
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    page_map = {item["questionId"]: item["page"] - 1 for item in report.get(exam_id, [])}

    for qid in question_ids:
        page_index = page_map.get(qid)
        if page_index is None or not (0 <= page_index < len(doc)):
            continue

        page = doc[page_index]
        rect = get_question_rect(page, qid)
        if rect is None:
            continue

        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0), clip=rect, alpha=False)
        file_path = out_dir / f"q{qid}.png"
        pix.save(file_path)

        q_to_src[qid] = f"assets/questions/{exam_id}/q{qid}.png"

    return q_to_src


def merge_media_into_exam_json(exam_id: str, q_to_src: dict[int, str]):
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


def main():
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    for exam_id in ["A", "B", "C", "D"]:
        qids = sorted({int(item["questionId"]) for item in report.get(exam_id, [])})
        mapping = ensure_media_for_exam(exam_id, qids)
        merge_media_into_exam_json(exam_id, mapping)
        print(exam_id, "media questions:", sorted(mapping.keys()))


if __name__ == "__main__":
    main()
