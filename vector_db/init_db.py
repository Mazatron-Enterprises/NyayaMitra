import json
import os
import psycopg
from pathlib import Path
from typing import List, Dict, Any

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "nyayamitra")
DB_USER = os.getenv("DB_USER", "nyayamitra")
DB_PASSWORD = os.getenv("DB_PASSWORD", "nyayamitra")
EMBEDDINGS_PATH = Path("data/embeddings/chunks_with_embeddings.json")


def load_chunks(path: Path) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_tables(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS statute_chunks (
            id SERIAL PRIMARY KEY,
            chunk_id TEXT UNIQUE NOT NULL,
            act TEXT,
            act_full_name TEXT,
            chapter_number TEXT,
            chapter_title TEXT,
            section_number TEXT,
            section_title TEXT,
            text TEXT,
            embedding vector(1024)
        )
        """)
        conn.commit()


def insert_chunks(conn, chunks: List[Dict[str, Any]]) -> None:
    with conn.cursor() as cur:
        for chunk in chunks:
            embedding = chunk.get("embedding") or []
            if len(embedding) != 1024:
                continue
            embedding_literal = json.dumps(embedding)
            cur.execute(
                """
                INSERT INTO statute_chunks (
                    chunk_id, act, act_full_name, chapter_number, chapter_title,
                    section_number, section_title, text, embedding
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::vector)
                ON CONFLICT (chunk_id) DO NOTHING
                """,
                (
                    chunk.get("chunk_id"),
                    chunk.get("act"),
                    chunk.get("act_full_name"),
                    chunk.get("chapter_number"),
                    chunk.get("chapter_title"),
                    chunk.get("section_number"),
                    chunk.get("section_title"),
                    chunk.get("text"),
                    embedding_literal,
                ),
            )
        conn.commit()


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)

    if not EMBEDDINGS_PATH.exists():
        raise FileNotFoundError(f"Embeddings file not found: {EMBEDDINGS_PATH}")

    chunks = load_chunks(EMBEDDINGS_PATH)
    print(f"Loaded {len(chunks)} chunks from {EMBEDDINGS_PATH}")

    conn = psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )
    try:
        create_tables(conn)
        insert_chunks(conn, chunks)
        print("Imported statute chunks into PostgreSQL")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
