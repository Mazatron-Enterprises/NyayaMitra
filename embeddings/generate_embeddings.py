import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Dict, Any


MODEL_NAME = "bge-m3:latest"
CHUNKS_PATH = Path("data/embeddings/chunks.json")
OUTPUT_PATH = Path("data/embeddings/chunks_with_embeddings.json")
OLLAMA_URL = "http://localhost:11434/api/embed"
BATCH_SIZE = 8


def load_chunks(path: Path) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def embed_texts(texts: List[str]) -> List[List[float]]:
    payload = json.dumps({"model": MODEL_NAME, "input": texts}).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=1800) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_text = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Ollama embedding request failed: {exc.code} {error_text}") from exc

    return data.get("embeddings", [])


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)

    if not CHUNKS_PATH.exists():
        raise FileNotFoundError(f"Chunks file not found: {CHUNKS_PATH}")

    chunks = load_chunks(CHUNKS_PATH)
    print(f"Loaded {len(chunks)} chunks from {CHUNKS_PATH}")

    enriched = []
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        texts = [chunk.get("text", "") for chunk in batch]

        try:
            embeddings = embed_texts(texts)
        except Exception as exc:
            print(f"Batch failed at chunk {i}: {exc}")
            print("Retrying with smaller batches...")
            for j, chunk in enumerate(batch):
                try:
                    single_embedding = embed_texts([chunk.get("text", "")])
                    if single_embedding:
                        enriched.append({**chunk, "embedding": single_embedding[0]})
                    else:
                        enriched.append({**chunk, "embedding": []})
                except Exception as inner_exc:
                    print(f"Single chunk failed for {chunk.get('chunk_id')}: {inner_exc}")
                    enriched.append({**chunk, "embedding": []})
            continue

        if len(embeddings) != len(batch):
            raise ValueError(f"Embedding count mismatch: expected {len(batch)}, got {len(embeddings)}")

        for chunk, embedding in zip(batch, embeddings):
            enriched.append({
                **chunk,
                "embedding": embedding,
            })

        print(f"Processed {min(i + BATCH_SIZE, len(chunks))}/{len(chunks)} chunks")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(enriched)} embedded chunks to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
