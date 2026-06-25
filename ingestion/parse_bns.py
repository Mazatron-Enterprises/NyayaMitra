import json
import re
from pathlib import Path

INPUT_FILE = Path(
    "data/extracted/statutes/bhartiya-nyaya-sanhita-2023.txt"
)

OUTPUT_FILE = Path(
    "data/processed/statutes/bhartiya-nyaya-sanhita-2023.json"
)

ACT_NAME = "Bharatiya Nyaya Sanhita, 2023"
ACT_SHORT = "BNS"
MAX_SECTION = 358


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

    # standalone page numbers
    text = re.sub(
        r"\n\s*\d+\s*\n",
        "\n",
        text
    )

    # page numbers embedded in text
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
            "Could not locate actual BNS text"
        )

    text = full_text[matches[1].start():]

    # remove everything after Act ends
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


def extract_sections(text):

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

        # ignore duplicate section numbers
        if section_no in seen:
            continue

        seen.add(section_no)
        filtered.append(m)

    print(
        f"Detected sections: {len(filtered)}"
    )

    return filtered

def parse_section(raw_section):

    raw_section = raw_section.strip()

    number_match = re.match(
        r"^(\d+)(?:\.|\.?—|\.?–)",
        raw_section
    )

    if not number_match:
        return None

    section_number = int(
        number_match.group(1)
    )

    remaining = raw_section[
        number_match.end():
    ].strip()

    remaining = re.sub(
        r"^[—–\s]+",
        "",
        remaining
    )

    if section_number == 217:
        split = re.search(
            r"person[—–]Whoever",
            remaining
        )

        if split:
            return {
                "section_number": section_number,
                "section_title":
                    remaining[:split.start() + len("person")],
                "text":
                    clean_text(
                        remaining[
                            split.start() + len("person—"):
                        ]
                    )
            }

    # --------------------------------------------------
    # Most BNS sections:
    #
    # Title.—Body
    #
    # Split on FIRST occurrence only.
    # --------------------------------------------------

    split_match = re.search(
        r"\.\s*[—–]",
        remaining
    )

    if split_match:

        section_title = remaining[
            :split_match.start()
        ].strip()

        body = remaining[
            split_match.end():
        ].strip()

    else:

        # --------------------------------------------------
        # Fallback:
        # title before first subsection
        # --------------------------------------------------

        body_start = re.search(
            r"(?:\(\d+\)|Whoever\b|When\b|If\b|Every\b|A person\b|No person\b|Nothing\b)",
            remaining
        )   

        if body_start:

            title = remaining[:body_start.start()]

            title = re.sub(
                r"[—–.\s]+$",
                "",
                title
            )

            body = remaining[body_start.start():]

        else:
            title = remaining
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

    with open(
        INPUT_FILE,
        encoding="utf-8"
    ) as f:

        full_text = f.read()

    text = get_act_text(
        full_text
    )

    
    chapters = extract_chapters(
        text
    )

    print(
        f"Detected chapters: {len(chapters)}"
    )

    section_matches = extract_sections(
        text
    )

    from collections import defaultdict

    counts = defaultdict(int)

    for m in section_matches:
        counts[int(m.group(1))] += 1

    duplicates = [
        k for k, v in counts.items()
        if v > 1
    ]

    print("Duplicates:", duplicates)


    numbers = [
        int(m.group(1))
        for m in section_matches
    ]

    print(f"First: {numbers[:10]}")
    print(f"Last: {numbers[-10:]}")

    missing = [
        n
        for n in range(1, 359)
        if n not in numbers
    ]

    print("Missing:", missing)

    sections = []

    for i, match in enumerate(section_matches):

        start = match.start()

        if i < len(section_matches) - 1:
            end = section_matches[i + 1].start()
        else:
            end = len(text)

        raw_section = text[start:end]

        parsed = parse_section(
            raw_section
        )

        if not parsed:
            continue

        chapter = chapter_for_position(
            start,
            chapters
        )

        sections.append(
            {
                "document_id":
                    f"bns_{parsed['section_number']}",

                "document_type":
                    "statute",

                "act":
                    ACT_SHORT,

                "act_full_name":
                    ACT_NAME,

                "chapter_number":
                    chapter["chapter_number"]
                    if chapter else None,

                "chapter_title":
                    chapter["chapter_title"]
                    if chapter else None,

                "section_number":
                    parsed["section_number"],

                "section_title":
                    parsed["section_title"],

                "text":
                    parsed["text"]
            }
        )

    print(
        f"\nParsed sections: {len(sections)}"
    )

    if len(sections) != 358:

        print(
            f"WARNING: Expected 358 sections, got {len(sections)}"
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        assert len(sections) == 358

        for s in sections:

            if not s["text"]:
                print("\nEMPTY SECTION")
                print(s["section_number"])
                print(s["section_title"])
                print(
                    f"WARNING Empty text in section {s['section_number']}"
                )    

        json.dump(
            sections,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(
        f"\nSaved: {OUTPUT_FILE}"
    )

    print("\nValidation\n")

    validation_sections = [
        1,
        6,
        255,
        165,
        209,
        318,
        358
    ]

    lookup = {
        s["section_number"]: s
        for s in sections
    }

    empty_sections = [
        s["section_number"]
        for s in sections
        if not s["text"].strip()
    ]

    print(
        "\nEmpty sections:",
        empty_sections
    )

    assert not empty_sections

    for n in [209, 217, 255, 318, 358]:
        print()
        print(n)
        print("TITLE:", lookup[n]["section_title"])
        print("TEXT:", lookup[n]["text"][:150])
        
    print(
        json.dumps(
            lookup[217],
            indent=2,
            ensure_ascii=False
        )
    )

    for n in [1, 255, 318, 358]:
        print(n, repr(lookup[n]["section_title"]))

    assert len(sections) == 358

    assert lookup[1]["section_title"] == \
        "Short title, commencement and application"

    assert lookup[6]["section_title"] == \
        "Fractions of terms of punishment"

    assert lookup[255]["section_title"].startswith(
        "Public servant disobeying"
    )

    assert lookup[318]["section_title"] == \
        "Cheating"

    assert lookup[358]["section_title"] == \
        "Repeal and savings"
    

    for section_no in validation_sections:

        if section_no in lookup:

            print("\n" + "=" * 80)

            print(
                f"Section {section_no}"
            )

            print(
                "Title:",
                lookup[section_no][
                    "section_title"
                ]
            )

            print(
                "Text Preview:",
                lookup[section_no][
                    "text"
                ][:300]
            )


if __name__ == "__main__":
    main()