"""
Main entry point for chunking pipeline.
Processes all parsed statute files and generates chunks with metadata.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from chunking.chunk_statutes import process_all_files, save_chunks, print_statistics


def main():
    """Run the complete chunking pipeline."""
    
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    input_files = [
        "data/processed/statutes/bhartiya-nagrik-suraksha-sanhita-2023.json",
        "data/processed/statutes/bhartiya-nyaya-sanhita-2023.json",
        "data/processed/statutes/bhartiya-sakshya-adhiniyam.json",
    ]
    
    print("=" * 70)
    print("NYAYAMITRA CHUNKING PIPELINE")
    print("=" * 70)
    print()
    
    # Process all files
    all_chunks = process_all_files(input_files, chunk_size=1000)
    
    if not all_chunks:
        print("\n❌ No chunks generated. Check input files.")
        return False
    
    # Save consolidated chunks
    output_path = "data/embeddings/chunks.json"
    save_chunks(all_chunks, output_path)
    
    # Print statistics
    print_statistics(all_chunks)
    
    print("✅ Chunking pipeline completed successfully!")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
