"""Claude-based document extraction using vision capabilities."""

import anthropic
import os
import json
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class ClaudeExtractor:
    """Extract structured data from NACC documents using Claude Sonnet 4.5 Vision."""

    def __init__(self, model: Optional[str] = None):
        """
        Initialize the Claude extractor.

        Args:
            model: Model to use (defaults to env CLAUDE_MODEL)
        """
        base_url = os.getenv("ANTHROPIC_BASE_URL")
        api_key = os.getenv("ANTHROPIC_AUTH_TOKEN")

        if not api_key:
            raise ValueError("ANTHROPIC_AUTH_TOKEN not set in environment")

        self.client = anthropic.Anthropic(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model or os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "8192"))
        self.temperature = float(os.getenv("TEMPERATURE", "0"))

    def _build_image_content(self, page_images: List[str]) -> List[dict]:
        """Build image content blocks for API request."""
        content = []
        for img_base64 in page_images:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": img_base64
                }
            })
        return content

    def _parse_json_response(self, response_text: str) -> Any:
        """Parse JSON from Claude's response, handling markdown code blocks."""
        # Try direct JSON parse
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Try finding JSON array or object
        array_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if array_match:
            try:
                return json.loads(array_match.group(0))
            except json.JSONDecodeError:
                pass

        obj_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if obj_match:
            try:
                return json.loads(obj_match.group(0))
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Could not parse JSON from response: {response_text[:500]}...")

    def _call_claude(self, content: List[dict], system_prompt: str = "") -> str:
        """Make API call to Claude using streaming for large requests."""
        messages = [{"role": "user", "content": content}]

        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": messages,
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        # Use streaming for large requests (high max_tokens or many images)
        num_images = sum(1 for c in content if c.get("type") == "image")
        use_streaming = self.max_tokens > 10000 or num_images > 5

        if use_streaming:
            # Stream the response
            response_text = ""
            with self.client.messages.stream(**kwargs) as stream:
                for text in stream.text_stream:
                    response_text += text
            return response_text
        else:
            response = self.client.messages.create(**kwargs)
            return response.content[0].text

    def extract_all_data(self, page_images: List[str], nacc_id: int, submitter_id: int) -> Dict[str, Any]:
        """
        Extract all document data in a single comprehensive call.

        Args:
            page_images: List of base64 encoded page images
            nacc_id: NACC document ID
            submitter_id: Submitter ID

        Returns:
            Dictionary with all extracted data
        """
        system_prompt = """You are an expert at extracting structured data from Thai NACC asset declaration documents (เอกสารบัญชีทรัพย์สินและหนี้สิน).
You must extract ALL information accurately and return it as valid JSON.
IMPORTANT: Convert all Buddhist Era (พ.ศ.) years to Common Era (ค.ศ.) by subtracting 543.
Use null for missing or unclear fields. Be precise with numbers and Thai text."""

        prompt = f"""Analyze this Thai NACC asset declaration document carefully.
Extract ALL the following information and return as a single JSON object.

NACC ID: {nacc_id}
Submitter ID: {submitter_id}

Return JSON with this exact structure:
{{
    "submitter": {{
        "title": "คำนำหน้า (นาย/นาง/นางสาว/พลเอก/etc.)",
        "first_name": "ชื่อ",
        "last_name": "นามสกุล",
        "age": null or integer,
        "status": "สถานะการสมรส (สมรส/โสด/หย่า/etc.)",
        "status_date": "DD" or null,
        "status_month": "MM" or null,
        "status_year": "YYYY CE" or null,
        "sub_district": "ตำบล/แขวง",
        "district": "อำเภอ/เขต",
        "province": "จังหวัด",
        "post_code": "รหัสไปรษณีย์" or null
    }},
    "submitter_positions": [
        {{
            "position_period_type_id": 1 for current position (ตำแหน่งปัจจุบัน), 2 for concurrent, 3 for past,
            "index": sequential number starting from 0,
            "position": "ตำแหน่ง",
            "position_category_type_id": "1-6 based on position type",
            "workplace": "หน่วยงาน",
            "workplace_location": "สถานที่ทำงาน",
            "start_date": "DD" or null,
            "start_month": "MM" or null,
            "start_year": "YYYY CE" or null,
            "end_date": "DD" or null,
            "end_month": "MM" or null,
            "end_year": "YYYY CE" or null,
            "note": "หมายเหตุ" or null
        }}
    ],
    "spouse": {{
        "title": "คำนำหน้า" or null if no spouse,
        "first_name": "ชื่อ" or null,
        "last_name": "นามสกุล" or null,
        "age": integer or null,
        "status": "สถานะ (จดทะเบียนสมรส/etc.)",
        "status_date": "DD" or null,
        "status_month": "MM" or null,
        "status_year": "YYYY CE" or null
    }},
    "spouse_positions": [
        {{
            "position_period_type_id": 2 (always 2 for spouse concurrent positions),
            "index": sequential number starting from 1,
            "position": "ตำแหน่ง (use / without spaces to separate multiple titles, e.g. กรรมการ/กรรมการบริหาร/รักษาการประธานกรรมการบริหาร)",
            "workplace": "หน่วยงาน (company/organization name)",
            "workplace_location": "ตำบลXXX อำเภอYYY จังหวัดZZZ ZZZZZ (use this format: ตำบล + sub-district + อำเภอ + district + จังหวัด + province + postal code)"
        }}
    ],
    "relatives": [
        {{
            "index": sequential number starting from 1,
            "relationship_id": 1=บิดา, 2=มารดา, 3=พี่น้อง, 4=บุตร, 5=บิดาคู่สมรส, 6=มารดาคู่สมรส,
            "title": "คำนำหน้า",
            "first_name": "ชื่อ",
            "last_name": "นามสกุล",
            "age": integer or null,
            "occupation": "อาชีพ" or null,
            "workplace": "หน่วยงาน" or null,
            "is_deceased": true/false
        }}
    ],
    "statements": [
        {{
            "statement_type_id": 1=รายได้รวม (total income), 2=รายจ่ายรวม (total expenses), 3=รายได้-รายจ่าย (net), 4=ทรัพย์สินรวม (total assets), 5=หนี้สินรวม (total liabilities),
            "valuation_submitter": float or null - Look for column header "ผู้ยื่น" - this is the submitter's value,
            "valuation_spouse": float or null - Look for column header "คู่สมรส" - this is the spouse's value,
            "valuation_child": float or null - Look for column header "บุตรที่ยังไม่บรรลุนิติภาวะ" - this is the child's value
        }}
        CRITICAL: For types 1-5, carefully match values to their column HEADERS, not positions.
        The columns ARE: ผู้ยื่น (submitter) | คู่สมรส (spouse) | บุตร (child).
        Type 3 should use values from row labeled "รายได้-รายจ่าย" or "รวม" in the summary table - NOT calculated.
    ],
    "statement_details": [
        {{
            "statement_detail_type_id": integer (see Statement Detail Type Reference below),
            "index": sequential number starting from 1 within each type,
            "detail": "รายละเอียด (เช่น เงินเดือน, ดอกเบี้ยเงินฝาก, ค่าใช้จ่าย)",
            "valuation_submitter": float or null,
            "valuation_spouse": float or null,
            "valuation_child": float or null,
            "note": "หมายเหตุ" or null
        }}
    ],
    "assets": [
        {{
            "index": sequential number starting from 1 (will be re-indexed per category),
            "asset_type_id": integer (1-39 based on asset type enum),
            "asset_type_main": "ที่ดิน/โรงเรือนและสิ่งปลูกสร้าง/ยานพาหนะ/สิทธิและสัมปทาน/ทรัพย์สินอื่น",
            "asset_type_sub": "sub-type like โฉนด, รถยนต์, etc.",
            "asset_type_other": "for 'other' types (36,37,38,39), describe what it is here (e.g. ทาวน์เฮ้าส์, เงินสงเคราะห์)",
            "asset_name": "FULL description with details - for land: โฉนด; for buildings: ห้องชุด or ห้องชุดเพนท์เฮ้าส์ or บ้านเดี่ยว 3 ชั้น; for rights: สิทธิในกรมธรรม์ประกันภัย เลขที่ XXX บริษัท YYY; for membership: สิทธิในสมาชิก ZZZ หมายเลข NNN; for funds: กองทุนเพื่อผู้เคยเป็นสมาชิกรัฐสภา สำนักงานเลขาธิการสภาผู้แทนราษฎร; for other assets: กระเป๋า Hermes รุ่น Himalayan Birkin",
            "date_acquiring_type_id": 1 (if date exists) or 2 (if no date specified),
            "acquiring_date": integer day without leading zeros (1-31) or null,
            "acquiring_month": integer month without leading zeros (1-12) or null,
            "acquiring_year": integer YYYY CE or null,
            "ending_date": integer day without leading zeros or null,
            "ending_month": integer month without leading zeros or null,
            "ending_year": integer YYYY CE or null,
            "valuation": float (มูลค่า),
            "owner_by_submitter": true/false,
            "owner_by_spouse": true/false,
            "owner_by_child": true/false,
            "land_info": {{
                "land_doc_number": "เลขที่เอกสาร/เลขที่โฉนด",
                "rai": "float - FIRST number in land size (ไร่), 0-999",
                "ngan": "float - SECOND number in land size (งาน), ALWAYS 0-3 since 4 ngan = 1 rai",
                "sq_wa": "float - THIRD number in land size (ตารางวา)",
                "sub_district": "ตำบล/แขวง from the location field",
                "district": "อำเภอ/เขต from the location field",
                "province": "จังหวัด from the location field"
            }} or null if not land,
            "building_info": {{
                "building_doc_number": "เลขที่เอกสาร",
                "sub_district": "ตำบล",
                "district": "อำเภอ",
                "province": "จังหวัด"
            }} or null if not building,
            "vehicle_info": {{
                "registration_number": "เลขทะเบียน",
                "vehicle_brand": "ยี่ห้อ",
                "vehicle_model": "รุ่น",
                "registration_province": "จังหวัด"
            }} or null if not vehicle,
            "other_info": {{
                "count": integer,
                "unit": "หน่วย"
            }} or null if not other asset
        }}
    ]
}}

Asset Type ID Reference:
- Land (ที่ดิน): 1=โฉนด, 2=ส.ป.ก, 3=ส.ป.ก4-01, 4=น.ส.3, 5=น.ส.3ก, 6=ภบท.5, 7=ห้องชุด(อ.ช.2), 8=สัญญาซื้อขาย, 9=น.ค.3, 36=อื่นๆ
- Building (โรงเรือน): 10=บ้าน/บ้านเดี่ยว, 11=อาคาร, 12=ตึก, 13=ห้องชุด/คอนโด/เพนท์เฮ้าส์, 14=คอนโด, 15=หอพัก, 16=ลานจอดรถ, 17=โรงงาน, 37=อื่นๆ(ทาวน์เฮ้าส์ ใช้ 37 และใส่ asset_type_other="ทาวน์เฮ้าส์")
- Vehicle (ยานพาหนะ): 18=รถยนต์, 19=จักรยานยนต์/รถจักรยานยนต์, 20=เรือยนต์, 21=เครื่องบิน, 38=อื่นๆ
- Rights (สิทธิและสัมปทาน): 22=กรมธรรม์/ประกันภัย, 23=สัญญา, 24=สมาชิก/สิทธิในสมาชิก, 25=กองทุน, 26=เงินสงเคราะห์(ใช้น้อย), 27=ป้ายประมูล, 39=อื่นๆ(เงินสงเคราะห์ชราภาพมาตรา33/39 ใช้ 39 และใส่ asset_type_other="เงินสงเคราะห์")
- Other (ทรัพย์สินอื่น): 28=กระเป๋า, 29=อาวุธปืน, 30=นาฬิกา, 31=เครื่องประดับ, 32=วัตถุมงคล, 33=ทองคำ, 34=งานศิลปะ, 35=ของสะสม

IMPORTANT Asset Type Mapping:
- ทาวน์เฮ้าส์ -> asset_type_id=37, asset_type_other="ทาวน์เฮ้าส์", asset_name="ทาวน์เฮ้าส์"
- เงินสงเคราะห์ชราภาพมาตรา 33/39 -> asset_type_id=39, asset_type_other="เงินสงเคราะห์", asset_name="เงินสงเคราะห์ชราภาพมาตรา 33/39 สำนักงานประกันสังคม"
- ห้องชุดเพนท์เฮ้าส์ -> asset_type_id=13, asset_name="ห้องชุดเพนท์เฮ้าส์" (not just ห้องชุด)
- บ้านเดี่ยว 3 ชั้น -> asset_type_id=10, asset_name="บ้านเดี่ยว 3 ชั้น" (include floors if specified)

Statement Detail Type Reference (extract ALL of these from the income/expense and summary tables):
- Income (รายได้): 1=รายได้ประจำ (เงินเดือน, เงินประจำตำแหน่ง), 2=รายได้จากการลงทุน (ดอกเบี้ยเงินฝาก, เงินปันผล), 3=รายได้อื่น (เงินได้จากบุพการี, ทรัพย์สินจากคู่สมรส)
- Expense (รายจ่าย): 5=รายจ่ายลงทุน (เงินปันผล LTF/SSF, ขายกองทุน), 6=รายจ่ายปกติ (ค่าใช้จ่ายอุปโภค, ค่าเบี้ยประกัน, ค่าผ่อนบ้าน), 7=รายจ่ายอื่น (ค่าท่องเที่ยว, เงินบริจาค)
- Asset Summaries: 8=เงินสด, 9=เงินฝาก, 10=เงินลงทุน, 11=เงินให้กู้ยืม, 12=ที่ดิน, 13=โรงเรือนและสิ่งปลูกสร้าง, 14=ยานพาหนะ, 15=สิทธิและสัมปทาน, 16=ทรัพย์สินอื่น
- Liability Summaries: 18=เงินกู้ธนาคารและสถาบันการเงินอื่น, 19=หนี้สินที่มีหลักฐานเป็นหนังสือ, 20=หนี้สินอื่น

IMPORTANT:
1. Extract ALL assets listed in all pages
2. Convert Buddhist Era years (พ.ศ.) to CE by subtracting 543
3. For each asset, determine the correct asset_type_id from the reference
4. Include type-specific info (land_info, building_info, vehicle_info, other_info) based on asset type
5. Use true/false for owner fields based on checkboxes in document
6. Extract ALL statement_details from income/expense tables AND asset/liability summary tables (types 1-3, 5-7, 8-16, 18-20)
7. For statement_details types 8-20, use index=1 and set detail to the category name (เงินสด, เงินฝาก, etc.)
8. Return ONLY valid JSON, no explanatory text"""

        # Build content with images and prompt
        content = self._build_image_content(page_images)
        content.append({"type": "text", "text": prompt})

        # Call Claude
        response_text = self._call_claude(content, system_prompt)

        # Parse and return
        return self._parse_json_response(response_text)

    def extract_submitter_info(self, page_images: List[str]) -> Dict[str, Any]:
        """Extract only submitter information from first pages."""
        prompt = """Extract submitter (ผู้ยื่น) information from this NACC document.
Return JSON:
{
    "title": "คำนำหน้า",
    "first_name": "ชื่อ",
    "last_name": "นามสกุล",
    "age": integer or null,
    "status": "สถานะการสมรส",
    "status_date": "DD" or null,
    "status_month": "MM" or null,
    "status_year": "YYYY CE (convert from BE)" or null,
    "sub_district": "ตำบล/แขวง",
    "district": "อำเภอ/เขต",
    "province": "จังหวัด",
    "post_code": "รหัสไปรษณีย์" or null
}
Convert Buddhist Era (พ.ศ.) to CE by subtracting 543.
Return ONLY JSON."""

        content = self._build_image_content(page_images[:3])  # First 3 pages
        content.append({"type": "text", "text": prompt})

        response = self._call_claude(content)
        return self._parse_json_response(response)

    def extract_assets_batch(self, page_images: List[str]) -> List[Dict[str, Any]]:
        """Extract all assets from asset section pages."""
        prompt = """Extract ALL assets (ทรัพย์สิน) from this NACC document.
Return a JSON array of assets:
[
    {
        "index": 1,
        "asset_type_id": integer (see reference),
        "asset_type_main": "main category",
        "asset_type_sub": "sub category",
        "asset_name": "description",
        "acquiring_date": "DD" or null,
        "acquiring_month": "MM" or null,
        "acquiring_year": "YYYY CE",
        "valuation": float,
        "owner_by_submitter": true/false,
        "owner_by_spouse": true/false,
        "owner_by_child": true/false
    }
]

Asset Type IDs:
Land: 1-9, 36 | Building: 10-17, 37 | Vehicle: 18-21, 38 | Rights: 22-27, 39 | Other: 28-35

Convert พ.ศ. to CE by subtracting 543.
Return ONLY JSON array."""

        content = self._build_image_content(page_images)
        content.append({"type": "text", "text": prompt})

        response = self._call_claude(content)
        return self._parse_json_response(response)

    def extract_all_data_batched(
        self,
        page_images: List[str],
        nacc_id: int,
        submitter_id: int,
        max_pages_per_batch: int = 25
    ) -> Dict[str, Any]:
        """
        Extract all document data with batching for large documents.

        For documents > max_pages_per_batch, splits into multiple API calls
        and merges results. First batch extracts everything, subsequent batches
        focus on assets from remaining pages.

        Args:
            page_images: List of base64 encoded page images
            nacc_id: NACC document ID
            submitter_id: Submitter ID
            max_pages_per_batch: Maximum pages per API call (default 25)

        Returns:
            Dictionary with all extracted data merged from batches
        """
        num_pages = len(page_images)

        # If document is small enough, use single call
        if num_pages <= max_pages_per_batch:
            return self.extract_all_data(page_images, nacc_id, submitter_id)

        # For large documents, use batched approach
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"  Large document ({num_pages} pages), using batched extraction")

        # First batch: get submitter, spouse, relatives, statements from first pages
        # and some assets
        first_batch_size = max_pages_per_batch
        first_batch = page_images[:first_batch_size]

        logger.info(f"  Batch 1: pages 1-{first_batch_size}")
        result = self.extract_all_data(first_batch, nacc_id, submitter_id)

        # Process remaining pages in batches for additional assets
        remaining_pages = page_images[first_batch_size:]
        batch_num = 2

        while remaining_pages:
            batch = remaining_pages[:max_pages_per_batch]
            remaining_pages = remaining_pages[max_pages_per_batch:]

            start_page = first_batch_size + (batch_num - 2) * max_pages_per_batch + 1
            end_page = start_page + len(batch) - 1
            logger.info(f"  Batch {batch_num}: pages {start_page}-{end_page} (assets only)")

            # Extract only assets from subsequent batches
            additional_assets = self._extract_assets_only(batch, nacc_id, submitter_id)

            # Merge assets into result
            if additional_assets:
                existing_assets = result.get('assets', [])
                # Renumber indices for new assets
                max_idx = max([a.get('index', 0) for a in existing_assets], default=0)
                for asset in additional_assets:
                    max_idx += 1
                    asset['index'] = max_idx
                existing_assets.extend(additional_assets)
                result['assets'] = existing_assets

            batch_num += 1

        logger.info(f"  Batched extraction complete: {len(result.get('assets', []))} total assets")
        return result

    def _extract_assets_only(
        self,
        page_images: List[str],
        nacc_id: int,
        submitter_id: int
    ) -> List[Dict[str, Any]]:
        """Extract only assets from a batch of pages."""
        system_prompt = """You are an expert at extracting structured data from Thai NACC asset declaration documents.
Extract ONLY the assets from these pages. Return valid JSON array."""

        prompt = f"""Extract ALL assets from these pages of a Thai NACC document.
NACC ID: {nacc_id}, Submitter ID: {submitter_id}

Return a JSON array of assets:
[
    {{
        "index": sequential number,
        "asset_type_id": integer (1-39),
        "asset_type_main": "ที่ดิน/โรงเรือน/ยานพาหนะ/สิทธิและสัมปทาน/ทรัพย์สินอื่น",
        "asset_type_sub": "sub-type",
        "asset_type_other": "for 'other' types" or null,
        "asset_name": "description",
        "date_acquiring_type_id": 1 or 2,
        "acquiring_date": day or null,
        "acquiring_month": month or null,
        "acquiring_year": YYYY CE or null,
        "ending_date": day or null,
        "ending_month": month or null,
        "ending_year": YYYY CE or null,
        "valuation": float,
        "owner_by_submitter": true/false,
        "owner_by_spouse": true/false,
        "owner_by_child": true/false,
        "land_info": {{...}} or null,
        "building_info": {{...}} or null,
        "vehicle_info": {{...}} or null,
        "other_info": {{...}} or null
    }}
]

Asset Type IDs: Land(1-9,36), Building(10-17,37), Vehicle(18-21,38), Rights(22-27,39), Other(28-35)
Convert พ.ศ. to CE by subtracting 543.
Return ONLY valid JSON array, empty array [] if no assets found."""

        content = self._build_image_content(page_images)
        content.append({"type": "text", "text": prompt})

        try:
            response_text = self._call_claude(content, system_prompt)
            assets = self._parse_json_response(response_text)
            return assets if isinstance(assets, list) else []
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"  Failed to extract assets from batch: {e}")
            return []
