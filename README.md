# NyayaMitra
Indian Legal AI assistant for Citizens and Lawyers

## Project Overview
NyayaMitra is designed to parse Indian legal statutes and prepare them for retrieval-augmented generation (RAG) via vector embeddings.

## Current Workflow
1. **Ingestion and parsing**
   - Statutes are parsed from source text into structured JSON.
   - Parsed statute files live under `data/processed/statutes/`.
   - Existing statute JSON files:
     - `bhartiya-nagrik-suraksha-sanhita-2023.json`
     - `bhartiya-nyaya-sanhita-2023.json`
     - `bhartiya-sakshya-adhiniyam.json`

2. **Chunking**
   - A new chunking pipeline was added under `chunking/`.
   - Core scripts:
     - `chunking/chunk_statutes.py` — chunking logic and metadata preservation
     - `chunking/run_chunking.py` — pipeline entry point
   - Output chunks are saved to `data/embeddings/chunks.json`.

## Chunking Methodology
- Each parsed statute section is treated as the primary unit.
- Sections with `<= 1000` estimated tokens are kept as a single chunk.
- Longer sections are split by sentence boundaries into smaller chunks.
- Each chunk retains metadata for:
  - `act`
  - `act_full_name`
  - `chapter_number`
  - `chapter_title`
  - `section_number`
  - `section_title`
- Chunk IDs follow the pattern: `ACT_S<section>_C<chunk>`.

## Results So Far
- Total parsed sections: **886**
- Total generated chunks: **1007**
- Embedding input file: `data/embeddings/chunks.json`

## Next Steps
- Generate vector embeddings from `data/embeddings/chunks.json`.
- Store embeddings in a vector store for retrieval.
- Build the question-answering / RAG layer on top of the embedded statute chunks.

## Notes
- The repository already contains ingestion/parsing scripts under `ingestion/`.
- Current chunking is focused on statute JSON data only.
- Future work can add support for judgments and additional legal documents.
