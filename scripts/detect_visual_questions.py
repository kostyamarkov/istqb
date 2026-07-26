from __future__ import annotations

import json
import re
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS_DIR = ROOT / "Questions"

QUESTION_PDFS = {
    "A": "ISTQB_CTFL_v4.0_Sample-Exam-A-Questions_v1.7.pdf",
    "B": "ISTQB_CTFL_v4.0_Sample-Exam-B-Questions_v1.7.pdf",
    "C": "ISTQB_CTFL_v4.0_Sample-Exam-C-Questions_v1.6.pdf",
    "D": "ISTQB_CTFL_v4.0_Sample-Exam-D-Questions_v1.5.pdf",
    "ADV1": "ISTQB-CTAL-TA-Sample-Exam-Questions-v4.1.pdf",
}

HEADER_RE = re.compile(r"Question #(\d+) \(\d+ Point\)")
KEYWORDS_RE = re.compile(r"\b(table|figure|diagram|shown below|following table|decision table|state transition)\b", re.I)


def detect_for_exam(exam_id: str, pdf_path: Path):
    doc = fitz.open(pdf_path)
    found = []

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        page_dict = page.get_text("dict")

        # Collect text lines with rough Y positions
        lines = []
        for block in page_dict.get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue
                text = "".join(span.get("text", "") for span in spans).strip()
                if not text:
                    continue
                y0 = min(span.get("bbox", [0, 0, 0, 0])[1] for span in spans)
                y1 = max(span.get("bbox", [0, 0, 0, 0])[3] for span in spans)
                lines.append((y0, y1, text))

        lines.sort(key=lambda item: item[0])

        question_positions = []
        for y0, y1, text in lines:
            m = HEADER_RE.search(text)
            if m:
                qnum = int(m.group(1))
                if 1 <= qnum <= 40:
                    question_positions.append((qnum, y0, y1))

        if not question_positions:
            continue

        drawings = page.get_drawings()
        images = [b for b in page_dict.get("blocks", []) if b.get("type") == 1]

        for idx, (qnum, y0, _y1) in enumerate(question_positions):
            next_y = question_positions[idx + 1][1] if idx + 1 < len(question_positions) else page.rect.height - 20
            span_top = y0
            span_bottom = next_y

            text_in_span = " ".join(
                t for ly0, ly1, t in lines if not (ly1 < span_top or ly0 > span_bottom)
            )

            keyword_hit = bool(KEYWORDS_RE.search(text_in_span))

            image_hit = False
            for img in images:
                ib = img.get("bbox", [0, 0, 0, 0])
                iy0, iy1 = ib[1], ib[3]
                if not (iy1 < span_top or iy0 > span_bottom):
                    image_hit = True
                    break

            drawing_count = 0
            for dr in drawings:
                rb = dr.get("rect")
                if rb is None:
                    continue
                dy0, dy1 = rb.y0, rb.y1
                if not (dy1 < span_top or dy0 > span_bottom):
                    drawing_count += 1

            if keyword_hit or image_hit or drawing_count >= 10:
                found.append(
                    {
                        "examId": exam_id,
                        "questionId": qnum,
                        "page": page_idx + 1,
                        "keywordHit": keyword_hit,
                        "imageHit": image_hit,
                        "drawingCount": drawing_count,
                        "textSample": text_in_span[:220],
                    }
                )

    # Deduplicate by question, keep strongest signal
    best = {}
    for item in found:
        qid = item["questionId"]
        score = (3 if item["imageHit"] else 0) + (2 if item["keywordHit"] else 0) + min(item["drawingCount"], 10) / 10.0
        prev = best.get(qid)
        if prev is None:
            best[qid] = (score, item)
        else:
            prev_score = prev[0]
            if score > prev_score:
                best[qid] = (score, item)

    items = [v[1] for _, v in sorted(best.items(), key=lambda x: x[0])]
    return items


def main():
    all_results = {}
    for exam_id, filename in QUESTION_PDFS.items():
        pdf_path = QUESTIONS_DIR / filename
        all_results[exam_id] = detect_for_exam(exam_id, pdf_path)

    out = ROOT / "scripts" / "visual_questions_report.json"
    out.write_text(json.dumps(all_results, indent=2), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
