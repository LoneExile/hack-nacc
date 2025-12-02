# NACC Asset Declaration Digitization

A solution for the "Hackathon Digitize ข้อมูลบัญชีทรัพย์สิน" competition - digitizing Thai NACC (National Anti-Corruption Commission) asset declaration documents using Claude Vision API.

## Solution Overview

### Approach
We use **Claude Vision API** to extract structured data from scanned PDF asset declaration documents. The solution converts PDF pages to images and uses Claude's multimodal capabilities to understand Thai handwritten/printed forms and extract all required fields.

### Architecture

```
PDF Documents
     │
     ▼
┌─────────────────┐
│  PDF Processor  │  Convert to images
└─────────────────┘
     │
     ▼
┌─────────────────┐
│ Claude Vision   │  Extract structured data
│   (Batched)     │  with Thai language support
└─────────────────┘
     │
     ▼
┌─────────────────┐
│ Pydantic Models │  Validate & structure
└─────────────────┘
     │
     ▼
┌─────────────────┐
│  CSV Outputs    │  13 output files
└─────────────────┘
```

### Key Features

- **Multimodal Document Understanding**: Uses Claude Vision to read Thai handwritten and printed forms
- **Batched Extraction**: Handles large documents (>25 pages) by splitting into batches
- **Buddhist Era Date Conversion**: Automatically converts BE dates to CE
- **Enum Mapping**: Maps extracted values to official NACC categories
- **DQS Validation**: Built-in scoring against ground truth for training data

---

## Installation

### Requirements
- Python 3.10+
- Claude API access (via proxy or direct)

### Setup

```bash
# Clone repository
git clone <repository-url>
cd hack-llm

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY="your-api-key"
export ANTHROPIC_BASE_URL=""  # Optional: custom endpoint
```

---

## Usage

### Extract Training Data (with validation)
```bash
python3 scripts/run_extraction.py --mode train --validate
```

### Extract Test Data
```bash
python3 scripts/run_extraction.py --mode test
```

### Extract Single Document
```bash
python3 scripts/run_extraction.py --mode train --limit 1
```

### Options
- `--mode`: `train` or `test`
- `--limit N`: Process only N documents
- `--validate`: Calculate DQS score (train mode only)

---

## Output Files

The solution generates 13 CSV files matching the competition format:

| File | Description |
|------|-------------|
| `submitter_old_name.csv` | Name changes of submitters |
| `submitter_position.csv` | Position history of submitters |
| `spouse_info.csv` | Spouse information |
| `spouse_old_name.csv` | Name changes of spouses |
| `spouse_position.csv` | Position history of spouses |
| `relative_info.csv` | Relative information |
| `statement.csv` | Financial statements |
| `statement_detail.csv` | Statement line items |
| `asset.csv` | Asset records |
| `asset_building_info.csv` | Building details |
| `asset_land_info.csv` | Land details |
| `asset_vehicle_info.csv` | Vehicle details |
| `asset_other_asset_info.csv` | Other asset details |

---

## Project Structure

```
hack-llm/
├── src/
│   ├── models/           # Pydantic data models
│   │   ├── submitter.py
│   │   ├── spouse.py
│   │   ├── relative.py
│   │   ├── statement.py
│   │   ├── asset.py
│   │   └── enums.py
│   ├── extractors/
│   │   └── claude_extractor.py   # Main extraction logic
│   ├── processors/
│   │   └── pdf_processor.py      # PDF to image conversion
│   ├── validators/
│   │   └── dqs_calculator.py     # DQS scoring
│   ├── utils/
│   │   └── enum_loader.py        # Load enum mappings
│   └── pipeline.py               # Orchestration
├── scripts/
│   └── run_extraction.py         # CLI entry point
├── outputs/                      # Generated CSV files
├── hack-the-assetdeclaration-data/  # Input data
└── requirements.txt
```

---

## Technical Details

### Batched Extraction
For documents exceeding 25 pages, we split extraction into batches to avoid API payload limits:

1. **Batch 1** (pages 1-25): Extract all data types
   - Submitter info, spouse, relatives
   - Statements and details
   - Assets (first portion)

2. **Batch 2+** (remaining pages): Extract assets only
   - Merge with previous batch
   - Renumber asset indices

### Date Handling
Thai documents use Buddhist Era (BE). We convert:
```
CE Year = BE Year - 543
```

### Enum Mapping
Values are mapped to official NACC categories:
- Position types
- Relationship types
- Asset types and acquisition types
- Statement types

---

## Tools and Resources

### AI/ML Tools
- **Claude Vision API** (claude-opus-4-5-20251101): Multimodal document understanding
- **Anthropic Python SDK**: API client

### Libraries
- **PyMuPDF (fitz)**: PDF processing and image extraction
- **Pydantic**: Data validation and serialization
- **Pandas**: CSV handling and data manipulation
- **Pillow**: Image processing

### Cost Estimate
- ~$0.50-1.00 per document (depending on page count)
- Batched requests for large documents

---

## Evaluation

### DQS (Digitization Quality Score)
The solution is evaluated using section-weighted scoring:

| Section | Weight |
|---------|--------|
| Submitter & Spouse | 0.25 |
| Statement & Details | 0.30 |
| Assets | 0.30 |
| Relatives | 0.15 |

### Current Performance
- Training DQS: ~65% (improving)
- Target: ≥70%

---

## Recommendations for NACC Data Publication

1. **Structured Digital Forms**: Use digital-first submission forms with validation
2. **OCR-Friendly Templates**: Standardize form layouts for easier processing
3. **Machine-Readable Dates**: Use ISO date format (YYYY-MM-DD)
4. **Unique Identifiers**: Add QR codes or barcodes linking to database records
5. **Open Data Standards**: Publish in structured formats (JSON, CSV) alongside PDFs

---

## License

MIT License

---

## Contact

For questions about this solution, contact the team.
