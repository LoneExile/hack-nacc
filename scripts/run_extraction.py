#!/usr/bin/env python3
"""
Main script to run NACC document extraction pipeline.

Usage:
    python scripts/run_extraction.py --mode train --limit 5
    python scripts/run_extraction.py --mode test
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import NACCExtractionPipeline


def main():
    parser = argparse.ArgumentParser(description="NACC Document Extraction Pipeline")
    parser.add_argument(
        "--mode",
        choices=["train", "test", "single"],
        default="train",
        help="Processing mode"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of documents to process"
    )
    parser.add_argument(
        "--pdf",
        type=str,
        default=None,
        help="Single PDF path (for --mode single)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Claude model to use (claude-sonnet-4-5-20250929, claude-opus-4-5-20251101, claude-haiku-4-5-20251001)"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="./hack-the-assetdeclaration-data",
        help="Data directory path"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./outputs",
        help="Output directory path"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate against ground truth (train mode only)"
    )

    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)

    # Initialize pipeline
    pipeline = NACCExtractionPipeline(
        data_dir=data_dir,
        output_dir=output_dir,
        model=args.model
    )

    print("=" * 60)
    print("NACC Document Extraction Pipeline")
    print("=" * 60)
    print(f"Mode: {args.mode}")
    print(f"Data directory: {data_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Limit: {args.limit or 'None (all documents)'}")
    print("=" * 60)

    if args.mode == "train":
        # Process training data
        pdf_dir = data_dir / "pdf training"
        doc_info_path = data_dir / "training" / "DB file" / "input" / "Train_doc_info.csv"

        if not pdf_dir.exists():
            print(f"ERROR: PDF directory not found: {pdf_dir}")
            sys.exit(1)
        if not doc_info_path.exists():
            print(f"ERROR: Doc info file not found: {doc_info_path}")
            sys.exit(1)

        print(f"\nProcessing training data from: {pdf_dir}")
        results = pipeline.process_batch(pdf_dir, doc_info_path, limit=args.limit)

        # Save results
        pipeline.save_results(results, prefix="Train_")

        # Validate if requested
        if args.validate:
            ground_truth_dir = data_dir / "training" / "DB file" / "output"
            print("\n" + "=" * 60)
            print("VALIDATION RESULTS")
            print("=" * 60)

            dqs_report = pipeline.validate_against_ground_truth(results, ground_truth_dir)

            print(f"\nOverall DQS: {dqs_report['overall_dqs']:.2%}")
            print(f"Passes 70% threshold: {'YES' if dqs_report['passes_threshold'] else 'NO'}")

            print("\nSection Scores:")
            for section, score in dqs_report['section_scores'].items():
                print(f"  {section}: {score:.2%}")

            print("\nTable Scores:")
            for table, score in dqs_report['table_scores'].items():
                if score > 0:
                    print(f"  {table}: {score:.2%}")

    elif args.mode == "test":
        # Process test data
        pdf_dir = data_dir / "pdf test phase 1"
        doc_info_path = data_dir / "test input phase 1" / "doc_info.csv"

        # Try alternative paths if not found
        if not doc_info_path.exists():
            # Create a simple doc_info from available PDFs
            print(f"Doc info not found at {doc_info_path}, scanning PDF directory...")
            pdf_files = list(pdf_dir.glob("*.pdf"))

            if pdf_files:
                import pandas as pd
                doc_info = pd.DataFrame({
                    'doc_id': range(1, len(pdf_files) + 1),
                    'doc_location_url': [f.name for f in pdf_files],
                    'nacc_id': range(1, len(pdf_files) + 1),
                    'submitter_id': range(1, len(pdf_files) + 1),
                })
                doc_info_path = output_dir / "test_doc_info.csv"
                doc_info.to_csv(doc_info_path, index=False)
                print(f"Created doc_info with {len(pdf_files)} PDFs")

        print(f"\nProcessing test data from: {pdf_dir}")
        results = pipeline.process_batch(pdf_dir, doc_info_path, limit=args.limit)

        # Save results
        pipeline.save_results(results, prefix="Test_")

    elif args.mode == "single":
        if not args.pdf:
            print("ERROR: --pdf argument required for single mode")
            sys.exit(1)

        pdf_path = Path(args.pdf)
        if not pdf_path.exists():
            print(f"ERROR: PDF not found: {pdf_path}")
            sys.exit(1)

        print(f"\nProcessing single document: {pdf_path}")
        results = pipeline.process_document(pdf_path, nacc_id=1, submitter_id=1)

        # Save results
        pipeline.save_results(results, prefix="Single_")

    # Print statistics
    stats = pipeline.get_stats()
    print("\n" + "=" * 60)
    print("PROCESSING COMPLETE")
    print("=" * 60)
    print(f"Processed: {stats['processed_documents']} documents")
    print(f"Failed: {stats['failed_documents']} documents")
    print(f"Success rate: {stats['success_rate']:.1%}")
    print(f"Output saved to: {output_dir}")


if __name__ == "__main__":
    main()
