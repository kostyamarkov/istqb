from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS_DIR = ROOT / "Questions"
ANSWERS_DIR = ROOT / "Answers"
OUTPUT_DIR = ROOT / "data"

HEADER_PATTERNS = [
    re.compile(r"^Certified Tester, Foundation Level\s*$"),
    re.compile(r"^Sample Exams? set [A-D]\s*$"),
    re.compile(r"^Sample Exam [–-] (Questions|Answers)\s*$"),
    re.compile(r"^Version .* Page \d+ of \d+ Release .*"),
    re.compile(r"^© International Software Testing Qualifications Board"),
    re.compile(r"^Question\s*$"),
    re.compile(r"^Number\s*$"),
    re.compile(r"^\(#\)\s*$"),
    re.compile(r"^Correct\s*$"),
    re.compile(r"^Answer\s*$"),
    re.compile(r"^Explanation / Rationale Learning\s*$"),
    re.compile(r"^Objective\s*$"),
    re.compile(r"^\(LO\)\s*$"),
    re.compile(r"^K-Level Number\s*$"),
    re.compile(r"^of\s*$"),
    re.compile(r"^Points\s*$"),
    re.compile(r"^Answers\s*$"),
]

INLINE_GARBAGE_PATTERNS = [
    re.compile(r"Certified Tester, Foundation Level", re.I),
    re.compile(r"Sample Exams? set [A-D]", re.I),
    re.compile(r"Sample Exam [–-] (Questions|Answers)", re.I),
    re.compile(r"Version\s+\d+(?:\.\d+)*", re.I),
    re.compile(r"Page\s+\d+\s+of\s+\d+", re.I),
    re.compile(
        r"Release\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}",
        re.I,
    ),
    re.compile(r"© International Software Testing Qualifications Board", re.I),
]


def extract_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def clean_lines(raw_text: str) -> List[str]:
    lines = [line.strip() for line in raw_text.splitlines()]
    cleaned: List[str] = []
    for line in lines:
        if not line:
            cleaned.append("")
            continue
        if any(pattern.match(line) for pattern in HEADER_PATTERNS):
            continue
        cleaned.append(line)
    return cleaned


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def strip_inline_garbage(text: str) -> str:
    cleaned = text
    for pattern in INLINE_GARBAGE_PATTERNS:
        cleaned = pattern.sub(" ", cleaned)
    return normalize_space(cleaned)


def parse_question_block(block: str) -> Dict:
    lines = [line.strip() for line in block.splitlines() if line.strip()]

    question_parts: List[str] = []
    options: List[Dict[str, str]] = []
    current_option_id = ""
    current_option_text: List[str] = []

    option_re = re.compile(r"^([a-z])\)\s*(.*)$")

    for line in lines:
        if line.startswith("Select "):
            continue

        m = option_re.match(line)
        if m:
            if current_option_id:
                options.append(
                    {
                        "id": current_option_id,
                        "text": strip_inline_garbage(" ".join(current_option_text)),
                    }
                )
            current_option_id = m.group(1)
            current_option_text = [m.group(2)]
            continue

        if current_option_id:
            current_option_text.append(line)
        else:
            question_parts.append(line)

    if current_option_id:
        options.append(
            {
                "id": current_option_id,
                "text": strip_inline_garbage(" ".join(current_option_text)),
            }
        )

    return {
        "text": strip_inline_garbage(" ".join(question_parts)),
        "options": options,
    }


def parse_questions(raw_text: str) -> Dict[int, Dict]:
    blocks = re.finditer(
        r"Question #(\d+) \(1 Point\)\s*(.*?)(?=Question #\d+ \(1 Point\)|Appendix: Additional Questions|\Z)",
        raw_text,
        flags=re.S,
    )

    questions: Dict[int, Dict] = {}
    for match in blocks:
        qnum = int(match.group(1))
        if not (1 <= qnum <= 40):
            continue

        parsed = parse_question_block(match.group(2))
        if not parsed["text"] or len(parsed["options"]) < 2:
            continue

        questions[qnum] = {
            "id": qnum,
            "text": parsed["text"],
            "options": parsed["options"],
        }

    return questions


def parse_answers(raw_text: str) -> Dict[int, Dict]:
    lines = clean_lines(raw_text)
    answers: Dict[int, Dict] = {}

    start_re = re.compile(r"^(\d+)\s+([a-z](?:,\s*[a-z])*)(?:\s+(.*))?$")
    lo_full_re = re.compile(r"^FL-\d+\.\d+\.\d+\s+K\d+\s+\d+\s*$")
    lo_only_re = re.compile(r"^FL-\d+\.\d+\.\d+\s*$")
    klevel_re = re.compile(r"^K\d+\s+\d+\s*$")

    i = 0
    while i < len(lines):
        line = lines[i]
        m = start_re.match(line)
        if not m:
            i += 1
            continue

        qnum = int(m.group(1))
        if not (1 <= qnum <= 40):
            i += 1
            continue

        correct_raw = m.group(2)
        explanation_parts = [m.group(3)] if m.group(3) else []

        i += 1
        while i < len(lines) and not start_re.match(lines[i]):
            current = lines[i]
            if lo_full_re.match(current) or lo_only_re.match(current) or klevel_re.match(current):
                i += 1
                continue
            if current:
                explanation_parts.append(current)
            i += 1

        answers[qnum] = {
            "correctOptions": [token.strip() for token in correct_raw.split(",")],
            "explanation": normalize_space(" ".join(explanation_parts)),
        }

    return answers


def build_exam_json(test_letter: str) -> Dict:
    q_pdf = QUESTIONS_DIR / f"ISTQB_CTFL_v4.0_Sample-Exam-{test_letter}-Questions_v1.{7 if test_letter in {'A', 'B'} else (6 if test_letter == 'C' else 5)}.pdf"
    a_pdf = ANSWERS_DIR / f"ISTQB_CTFL_v4.0_Sample-Exam-{test_letter}-Answers_v1.{7 if test_letter in {'A', 'B'} else (6 if test_letter == 'C' else 5)}.pdf"

    q_text = extract_text(q_pdf)
    a_text = extract_text(a_pdf)

    questions = parse_questions(q_text)
    answers = parse_answers(a_text)

    merged_questions = []
    for qnum in range(1, 41):
        if qnum not in questions:
            raise ValueError(f"Missing question #{qnum} in exam {test_letter}")
        if qnum not in answers:
            raise ValueError(f"Missing answer #{qnum} in exam {test_letter}")

        item = questions[qnum]
        item["correctOptions"] = answers[qnum]["correctOptions"]
        item["explanation"] = answers[qnum]["explanation"]
        merged_questions.append(item)

    return {
        "examId": test_letter,
        "title": f"ISTQB CTFL Sample Exam {test_letter}",
        "questionCount": len(merged_questions),
        "questions": merged_questions,
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for letter in ["A", "B", "C", "D"]:
        payload = build_exam_json(letter)
        out_path = OUTPUT_DIR / f"exam_{letter}.json"
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Created {out_path} with {payload['questionCount']} questions")


if __name__ == "__main__":
    main()
