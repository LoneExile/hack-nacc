"""Enum loader for NACC lookup tables."""

import pandas as pd
from pathlib import Path
from typing import Dict, Optional
from functools import lru_cache


class EnumLoader:
    """Load and cache enum lookup tables from CSV files."""

    def __init__(self, enum_dir: Path):
        """
        Initialize enum loader.

        Args:
            enum_dir: Directory containing enum CSV files
        """
        self.enum_dir = Path(enum_dir)
        if not self.enum_dir.exists():
            raise FileNotFoundError(f"Enum directory not found: {enum_dir}")

    @lru_cache(maxsize=32)
    def load_enum(self, enum_name: str) -> pd.DataFrame:
        """Load an enum CSV file."""
        file_path = self.enum_dir / f"{enum_name}.csv"
        if not file_path.exists():
            raise FileNotFoundError(f"Enum file not found: {file_path}")
        return pd.read_csv(file_path)

    def get_relationship_types(self) -> Dict[int, str]:
        """Get relationship ID to name mapping."""
        df = self.load_enum("relationship")
        return dict(zip(df['relationship_id'], df['relationship_name']))

    def get_asset_types(self) -> pd.DataFrame:
        """Get asset types dataframe."""
        return self.load_enum("asset_type")

    def get_statement_types(self) -> pd.DataFrame:
        """Get statement types dataframe."""
        return self.load_enum("statement_type")

    def match_asset_type_id(self, main_type: str, sub_type: Optional[str] = None) -> int:
        """
        Match asset type text to asset_type_id.

        Args:
            main_type: Main asset type (ที่ดิน, โรงเรือน, etc.)
            sub_type: Sub-type if available

        Returns:
            asset_type_id
        """
        df = self.get_asset_types()
        main_type_lower = main_type.lower().strip() if main_type else ""

        # Try exact sub_type match first
        if sub_type:
            sub_type_lower = sub_type.lower().strip()
            for _, row in df.iterrows():
                if (sub_type_lower in str(row['asset_type_sub_type_name']).lower()):
                    return int(row['asset_type_id'])

        # Match by main type
        type_mapping = {
            'ที่ดิน': 1,  # Default to โฉนด
            'land': 1,
            'โรงเรือน': 10,  # Default to บ้าน
            'สิ่งปลูกสร้าง': 10,
            'building': 10,
            'ยานพาหนะ': 18,  # Default to รถยนต์
            'vehicle': 18,
            'รถยนต์': 18,
            'รถจักรยานยนต์': 19,
            'สิทธิ': 22,  # Default to กรมธรรม์
            'สัมปทาน': 22,
            'rights': 22,
            'กรมธรรม์': 22,
            'ทรัพย์สินอื่น': 28,  # Default to กระเป๋า
            'other': 28,
        }

        for key, type_id in type_mapping.items():
            if key in main_type_lower:
                return type_id

        return 1  # Default to land/โฉนด

    def match_relationship_id(self, text: str) -> int:
        """
        Match relationship text to relationship_id.

        Args:
            text: Relationship description in Thai

        Returns:
            relationship_id (1-6)
        """
        text_lower = text.lower().strip() if text else ""

        mapping = {
            'บิดา': 1,
            'พ่อ': 1,
            'father': 1,
            'มารดา': 2,
            'แม่': 2,
            'mother': 2,
            'พี่': 3,
            'น้อง': 3,
            'พี่น้อง': 3,
            'sibling': 3,
            'บุตร': 4,
            'ลูก': 4,
            'child': 4,
            'บิดาคู่สมรส': 5,
            'พ่อสามี': 5,
            'พ่อภรรยา': 5,
            'มารดาคู่สมรส': 6,
            'แม่สามี': 6,
            'แม่ภรรยา': 6,
        }

        for key, rel_id in mapping.items():
            if key in text_lower:
                return rel_id

        return 4  # Default to child
