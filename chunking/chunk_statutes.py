"""
Chunking module for legal statute documents.
Simple, fast implementation focusing on section-level chunking.
"""

import json
import os
from typing import List, Dict, Any


def estimate_tokens(text: str) -> int:
    """Rough token estimation: ~4 characters = 1 token."""
    return max(1, len(text) // 4)


def chunk_sections(
    sections: List[Dict[str, Any]],
    chunk_size: int = 1000,
) -> List[Dict[str, Any]]:
    """
    Chunk statute sections. Most fit in one chunk; split only if necessary.
    
    Args:
        sections: List of statute section dictionaries
        chunk_size: Target tokens per chunk
    
    Returns:
        List of chunked records
    """
    chunks = []
    
    for section in sections:
        text = section.get("text", "").strip()
        if not text:
            continue
        
        tokens = estimate_tokens(text)
        
        # If section fits, create single chunk
        if tokens <= chunk_size:
            chunk = {
                "chunk_id": f"{section['act']}_S{section['section_number']}_C1",
                "act": section["act"],
                "act_full_name": section.get("act_full_name", ""),
                "chapter_number": section.get("chapter_number", ""),
                "chapter_title": section.get("chapter_title", ""),
                "section_number": section["section_number"],
                "section_title": section.get("section_title", ""),
                "text": text,
                "token_count": tokens,
            }
            chunks.append(chunk)
        else:
            # Split large sections by sentences
            sentences = text.replace(". ", ".|").split("|")
            
            current_chunk = ""
            current_tokens = 0
            chunk_num = 1
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                
                sentence_tokens = estimate_tokens(sentence)
                
                # If adding this sentence exceeds limit, save chunk and start new
                if current_tokens + sentence_tokens > chunk_size and current_chunk:
                    chunk = {
                        "chunk_id": f"{section['act']}_S{section['section_number']}_C{chunk_num}",
                        "act": section["act"],
                        "act_full_name": section.get("act_full_name", ""),
                        "chapter_number": section.get("chapter_number", ""),
                        "chapter_title": section.get("chapter_title", ""),
                        "section_number": section["section_number"],
                        "section_title": section.get("section_title", ""),
                        "text": current_chunk.strip(),
                        "token_count": current_tokens,
                    }
                    chunks.append(chunk)
                    current_chunk = ""
                    current_tokens = 0
                    chunk_num += 1
                
                current_chunk += sentence + ". "
                current_tokens += sentence_tokens
            
            # Save remaining chunk
            if current_chunk.strip():
                chunk = {
                    "chunk_id": f"{section['act']}_S{section['section_number']}_C{chunk_num}",
                    "act": section["act"],
                    "act_full_name": section.get("act_full_name", ""),
                    "chapter_number": section.get("chapter_number", ""),
                    "chapter_title": section.get("chapter_title", ""),
                    "section_number": section["section_number"],
                    "section_title": section.get("section_title", ""),
                    "text": current_chunk.strip(),
                    "token_count": current_tokens,
                }
                chunks.append(chunk)
    
    return chunks


def process_all_files(
    input_files: List[str],
    chunk_size: int = 1000,
) -> List[Dict[str, Any]]:
    """Process all statute files and generate chunks."""
    all_chunks = []
    
    for filepath in input_files:
        if not os.path.exists(filepath):
            print(f"⚠️  File not found: {filepath}")
            continue
        
        with open(filepath, "r", encoding="utf-8") as f:
            sections = json.load(f)
        
        chunks = chunk_sections(sections, chunk_size=chunk_size)
        all_chunks.extend(chunks)
        
        filename = os.path.basename(filepath)
        print(f"✅ {filename}: {len(sections)} sections → {len(chunks)} chunks")
    
    return all_chunks


def save_chunks(chunks: List[Dict[str, Any]], output_path: str) -> None:
    """Save chunks to JSON file."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Saved {len(chunks)} chunks to {output_path}")


def print_statistics(chunks: List[Dict[str, Any]]) -> None:
    """Print chunking statistics."""
    if not chunks:
        print("No chunks generated.")
        return
    
    total_tokens = sum(c.get("token_count", 0) for c in chunks)
    avg_tokens = total_tokens // len(chunks)
    token_counts = [c.get("token_count", 0) for c in chunks]
    
    acts = {}
    for chunk in chunks:
        act = chunk.get("act", "")
        acts[act] = acts.get(act, 0) + 1
    
    print("\n" + "=" * 70)
    print("CHUNKING STATISTICS")
    print("=" * 70)
    print(f"Total chunks:        {len(chunks)}")
    print(f"Total tokens:        {total_tokens:,}")
    print(f"Avg tokens/chunk:    {avg_tokens:,}")
    print(f"Min tokens:          {min(token_counts)}")
    print(f"Max tokens:          {max(token_counts)}")
    print(f"Median tokens:       {sorted(token_counts)[len(token_counts)//2]}")
    print(f"\nChunks by Act:")
    for act, count in sorted(acts.items()):
        print(f"  {act}: {count}")
    print("=" * 70)


if __name__ == "__main__":
    input_files = [
        "data/processed/statutes/bhartiya-nagrik-suraksha-sanhita-2023.json",
        "data/processed/statutes/bhartiya-nyaya-sanhita-2023.json",
        "data/processed/statutes/bhartiya-sakshya-adhiniyam.json",
    ]
    
    print("=" * 70)
    print("NYAYAMITRA CHUNKING PIPELINE")
    print("=" * 70 + "\n")
    
    all_chunks = process_all_files(input_files, chunk_size=1000)
    
    if all_chunks:
        output_path = "data/embeddings/chunks.json"
        save_chunks(all_chunks, output_path)
        print_statistics(all_chunks)
        print("\n✅ Chunking completed successfully!")
    else:
        print("\n❌ No chunks generated. Check input files.")
