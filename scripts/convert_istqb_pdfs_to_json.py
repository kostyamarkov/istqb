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

EXAM_SPECS = {
    "A": {
        "question_pdf": "ISTQB_CTFL_v4.0_Sample-Exam-A-Questions_v1.7.pdf",
        "answer_pdf": "ISTQB_CTFL_v4.0_Sample-Exam-A-Answers_v1.7.pdf",
        "title": "ISTQB CTFL Sample Exam A",
        "question_count": 40,
    },
    "B": {
        "question_pdf": "ISTQB_CTFL_v4.0_Sample-Exam-B-Questions_v1.7.pdf",
        "answer_pdf": "ISTQB_CTFL_v4.0_Sample-Exam-B-Answers_v1.7.pdf",
        "title": "ISTQB CTFL Sample Exam B",
        "question_count": 40,
    },
    "C": {
        "question_pdf": "ISTQB_CTFL_v4.0_Sample-Exam-C-Questions_v1.6.pdf",
        "answer_pdf": "ISTQB_CTFL_v4.0_Sample-Exam-C-Answers_v1.6.pdf",
        "title": "ISTQB CTFL Sample Exam C",
        "question_count": 40,
    },
    "D": {
        "question_pdf": "ISTQB_CTFL_v4.0_Sample-Exam-D-Questions_v1.5.pdf",
        "answer_pdf": "ISTQB_CTFL_v4.0_Sample-Exam-D-Answers_v1.5.pdf",
        "title": "ISTQB CTFL Sample Exam D",
        "question_count": 40,
    },
    "ADV1": {
        "question_pdf": "ISTQB-CTAL-TA-Sample-Exam-Questions-v4.1.pdf",
        "answer_pdf": "ISTQB-CTAL-TA-Sample-Exam-Answers-v4.1.pdf",
        "title": "ISTQB CTAL-TA Sample Exam - Advanced 1",
        "question_count": 45,
    },
}

HEADER_PATTERNS = [
    re.compile(r"^Certified Tester, Foundation Level\s*$"),
    re.compile(r"^Certified Tester\s*$"),
    re.compile(r"^Advanced Level\s*$"),
    re.compile(r"^Test Analyst \(CTAL-TA\)\s*$"),
    re.compile(r"^Sample Exams? set [A-D]\s*$"),
    re.compile(r"^Sample Exam [–-] (Questions|Answers)\s*$"),
    re.compile(r"^Advanced Level Sample Exam [–-] (Questions|Answers) [–-] Test Analyst \(CTAL-TA\)\s*$"),
    re.compile(r"^ISTQB® Certified Tester\s*$"),
    re.compile(r"^ISTQB® Certified Tester\s+Advanced Level Sample Exam [–-] (Questions|Answers) [–-] Test Analyst \(CTAL-TA\)\s*$"),
    re.compile(r"^Version .* Page \d+ of \d+ Release .*"),
    re.compile(r"^Page \d+ of \d+ v4\.\d+.*$"),
    re.compile(r"^2025/07/08\s*$"),
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
    re.compile(r"Certified Tester", re.I),
    re.compile(r"Advanced Level", re.I),
    re.compile(r"Test Analyst \(CTAL-TA\)", re.I),
    re.compile(r"Sample Exams? set [A-D]", re.I),
    re.compile(r"Sample Exam [–-] (Questions|Answers)", re.I),
    re.compile(r"Advanced Level Sample Exam [–-] (Questions|Answers) [–-] Test Analyst \(CTAL-TA\)", re.I),
    re.compile(r"ISTQB® Certified Tester", re.I),
    re.compile(r"Version\s+\d+(?:\.\d+)*", re.I),
    re.compile(r"Page\s+\d+\s+of\s+\d+", re.I),
    re.compile(
        r"Release\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}",
        re.I,
    ),
    re.compile(r"TA-\d+\.\d+\.\d+\s+K\d+\s+\d+", re.I),
    re.compile(r"FL-\d+\.\d+\.\d+\s+K\d+\s+\d+", re.I),
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
    marker = re.search(r"\b(?:TA|FL)-\d+\.\d+\.\d+\s+K\d+\s+\d+\b", cleaned, flags=re.I)
    if marker:
        cleaned = cleaned[: marker.start()]
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
        r"Question #(\d+) \(\d+ Point(?:s)?\)\s*(.*?)(?=Question #\d+ \(\d+ Point(?:s)?\)|Appendix: Additional Questions|\Z)",
        raw_text,
        flags=re.S,
    )

    questions: Dict[int, Dict] = {}
    for match in blocks:
        qnum = int(match.group(1))
        if qnum < 1:
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
        if not (1 <= qnum <= 45):
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
            footer_marker = re.search(r"\b(?:TA|FL)-\d+\.\d+\.\d+\s+K\d+\s+\d+\b", current, flags=re.I)
            if footer_marker:
                prefix = current[: footer_marker.start()].strip()
                if prefix:
                    explanation_parts.append(prefix)
                i += 1
                break
            if current:
                explanation_parts.append(current)
            i += 1

        answers[qnum] = {
            "correctOptions": [token.strip() for token in correct_raw.split(",")],
            "explanation": normalize_space(" ".join(explanation_parts)),
        }

    return answers


def build_exam_json(test_letter: str) -> Dict:
    spec = EXAM_SPECS[test_letter]
    q_pdf = QUESTIONS_DIR / spec["question_pdf"]
    a_pdf = ANSWERS_DIR / spec["answer_pdf"]

    q_text = extract_text(q_pdf)
    a_text = extract_text(a_pdf)

    questions = parse_questions(q_text)
    answers = parse_answers(a_text)

    merged_questions = []
    for qnum in range(1, spec["question_count"] + 1):
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
        "title": spec["title"],
        "questionCount": len(merged_questions),
        "questions": merged_questions,
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for letter in ["A", "B", "C", "D", "ADV1"]:
        payload = build_exam_json(letter)
        out_path = OUTPUT_DIR / ("exam_advanced_1.json" if letter == "ADV1" else f"exam_{letter}.json")
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Created {out_path} with {payload['questionCount']} questions")


if __name__ == "__main__":
    main()
