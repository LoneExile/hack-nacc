"""PDF processing module for extracting images from PDF files."""

import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Optional
from PIL import Image
import io
import base64


class PDFProcessor:
    """Process PDF files and extract pages as images for Claude vision API."""

    def __init__(self, pdf_path: Path):
        """
        Initialize the PDF processor.

        Args:
            pdf_path: Path to the PDF file
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        self.doc = fitz.open(self.pdf_path)
        self.num_pages = len(self.doc)

    def get_page_image(self, page_num: int, zoom: float = 2.0) -> Image.Image:
        """
        Extract a page as PIL Image.

        Args:
            page_num: Page number (0-indexed)
            zoom: Zoom factor for better quality (default 2.0)

        Returns:
            PIL Image of the page
        """
        if page_num < 0 or page_num >= self.num_pages:
            raise ValueError(f"Page {page_num} out of range (0-{self.num_pages-1})")

        page = self.doc[page_num]
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        return img

    def get_page_base64(self, page_num: int, zoom: float = 1.5, quality: int = 85) -> str:
        """
        Get page image as base64 string for Claude API.

        Args:
            page_num: Page number (0-indexed)
            zoom: Zoom factor (lower = smaller file, faster processing)
            quality: JPEG quality (lower = smaller file)

        Returns:
            Base64 encoded JPEG image
        """
        img = self.get_page_image(page_num, zoom)

        # Resize if too large (Claude has limits)
        max_size = 2000
        if img.width > max_size or img.height > max_size:
            ratio = min(max_size / img.width, max_size / img.height)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=quality, optimize=True)
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        return img_base64

    def get_page_text(self, page_num: int) -> str:
        """
        Extract text from page (if PDF is searchable).

        Args:
            page_num: Page number (0-indexed)

        Returns:
            Extracted text content
        """
        page = self.doc[page_num]
        return page.get_text()

    def get_all_pages_base64(self, zoom: float = 1.5, quality: int = 85) -> List[str]:
        """
        Get all pages as base64 encoded images.

        Args:
            zoom: Zoom factor for all pages
            quality: JPEG quality for all pages

        Returns:
            List of base64 encoded images
        """
        return [
            self.get_page_base64(i, zoom, quality)
            for i in range(self.num_pages)
        ]

    def get_pages_range_base64(
        self,
        start: int = 0,
        end: Optional[int] = None,
        zoom: float = 1.5,
        quality: int = 85
    ) -> List[str]:
        """
        Get a range of pages as base64 images.

        Args:
            start: Start page (0-indexed)
            end: End page (exclusive), None for all remaining
            zoom: Zoom factor
            quality: JPEG quality

        Returns:
            List of base64 encoded images
        """
        if end is None:
            end = self.num_pages
        end = min(end, self.num_pages)

        return [
            self.get_page_base64(i, zoom, quality)
            for i in range(start, end)
        ]

    def is_searchable(self) -> bool:
        """
        Check if PDF contains searchable text.

        Returns:
            True if PDF has extractable text
        """
        # Check first few pages for text
        for i in range(min(3, self.num_pages)):
            text = self.get_page_text(i)
            if len(text.strip()) > 50:  # Has meaningful text
                return True
        return False

    def get_document_info(self) -> dict:
        """
        Get document metadata.

        Returns:
            Dictionary with document info
        """
        return {
            "num_pages": self.num_pages,
            "is_searchable": self.is_searchable(),
            "file_name": self.pdf_path.name,
            "file_size_kb": self.pdf_path.stat().st_size / 1024,
        }

    def close(self):
        """Close the PDF document."""
        self.doc.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __len__(self):
        return self.num_pages
