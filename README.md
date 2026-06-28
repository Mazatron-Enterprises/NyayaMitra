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
   - A chunking pipeline was added under `chunking/`.
   - Core scripts:
     - `chunking/chunk_statutes.py` — chunking logic and metadata preservation
     - `chunking/run_chunking.py` — pipeline entry point
   - Output chunks are saved to `data/embeddings/chunks.json`.

3. **Embedding generation**
   - An embedding pipeline was added under `embeddings/`.
   - Core script:
     - `embeddings/generate_embeddings.py` — generates embeddings with the local BGE-M3 model via Ollama
   - Embedded output is saved to `data/embeddings/chunks_with_embeddings.json`.

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

## Embedding Methodology
- The local BGE-M3 model is used through Ollama for generating dense vector embeddings.
- Each chunk is embedded individually and stored with its metadata.
- Embedding vectors are 1024-dimensional.
- The output file preserves the original chunk text and metadata alongside the vector.

## Results So Far
- Total parsed sections: **886**
- Total generated chunks: **1007**
- Embedding input file: `data/embeddings/chunks.json`
- Embedded output file: `data/embeddings/chunks_with_embeddings.json`
- Verified embedding count: **1007** records, with **1005** non-empty embeddings

## Vector Database Setup
- PostgreSQL with pgvector is now configured via Docker Compose in [docker-compose.yml](docker-compose.yml).
- The database schema and import script live in [vector_db/init_db.py](vector_db/init_db.py).
- Example semantic search is available through [vector_db/query_db.py](vector_db/query_db.py).

### Run locally
1. Start the database container:
   - `docker compose up -d db`
2. Install Python dependencies:
   - `pip install -r requirements.txt`
3. Import the embedded chunks:
   - `python vector_db/init_db.py`
4. Run a sample semantic search:
   - `python vector_db/query_db.py "defamation"`

## Next Steps
- Add a web or CLI interface for legal question answering.
- Connect the retrieval layer into a RAG pipeline.
- Expand support for judgments and other legal documents.

## Notes
- The repository already contains ingestion/parsing scripts under `ingestion/`.
- Current chunking and embedding workflows are focused on statute JSON data only.
- Future work can add support for judgments and additional legal documents.
