from pathlib import Path
import pdfplumber

RAW_DIR = Path("data/raw/statutes")
OUTPUT_DIR = Path("data/extracted/statutes")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)    

def extract_text_from_pdf(pdf_path: Path) -> str:
    print(f"Extracting text from {pdf_path.name}")

    text_parts = []

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)

        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()

            if text:
                text_parts.append(
                    f"\n\n===== PAGE {page_num} =====\n\n{text}"
                )

        full_text = "\n".join(text_parts)

    output_file = OUTPUT_DIR / f"{pdf_path.stem}.txt"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(full_text)
    
    print(
        f"✓ Extracted {pdf_path.name} "
        f"({total_pages} pages) -> {output_file}"
    )

def main():
    pdfs = list(RAW_DIR.glob("*.pdf"))

    if not pdfs:
        print(f"No PDF files found in {RAW_DIR}")
        return

    for pdf in pdfs:
        extract_text_from_pdf(pdf)

if __name__ == "__main__":
    main()
