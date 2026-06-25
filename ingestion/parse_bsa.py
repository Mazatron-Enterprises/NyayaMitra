import json
import re
from pathlib import Path

INPUT_FILE = Path(
    "data/extracted/statutes/bhartiya-sakshya-adhiniyam.txt"
)

OUTPUT_FILE = Path(
    "data/processed/statutes/bhartiya-sakshya-adhiniyam.json"
)

ACT_NAME = "Bharatiya Sakshya Adhiniyam, 2023"
ACT_SHORT = "BSA"
MAX_SECTION = 170


def clean_text(text: str) -> str:
    text = re.sub(
        r"===== PAGE \d+ =====",
        " ",
        text
    )

    text = re.sub(
        r"CHAPTER\s+[IVXLCDM]+\s+[A-Z][A-Z ,()\-]+",
        " ",
        text
    )

    text = re.sub(
        r"\n\s*\d+\s*\n",
        "\n",
        text
    )

    text = re.sub(
        r"\b\d{1,3}\b(?=\s+\(\d+\))",
        " ",
        text
    )

    text = re.sub(
        r"\b\d{1,3}\b(?=\s+Illustration)",
        " ",
        text
    )

    text = re.sub(
        r"\b\d{1,3}\b(?=\s+Explanation)",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def get_act_text(full_text: str) -> str:
    matches = list(
        re.finditer(
            r"CHAPTER I\s+PRELIMINARY",
            full_text
        )
    )

    if len(matches) < 2:
        raise Exception(
            "Could not locate actual act text"
        )

    text = full_text[matches[1].start():]

    cutoff_patterns = [
        r"STATEMENT OF OBJECTS AND REASONS",
        r"THE SCHEDULE",
        r"MEMORANDUM REGARDING DELEGATED LEGISLATION"
    ]

    for pattern in cutoff_patterns:
        m = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if m:
            text = text[:m.start()]
            break

    return text


def extract_chapters(text: str):
    chapter_pattern = re.compile(
        r"CHAPTER\s+([IVXLCDM]+)\s*\n([A-Z][A-Z ,()\-]+)"
    )

    chapters = []

    for m in chapter_pattern.finditer(text):
        chapters.append(
            {
                "position": m.start(),
                "chapter_number": m.group(1).strip(),
                "chapter_title": " ".join(
                    m.group(2).split()
                )
            }
        )

    return chapters


def chapter_for_position(position, chapters):
    current = None

    for chapter in chapters:
        if chapter["position"] <= position:
            current = chapter
        else:
            break

    return current


def extract_sections(text: str):
    pattern = re.compile(
        r"(?m)^(\d{1,3})(?:\.|\.?—|\.?–)"
    )

    matches = list(pattern.finditer(text))

    seen = set()
    filtered = []

    for m in matches:
        section_no = int(m.group(1))

        if section_no > MAX_SECTION:
            continue

        if section_no in seen:
            continue

        seen.add(section_no)
        filtered.append(m)

    print(f"Detected sections: {len(filtered)}")
    return filtered


def parse_section(raw_section: str):
    raw_section = raw_section.strip()

    number_match = re.match(
        r"^(\d+)(?:\.|\.?—|\.?–)",
        raw_section
    )

    if not number_match:
        return None

    section_number = int(number_match.group(1))
    remaining = raw_section[number_match.end():].strip()

    remaining = re.sub(
        r"^[—–\s]+",
        "",
        remaining
    )

    split_match = re.search(
        r"\.\s*[—–]",
        remaining
    )

    if split_match:
        section_title = remaining[:split_match.start()].strip()
        body = remaining[split_match.end():].strip()
    else:
        body_start = re.search(
            r"(?:\(\d+\)|Whoever\b|When\b|If\b|Every\b|A person\b|No person\b|Nothing\b)",
            remaining
        )

        if body_start:
            title = remaining[:body_start.start()]
            section_title = re.sub(
                r"[—–.\s]+$",
                "",
                title
            )
            body = remaining[body_start.start():]
        else:
            section_title = remaining
            body = ""

    section_title = re.sub(
        r"\s+",
        " ",
        section_title
    ).strip()

    body = clean_text(body)

    return {
        "section_number": section_number,
        "section_title": section_title,
        "text": body
    }


def main():
    with open(INPUT_FILE, encoding="utf-8") as f:
        full_text = f.read()

    text = get_act_text(full_text)
    chapters = extract_chapters(text)

    print(f"Detected chapters: {len(chapters)}")

    section_matches = extract_sections(text)

    from collections import defaultdict
    counts = defaultdict(int)
    for m in section_matches:
        counts[int(m.group(1))] += 1

    duplicates = [k for k, v in counts.items() if v > 1]
    print("Duplicates:", duplicates)

    numbers = [int(m.group(1)) for m in section_matches]
    print(f"First: {numbers[:10]}")
    print(f"Last: {numbers[-10:]}")

    missing = [n for n in range(1, MAX_SECTION + 1) if n not in numbers]
    print("Missing:", missing)

    sections = []

    for i, match in enumerate(section_matches):
        start = match.start()
        end = section_matches[i + 1].start() if i < len(section_matches) - 1 else len(text)
        raw_section = text[start:end]
        parsed = parse_section(raw_section)

        if not parsed:
            continue

        chapter = chapter_for_position(start, chapters)
        sections.append(
            {
                "document_id": f"bsa_{parsed['section_number']}",
                "document_type": "statute",
                "act": ACT_SHORT,
                "act_full_name": ACT_NAME,
                "chapter_number": chapter["chapter_number"] if chapter else None,
                "chapter_title": chapter["chapter_title"] if chapter else None,
                "section_number": parsed["section_number"],
                "section_title": parsed["section_title"],
                "text": parsed["text"]
            }
        )

    print(f"\nParsed sections: {len(sections)}")
    if len(sections) != MAX_SECTION:
        print(f"WARNING: Expected {MAX_SECTION} sections, got {len(sections)}")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        assert len(sections) == MAX_SECTION
        json.dump(sections, f, indent=2, ensure_ascii=False)

    print(f"\nSaved: {OUTPUT_FILE}")

    lookup = {s["section_number"]: s for s in sections}
    empty_sections = [s["section_number"] for s in sections if not s["text"].strip()]
    print("\nEmpty sections:", empty_sections)

    assert not empty_sections

    assert lookup[1]["section_title"] == "Short title, application and commencement"
    assert lookup[170]["section_title"] == "Repeal and savings"

    print("\nValidation succeeded.")


if __name__ == "__main__":
    main()
