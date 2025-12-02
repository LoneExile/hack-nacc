#!/usr/bin/env python3
"""
Test extraction on a single document.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.processors.pdf_processor import PDFProcessor
from src.extractors.claude_extractor import ClaudeExtractor
import json


def main():
    data_dir = Path("./hack-the-assetdeclaration-data")
    pdf_dir = data_dir / "pdf training"

    # Get first PDF
    pdf_files = sorted(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        print("No PDF files found!")
        return

    pdf_path = pdf_files[0]
    print(f"Testing with: {pdf_path.name}")
    print("=" * 60)

    # Process PDF
    with PDFProcessor(pdf_path) as pdf:
        print(f"Pages: {pdf.num_pages}")
        print(f"Searchable: {pdf.is_searchable()}")

        # Get page images
        print("\nExtracting page images...")
        page_images = pdf.get_all_pages_base64(zoom=1.5, quality=85)
        print(f"Got {len(page_images)} images")

    # Extract with Claude
    print("\nCalling Claude API...")
    extractor = ClaudeExtractor()

    try:
        result = extractor.extract_all_data(page_images, nacc_id=1, submitter_id=1)

        print("\n" + "=" * 60)
        print("EXTRACTION RESULT")
        print("=" * 60)
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))

    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
