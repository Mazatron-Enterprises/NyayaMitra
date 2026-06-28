import os
import json
import sys
import psycopg
from pathlib import Path
from typing import List, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "nyayamitra")
DB_USER = os.getenv("DB_USER", "nyayamitra")
DB_PASSWORD = os.getenv("DB_PASSWORD", "nyayamitra")


def connect() -> psycopg.Connection:
    return psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def search(query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
    from embeddings.generate_embeddings import embed_texts

    embedding = embed_texts([query_text])[0]
    embedding_literal = json.dumps(embedding)
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT chunk_id, act, act_full_name, section_number, section_title, text,
                       1 - (embedding <=> %s::vector) AS similarity
                FROM statute_chunks
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (embedding_literal, embedding_literal, limit),
            )
            rows = cur.fetchall()

    return [
        {
            "chunk_id": row[0],
            "act": row[1],
            "act_full_name": row[2],
            "section_number": row[3],
            "section_title": row[4],
            "text": row[5],
            "similarity": row[6],
        }
        for row in rows
    ]


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "defamation"
    results = search(query)
    for result in results:
        print(f"[{result['chunk_id']}] {result['section_number']} {result['section_title']}")
        print(f"Similarity: {result['similarity']:.4f}")
        print(result["text"][:500])
        print("-" * 80)
