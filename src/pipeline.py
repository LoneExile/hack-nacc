"""Main NACC extraction pipeline."""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime, date
import logging
from dotenv import load_dotenv

from src.processors.pdf_processor import PDFProcessor
from src.extractors.claude_extractor import ClaudeExtractor
from src.utils.enum_loader import EnumLoader
from src.validators.dqs_calculator import DQSCalculator

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NACCExtractionPipeline:
    """Main pipeline for extracting NACC documents to CSV."""

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        model: Optional[str] = None
    ):
        """
        Initialize the extraction pipeline.

        Args:
            data_dir: Directory containing data files
            output_dir: Directory for output CSVs
            model: Claude model to use
        """
        self.data_dir = Path(data_dir or os.getenv("DATA_DIR", "./hack-the-assetdeclaration-data"))
        self.output_dir = Path(output_dir or os.getenv("OUTPUT_DIR", "./outputs"))
        self.output_dir.mkdir(exist_ok=True, parents=True)

        # Initialize components
        self.enum_loader = EnumLoader(self.data_dir / "enum_type")
        self.extractor = ClaudeExtractor(model=model)
        self.dqs_calculator = DQSCalculator()

        # Counters
        self.processed_docs = 0
        self.failed_docs = 0

        # Results storage
        self.all_results = {
            'submitter_info': [],
            'submitter_old_name': [],
            'submitter_position': [],
            'spouse_info': [],
            'spouse_old_name': [],
            'spouse_position': [],
            'relative_info': [],
            'statement': [],
            'statement_detail': [],
            'asset': [],
            'asset_land_info': [],
            'asset_building_info': [],
            'asset_vehicle_info': [],
            'asset_other_asset_info': [],
        }

        # ID counters
        self.next_asset_id = 1
        self.next_spouse_id = 1
        self.next_relative_id = 1
        self.next_statement_detail_id = 1

    def process_document(
        self,
        pdf_path: Path,
        nacc_id: int,
        submitter_id: int
    ) -> Dict[str, pd.DataFrame]:
        """
        Process a single NACC document PDF.

        Args:
            pdf_path: Path to PDF file
            nacc_id: NACC document ID
            submitter_id: Submitter ID

        Returns:
            Dictionary of DataFrames for each output table
        """
        logger.info(f"Processing: {pdf_path.name} (nacc_id={nacc_id}, submitter_id={submitter_id})")

        results = {key: [] for key in self.all_results.keys()}
        today = date.today()

        try:
            with PDFProcessor(pdf_path) as pdf:
                doc_info = pdf.get_document_info()
                logger.info(f"  Pages: {doc_info['num_pages']}, Searchable: {doc_info['is_searchable']}")

                # Get all pages as base64
                page_images = pdf.get_all_pages_base64(zoom=1.5, quality=85)
                logger.info(f"  Extracted {len(page_images)} page images")

                # Extract all data (with automatic batching for large docs)
                logger.info("  Extracting data with Claude...")
                extracted = self.extractor.extract_all_data_batched(page_images, nacc_id, submitter_id)

                # Process submitter info
                if extracted.get('submitter'):
                    submitter = extracted['submitter']
                    results['submitter_info'].append({
                        'submitter_id': submitter_id,
                        'title': submitter.get('title'),
                        'first_name': submitter.get('first_name'),
                        'last_name': submitter.get('last_name'),
                        'age': submitter.get('age'),
                        'status': submitter.get('status'),
                        'status_date': submitter.get('status_date'),
                        'status_month': submitter.get('status_month'),
                        'status_year': submitter.get('status_year'),
                        'sub_district': submitter.get('sub_district'),
                        'district': submitter.get('district'),
                        'province': submitter.get('province'),
                        'post_code': submitter.get('post_code'),
                        'latest_submitted_date': today,
                    })

                # Process submitter positions
                for pos in extracted.get('submitter_positions', []):
                    results['submitter_position'].append({
                        'submitter_id': submitter_id,
                        'nacc_id': nacc_id,
                        'position_period_type_id': pos.get('position_period_type_id', 1),
                        'index': pos.get('index', 0),
                        'position': pos.get('position'),
                        'position_category_type_id': pos.get('position_category_type_id'),
                        'workplace': pos.get('workplace'),
                        'workplace_location': pos.get('workplace_location'),
                        'date_acquiring_type_id': 1,
                        'start_date': pos.get('start_date'),
                        'start_month': pos.get('start_month'),
                        'start_year': pos.get('start_year'),
                        'date_ending_type_id': pos.get('date_ending_type_id'),
                        'end_date': pos.get('end_date'),
                        'end_month': pos.get('end_month'),
                        'end_year': pos.get('end_year'),
                        'note': pos.get('note'),
                        'latest_submitted_date': today,
                    })

                # Process spouse info
                spouse_data = extracted.get('spouse')
                if spouse_data and spouse_data.get('first_name'):
                    spouse_id = self.next_spouse_id
                    self.next_spouse_id += 1

                    results['spouse_info'].append({
                        'spouse_id': spouse_id,
                        'submitter_id': submitter_id,
                        'nacc_id': nacc_id,
                        'title': spouse_data.get('title'),
                        'first_name': spouse_data.get('first_name'),
                        'last_name': spouse_data.get('last_name'),
                        'age': spouse_data.get('age'),
                        'status': spouse_data.get('status'),
                        'status_date': spouse_data.get('status_date'),
                        'status_month': spouse_data.get('status_month'),
                        'status_year': spouse_data.get('status_year'),
                        'latest_submitted_date': today,
                    })

                    # Process spouse positions (GT format: spouse_id, submitter_id, nacc_id, position_period_type_id, index, position, workplace, workplace_location, note)
                    for idx, pos in enumerate(extracted.get('spouse_positions', []), start=1):
                        results['spouse_position'].append({
                            'spouse_id': spouse_id,
                            'submitter_id': submitter_id,
                            'nacc_id': nacc_id,
                            'position_period_type_id': pos.get('position_period_type_id', 2),  # 2=concurrent for spouse
                            'index': pos.get('index', idx),
                            'position': pos.get('position'),
                            'workplace': pos.get('workplace'),
                            'workplace_location': pos.get('workplace_location'),
                            'note': pos.get('note'),
                            'latest_submitted_date': today,
                        })

                # Process relatives
                for rel in extracted.get('relatives', []):
                    relative_id = self.next_relative_id
                    self.next_relative_id += 1

                    results['relative_info'].append({
                        'relative_id': relative_id,
                        'submitter_id': submitter_id,
                        'nacc_id': nacc_id,
                        'index': rel.get('index', 1),
                        'relationship_id': rel.get('relationship_id', 4),
                        'title': rel.get('title'),
                        'first_name': rel.get('first_name'),
                        'last_name': rel.get('last_name'),
                        'age': rel.get('age'),
                        'occupation': rel.get('occupation'),
                        'workplace': rel.get('workplace'),
                        'is_deceased': rel.get('is_deceased', False),
                        'latest_submitted_date': today,
                    })

                # Process statements (column order must match GT: nacc_id, statement_type_id, valuation_submitter, submitter_id, ...)
                for stmt in extracted.get('statements', []):
                    results['statement'].append({
                        'nacc_id': nacc_id,
                        'statement_type_id': stmt.get('statement_type_id'),
                        'valuation_submitter': stmt.get('valuation_submitter'),
                        'submitter_id': submitter_id,
                        'valuation_spouse': stmt.get('valuation_spouse'),
                        'valuation_child': stmt.get('valuation_child'),
                        'latest_submitted_date': today,
                    })

                # Process statement details
                for detail in extracted.get('statement_details', []):
                    results['statement_detail'].append({
                        'nacc_id': nacc_id,
                        'submitter_id': submitter_id,
                        'statement_detail_type_id': detail.get('statement_detail_type_id'),
                        'index': detail.get('index', 1),
                        'detail': detail.get('detail'),
                        'valuation_submitter': detail.get('valuation_submitter'),
                        'valuation_spouse': detail.get('valuation_spouse'),
                        'valuation_child': detail.get('valuation_child'),
                        'note': detail.get('note'),
                        'latest_submitted_date': today,
                    })

                # Process assets - track index per asset category
                asset_category_index = {}  # Maps category to next index

                def get_asset_category(type_id):
                    """Get asset category for index grouping."""
                    if type_id in range(1, 10) or type_id == 36:  # Land
                        return 'land'
                    elif type_id in range(10, 18) or type_id == 37:  # Building
                        return 'building'
                    elif type_id in range(18, 22) or type_id == 38:  # Vehicle
                        return 'vehicle'
                    elif type_id in range(22, 28) or type_id == 39:  # Rights
                        return 'rights'
                    else:  # Other (28-35)
                        return 'other'

                def strip_leading_zeros(val):
                    """Remove leading zeros from month/date values."""
                    if val is None:
                        return None
                    try:
                        return int(val)
                    except (ValueError, TypeError):
                        return val

                for asset in extracted.get('assets', []):
                    asset_id = self.next_asset_id
                    self.next_asset_id += 1

                    # Determine asset type ID
                    asset_type_id = asset.get('asset_type_id')
                    if not asset_type_id:
                        main_type = asset.get('asset_type_main', '')
                        sub_type = asset.get('asset_type_sub')
                        asset_type_id = self.enum_loader.match_asset_type_id(main_type, sub_type)

                    # Get category and compute index within category
                    category = get_asset_category(asset_type_id)
                    if category not in asset_category_index:
                        asset_category_index[category] = 1
                    asset_index = asset_category_index[category]
                    asset_category_index[category] += 1

                    # Determine date_ending_type_id: 1 if has end date, else 4
                    has_end_date = asset.get('ending_date') or asset.get('ending_month') or asset.get('ending_year')
                    date_ending_type_id = 1 if has_end_date else 4

                    # Use date_acquiring_type_id from asset or default based on whether date exists
                    has_acq_date = asset.get('acquiring_date') or asset.get('acquiring_month') or asset.get('acquiring_year')
                    date_acquiring_type_id = asset.get('date_acquiring_type_id', 1 if has_acq_date else 2)

                    results['asset'].append({
                        'asset_id': asset_id,
                        'submitter_id': submitter_id,
                        'nacc_id': nacc_id,
                        'index': asset_index,
                        'asset_type_id': asset_type_id,
                        'asset_type_other': asset.get('asset_type_other'),
                        'asset_name': asset.get('asset_name'),
                        'date_acquiring_type_id': date_acquiring_type_id,
                        'acquiring_date': strip_leading_zeros(asset.get('acquiring_date')),
                        'acquiring_month': strip_leading_zeros(asset.get('acquiring_month')),
                        'acquiring_year': asset.get('acquiring_year'),
                        'date_ending_type_id': date_ending_type_id,
                        'ending_date': strip_leading_zeros(asset.get('ending_date')),
                        'ending_month': strip_leading_zeros(asset.get('ending_month')),
                        'ending_year': asset.get('ending_year'),
                        'asset_acquisition_type_id': 6,
                        'valuation': asset.get('valuation'),
                        'owner_by_submitter': asset.get('owner_by_submitter', False),
                        'owner_by_spouse': asset.get('owner_by_spouse', False),
                        'owner_by_child': asset.get('owner_by_child', False),
                        'latest_submitted_date': today,
                    })

                    # Land info (GT has misspelled column names: sub_distirict, distirict)
                    land_info = asset.get('land_info')
                    if land_info and asset_type_id in range(1, 10):
                        results['asset_land_info'].append({
                            'asset_id': asset_id,
                            'submitter_id': submitter_id,
                            'nacc_id': nacc_id,
                            'land_doc_number': land_info.get('land_doc_number'),
                            'rai': land_info.get('rai') or 0,
                            'ngan': land_info.get('ngan') or 0,
                            'sq_wa': land_info.get('sq_wa'),
                            'sub_distirict': land_info.get('sub_district'),  # GT misspelling
                            'distirict': land_info.get('district'),  # GT misspelling
                            'province': land_info.get('province'),
                            'latest_submitted_date': today,
                        })

                    # Building info
                    building_info = asset.get('building_info')
                    if building_info and asset_type_id in range(10, 18):
                        results['asset_building_info'].append({
                            'asset_id': asset_id,
                            'submitter_id': submitter_id,
                            'nacc_id': nacc_id,
                            'building_doc_number': building_info.get('building_doc_number'),
                            'sub_district': building_info.get('sub_district'),
                            'district': building_info.get('district'),
                            'province': building_info.get('province'),
                            'latest_submitted_date': today,
                        })

                    # Vehicle info (GT schema: registration_number, vehicle_model, province)
                    vehicle_info = asset.get('vehicle_info')
                    if vehicle_info and asset_type_id in range(18, 22):
                        # Combine brand and model into single vehicle_model field
                        brand = vehicle_info.get('vehicle_brand') or ''
                        model = vehicle_info.get('vehicle_model') or ''
                        # Filter out None strings
                        if str(brand).strip().upper() == 'NONE':
                            brand = ''
                        if str(model).strip().upper() == 'NONE':
                            model = ''
                        combined_model = f"{brand} {model}".strip() if brand or model else model
                        # Strip spaces from registration number
                        reg_number = vehicle_info.get('registration_number', '')
                        if reg_number:
                            reg_number = reg_number.replace(' ', '')
                        results['asset_vehicle_info'].append({
                            'asset_id': asset_id,
                            'submitter_id': submitter_id,
                            'nacc_id': nacc_id,
                            'registration_number': reg_number,
                            'vehicle_model': combined_model,
                            'province': vehicle_info.get('registration_province'),
                            'latest_submitted_date': today,
                        })

                    # Other asset info
                    other_info = asset.get('other_info')
                    if other_info and asset_type_id in range(28, 36):
                        results['asset_other_asset_info'].append({
                            'asset_id': asset_id,
                            'submitter_id': submitter_id,
                            'nacc_id': nacc_id,
                            'count': other_info.get('count'),
                            'unit': other_info.get('unit'),
                            'latest_submitted_date': today,
                        })

            self.processed_docs += 1
            logger.info(f"  Successfully processed: {pdf_path.name}")

        except Exception as e:
            self.failed_docs += 1
            logger.error(f"  Error processing {pdf_path.name}: {e}")
            raise

        # Convert to DataFrames
        return {k: pd.DataFrame(v) for k, v in results.items()}

    def process_batch(
        self,
        pdf_dir: Path,
        doc_info_path: Path,
        limit: Optional[int] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Process a batch of PDFs based on doc_info.csv.

        Args:
            pdf_dir: Directory containing PDF files
            doc_info_path: Path to doc_info.csv
            limit: Maximum number of documents to process

        Returns:
            Combined results as DataFrames
        """
        pdf_dir = Path(pdf_dir)
        doc_info = pd.read_csv(doc_info_path)

        # Load nacc_detail.csv for nacc_id -> submitter_id mapping
        nacc_detail_path = doc_info_path.parent / "Train_nacc_detail.csv"
        nacc_id_to_submitter_id = {}
        if nacc_detail_path.exists():
            nacc_detail = pd.read_csv(nacc_detail_path)
            for _, row in nacc_detail.iterrows():
                nacc_id_val = int(row.get('nacc_id', 0))
                submitter_id_val = int(row.get('submitter_id', 0))
                if nacc_id_val and submitter_id_val:
                    nacc_id_to_submitter_id[nacc_id_val] = submitter_id_val
            logger.info(f"Loaded nacc_id -> submitter_id mapping: {len(nacc_id_to_submitter_id)} entries")

        if limit:
            doc_info = doc_info.head(limit)

        logger.info(f"Processing {len(doc_info)} documents from {pdf_dir}")

        for idx, row in doc_info.iterrows():
            # Find PDF file
            pdf_name = row.get('doc_location_url', '')
            if not pdf_name:
                continue

            pdf_path = pdf_dir / pdf_name

            if not pdf_path.exists():
                # Try alternative naming
                alt_name = f"{row.get('doc_id', '')}.pdf"
                pdf_path = pdf_dir / alt_name
                if not pdf_path.exists():
                    logger.warning(f"PDF not found: {pdf_name}")
                    continue

            nacc_id = int(row.get('nacc_id', row.get('ref_id', idx + 1)))
            # Get submitter_id from nacc_detail mapping, fallback to row or sequential
            submitter_id = nacc_id_to_submitter_id.get(
                nacc_id,
                int(row.get('submitter_id', idx + 1))
            )

            try:
                results = self.process_document(pdf_path, nacc_id, submitter_id)

                # Aggregate results
                for table_name, df in results.items():
                    if not df.empty:
                        self.all_results[table_name].append(df)

            except Exception as e:
                logger.error(f"Skipping {pdf_name}: {e}")
                continue

        # Combine all results
        combined = {}
        for table_name, df_list in self.all_results.items():
            if df_list:
                combined[table_name] = pd.concat(df_list, ignore_index=True)
            else:
                combined[table_name] = pd.DataFrame()

        return combined

    def save_results(self, results: Dict[str, pd.DataFrame], prefix: str = ""):
        """Save results to CSV files."""
        for table_name, df in results.items():
            if not df.empty:
                filename = f"{prefix}{table_name}.csv" if prefix else f"{table_name}.csv"
                output_path = self.output_dir / filename
                df.to_csv(output_path, index=False, encoding='utf-8-sig')
                logger.info(f"Saved {table_name}: {len(df)} records -> {output_path}")

    def validate_against_ground_truth(
        self,
        results: Dict[str, pd.DataFrame],
        ground_truth_dir: Path
    ) -> Dict[str, Any]:
        """
        Validate results against ground truth data.

        Args:
            results: Extracted results
            ground_truth_dir: Directory with ground truth CSVs

        Returns:
            DQS report
        """
        ground_truth = {}

        # Load ground truth files
        for table_name in self.all_results.keys():
            gt_path = ground_truth_dir / f"Train_{table_name}.csv"
            if gt_path.exists():
                ground_truth[table_name] = pd.read_csv(gt_path)
                logger.info(f"Loaded ground truth: {table_name} ({len(ground_truth[table_name])} rows)")

        # Calculate DQS
        dqs_report = self.dqs_calculator.calculate_overall_dqs(results, ground_truth)

        return dqs_report

    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return {
            'processed_documents': self.processed_docs,
            'failed_documents': self.failed_docs,
            'success_rate': self.processed_docs / (self.processed_docs + self.failed_docs)
                           if (self.processed_docs + self.failed_docs) > 0 else 0,
        }
