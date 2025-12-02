"""DQS (Digitization Quality Score) Calculator."""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime

try:
    import Levenshtein
    HAS_LEVENSHTEIN = True
except ImportError:
    HAS_LEVENSHTEIN = False


class DQSCalculator:
    """Calculate Digitization Quality Score based on competition rules."""

    # Section weights from competition rules
    SECTION_WEIGHTS = {
        'submitter_spouse': 0.25,
        'statement_details': 0.30,
        'assets': 0.30,
        'relatives': 0.15
    }

    # Tables belonging to each section
    TABLE_TO_SECTION = {
        'submitter_info': 'submitter_spouse',
        'submitter_old_name': 'submitter_spouse',
        'submitter_position': 'submitter_spouse',
        'spouse_info': 'submitter_spouse',
        'spouse_old_name': 'submitter_spouse',
        'spouse_position': 'submitter_spouse',
        'statement': 'statement_details',
        'statement_detail': 'statement_details',
        'asset': 'assets',
        'asset_land_info': 'assets',
        'asset_building_info': 'assets',
        'asset_vehicle_info': 'assets',
        'asset_other_asset_info': 'assets',
        'relative_info': 'relatives'
    }

    def __init__(self):
        pass

    def calculate_text_score(self, predicted: str, ground_truth: str) -> float:
        """
        Calculate text field score: 1 - CER.
        CER = Character Error Rate (Levenshtein distance / length)
        """
        if pd.isna(predicted) and pd.isna(ground_truth):
            return 1.0
        if pd.isna(predicted) or pd.isna(ground_truth):
            return 0.0

        pred_str = str(predicted).strip()
        truth_str = str(ground_truth).strip()

        # Handle "NONE" values
        if pred_str.upper() == "NONE":
            pred_str = ""
        if truth_str.upper() == "NONE":
            truth_str = ""

        if not truth_str and not pred_str:
            return 1.0
        if not truth_str:
            return 0.0 if pred_str else 1.0

        if HAS_LEVENSHTEIN:
            distance = Levenshtein.distance(pred_str, truth_str)
        else:
            # Simple fallback without Levenshtein
            distance = 0 if pred_str == truth_str else len(truth_str)

        cer = distance / max(len(truth_str), 1)
        score = max(0, 1 - cer)
        return score

    def calculate_numeric_score(self, predicted: float, ground_truth: float) -> float:
        """Calculate numeric field score: 1 - relative_error."""
        if pd.isna(predicted) and pd.isna(ground_truth):
            return 1.0
        if pd.isna(predicted) or pd.isna(ground_truth):
            return 0.0

        try:
            pred_val = float(predicted)
            truth_val = float(ground_truth)
        except (ValueError, TypeError):
            return 0.0

        if truth_val == 0:
            return 1.0 if pred_val == 0 else 0.0

        relative_error = abs(pred_val - truth_val) / abs(truth_val)
        score = max(0, 1 - relative_error)
        return score

    def calculate_date_score(
        self,
        pred_date: Optional[str],
        pred_month: Optional[str],
        pred_year: Optional[str],
        truth_date: Optional[str],
        truth_month: Optional[str],
        truth_year: Optional[str]
    ) -> float:
        """
        Calculate date field score.
        - exact match = 1.0
        - ±3 days = 0.8
        - same month/year = 0.5
        - same year = 0.3
        - else = 0.0
        """
        # Handle all null case
        all_pred_null = all(pd.isna(x) or str(x).upper() == "NONE" for x in [pred_date, pred_month, pred_year])
        all_truth_null = all(pd.isna(x) or str(x).upper() == "NONE" for x in [truth_date, truth_month, truth_year])

        if all_pred_null and all_truth_null:
            return 1.0
        if all_pred_null or all_truth_null:
            return 0.0

        # Compare year
        try:
            p_year = int(pred_year) if pred_year and str(pred_year).upper() != "NONE" else None
            t_year = int(truth_year) if truth_year and str(truth_year).upper() != "NONE" else None
        except (ValueError, TypeError):
            p_year = t_year = None

        if p_year != t_year:
            return 0.0 if p_year is None or t_year is None else 0.0

        # Compare month
        try:
            p_month = int(pred_month) if pred_month and str(pred_month).upper() != "NONE" else None
            t_month = int(truth_month) if truth_month and str(truth_month).upper() != "NONE" else None
        except (ValueError, TypeError):
            p_month = t_month = None

        if p_month != t_month:
            return 0.3  # Same year, different month

        # Compare date
        try:
            p_date = int(pred_date) if pred_date and str(pred_date).upper() != "NONE" else None
            t_date = int(truth_date) if truth_date and str(truth_date).upper() != "NONE" else None
        except (ValueError, TypeError):
            p_date = t_date = None

        if p_date == t_date:
            return 1.0
        if p_date is None or t_date is None:
            return 0.5  # Same month/year

        date_diff = abs(p_date - t_date)
        if date_diff <= 3:
            return 0.8

        return 0.5  # Same month/year but different date

    def calculate_enum_score(self, predicted: Any, ground_truth: Any) -> float:
        """Calculate enum field score: exact match."""
        if pd.isna(predicted) and pd.isna(ground_truth):
            return 1.0
        if pd.isna(predicted) or pd.isna(ground_truth):
            return 0.0

        pred_str = str(predicted).strip().lower()
        truth_str = str(ground_truth).strip().lower()

        # Handle "NONE" values
        if pred_str == "none" and truth_str == "none":
            return 1.0

        return 1.0 if pred_str == truth_str else 0.0

    def calculate_boolean_score(self, predicted: Any, ground_truth: Any) -> float:
        """Calculate boolean field score."""
        def to_bool(val):
            if pd.isna(val):
                return None
            if isinstance(val, bool):
                return val
            val_str = str(val).strip().lower()
            if val_str in ('true', '1', 'yes'):
                return True
            if val_str in ('false', '0', 'no'):
                return False
            return None

        p = to_bool(predicted)
        t = to_bool(ground_truth)

        if p is None and t is None:
            return 1.0
        if p is None or t is None:
            return 0.5
        return 1.0 if p == t else 0.0

    def calculate_row_dqs(
        self,
        predicted_row: pd.Series,
        truth_row: pd.Series,
        field_types: Dict[str, str]
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate DQS for a single row.

        Args:
            predicted_row: Predicted data row
            truth_row: Ground truth row
            field_types: Field name to type mapping ('text', 'numeric', 'date', 'enum', 'boolean')

        Returns:
            (overall_score, field_scores)
        """
        field_scores = {}

        for field, field_type in field_types.items():
            if field not in predicted_row.index or field not in truth_row.index:
                continue

            pred_val = predicted_row.get(field)
            truth_val = truth_row.get(field)

            if field_type == 'text':
                score = self.calculate_text_score(pred_val, truth_val)
            elif field_type == 'numeric':
                score = self.calculate_numeric_score(pred_val, truth_val)
            elif field_type == 'enum':
                score = self.calculate_enum_score(pred_val, truth_val)
            elif field_type == 'boolean':
                score = self.calculate_boolean_score(pred_val, truth_val)
            else:
                score = self.calculate_text_score(pred_val, truth_val)

            field_scores[field] = score

        overall = np.mean(list(field_scores.values())) if field_scores else 0.0
        return overall, field_scores

    def calculate_table_dqs(
        self,
        predicted_df: pd.DataFrame,
        ground_truth_df: pd.DataFrame,
        key_columns: List[str],
        field_types: Dict[str, str]
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate DQS for a single table.

        Args:
            predicted_df: Predicted DataFrame
            ground_truth_df: Ground truth DataFrame
            key_columns: Columns to match rows
            field_types: Field type mapping

        Returns:
            (overall_score, field_scores)
        """
        if predicted_df.empty and ground_truth_df.empty:
            return 1.0, {}
        if predicted_df.empty:
            return 0.0, {}  # We have nothing but should have
        if ground_truth_df.empty:
            return 1.0, {}  # We have something but no ground truth to compare = pass

        all_field_scores = {field: [] for field in field_types.keys()}
        matched_count = 0

        # Try to match rows by key columns
        for _, truth_row in ground_truth_df.iterrows():
            # Find matching prediction row
            mask = pd.Series([True] * len(predicted_df))
            for key in key_columns:
                if key in predicted_df.columns and key in truth_row.index:
                    mask = mask & (predicted_df[key] == truth_row[key])

            matched_rows = predicted_df[mask]

            if not matched_rows.empty:
                pred_row = matched_rows.iloc[0]
                matched_count += 1

                for field, field_type in field_types.items():
                    if field in pred_row.index and field in truth_row.index:
                        if field_type == 'text':
                            score = self.calculate_text_score(pred_row[field], truth_row[field])
                        elif field_type == 'numeric':
                            score = self.calculate_numeric_score(pred_row[field], truth_row[field])
                        elif field_type == 'enum':
                            score = self.calculate_enum_score(pred_row[field], truth_row[field])
                        elif field_type == 'boolean':
                            score = self.calculate_boolean_score(pred_row[field], truth_row[field])
                        else:
                            score = self.calculate_text_score(pred_row[field], truth_row[field])

                        all_field_scores[field].append(score)

        # Calculate average scores
        final_field_scores = {}
        for field, scores in all_field_scores.items():
            if scores:
                final_field_scores[field] = np.mean(scores)

        # Apply penalty for missing rows
        coverage = matched_count / len(ground_truth_df) if len(ground_truth_df) > 0 else 0
        overall = np.mean(list(final_field_scores.values())) * coverage if final_field_scores else 0.0

        return overall, final_field_scores

    def calculate_overall_dqs(
        self,
        predicted: Dict[str, pd.DataFrame],
        ground_truth: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """
        Calculate overall DQS across all tables.

        Returns:
            Dictionary with overall DQS, section scores, and table scores
        """
        # Get the submitter_ids and nacc_ids we actually processed
        processed_submitter_ids = set()
        processed_nacc_ids = set()
        for table_name, df in predicted.items():
            if 'submitter_id' in df.columns:
                processed_submitter_ids.update(df['submitter_id'].dropna().unique())
            if 'nacc_id' in df.columns:
                processed_nacc_ids.update(df['nacc_id'].dropna().unique())

        # Filter ground truth to only include rows we should have processed
        filtered_gt = {}
        for table_name, df in ground_truth.items():
            if df.empty:
                filtered_gt[table_name] = df
                continue

            # Filter by submitter_id or nacc_id
            if 'submitter_id' in df.columns and processed_submitter_ids:
                filtered_df = df[df['submitter_id'].isin(processed_submitter_ids)]
            elif 'nacc_id' in df.columns and processed_nacc_ids:
                filtered_df = df[df['nacc_id'].isin(processed_nacc_ids)]
            else:
                filtered_df = df

            filtered_gt[table_name] = filtered_df

        table_scores = {}
        section_scores = {section: [] for section in self.SECTION_WEIGHTS.keys()}

        # Define field types for key tables
        field_type_definitions = {
            'submitter_info': {
                'title': 'text',
                'first_name': 'text',
                'last_name': 'text',
                'age': 'numeric',
                'status': 'text',
                'sub_district': 'text',
                'district': 'text',
                'province': 'text',
            },
            'spouse_info': {
                'title': 'text',
                'first_name': 'text',
                'last_name': 'text',
                'age': 'numeric',
                'status': 'text',
            },
            'asset': {
                'asset_type_id': 'enum',
                'asset_name': 'text',
                'valuation': 'numeric',
                'owner_by_submitter': 'boolean',
                'owner_by_spouse': 'boolean',
                'owner_by_child': 'boolean',
            },
            'relative_info': {
                'relationship_id': 'enum',
                'title': 'text',
                'first_name': 'text',
                'last_name': 'text',
            },
            'statement': {
                'statement_type_id': 'enum',
                'valuation_submitter': 'numeric',
                'valuation_spouse': 'numeric',
                'valuation_child': 'numeric',
            },
        }

        # Key columns for matching - use composite keys to properly match rows
        key_columns_map = {
            'submitter_info': ['submitter_id'],
            'submitter_old_name': ['submitter_id', 'nacc_id'],
            'submitter_position': ['submitter_id', 'nacc_id', 'index', 'position_period_type_id'],
            'spouse_info': ['submitter_id', 'nacc_id'],
            'spouse_old_name': ['submitter_id', 'nacc_id'],
            'spouse_position': ['submitter_id', 'nacc_id', 'position'],
            'asset': ['submitter_id', 'nacc_id', 'index'],
            'asset_land_info': ['submitter_id', 'nacc_id', 'asset_index'],
            'asset_building_info': ['submitter_id', 'nacc_id', 'asset_index'],
            'asset_vehicle_info': ['submitter_id', 'nacc_id', 'asset_index'],
            'asset_other_asset_info': ['submitter_id', 'nacc_id', 'asset_index'],
            'relative_info': ['submitter_id', 'nacc_id', 'relationship_id', 'first_name'],
            'statement': ['submitter_id', 'nacc_id', 'statement_type_id'],
            'statement_detail': ['submitter_id', 'nacc_id', 'statement_type_id', 'statement_detail_type_id'],
        }

        # Calculate score for each table
        for table_name in self.TABLE_TO_SECTION.keys():
            pred_df = predicted.get(table_name, pd.DataFrame())
            truth_df = filtered_gt.get(table_name, pd.DataFrame())

            # Skip tables we didn't output (if pred is empty but truth has data for our submitters)
            if pred_df.empty:
                if truth_df.empty:
                    table_scores[table_name] = 1.0  # Both empty = perfect
                else:
                    table_scores[table_name] = 0.0  # We have no data for existing ground truth
                # Add 0 to section if we're missing this table
                section = self.TABLE_TO_SECTION.get(table_name)
                if section and not truth_df.empty:
                    section_scores[section].append(0.0)
                continue

            field_types = field_type_definitions.get(table_name, {})
            key_cols = key_columns_map.get(table_name, ['submitter_id', 'nacc_id'])

            if not field_types:
                # Default text comparison for all columns
                if not truth_df.empty:
                    field_types = {col: 'text' for col in truth_df.columns
                                  if col not in ['latest_submitted_date']}

            score, _ = self.calculate_table_dqs(pred_df, truth_df, key_cols, field_types)
            table_scores[table_name] = score

            # Add to section
            section = self.TABLE_TO_SECTION.get(table_name)
            if section:
                section_scores[section].append(score)

        # Calculate section averages
        final_section_scores = {}
        for section, scores in section_scores.items():
            final_section_scores[section] = np.mean(scores) if scores else 0.0

        # Calculate weighted overall DQS
        overall_dqs = sum(
            final_section_scores.get(section, 0) * weight
            for section, weight in self.SECTION_WEIGHTS.items()
        )

        return {
            'overall_dqs': overall_dqs,
            'passes_threshold': overall_dqs >= 0.70,
            'section_scores': final_section_scores,
            'table_scores': table_scores,
        }
