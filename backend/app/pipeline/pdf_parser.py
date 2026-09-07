import os
from typing import List, Dict, Any, Tuple
try:
    import pymupdf as fitz
except ImportError:
    import fitz


class PDFPageData:
    def __init__(self, page_number: int, text: str, blocks: List[Dict[str, Any]]):
        self.page_number = page_number
        self.text = text
        self.blocks = blocks

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)


class PDFParser:
    """Page-aware PDF text block and bounding box extractor using PyMuPDF."""
    
    @staticmethod
    def parse_pdf(file_path: str) -> Tuple[int, List[PDFPageData]]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
            
        doc = fitz.open(file_path)
        page_count = len(doc)
        pages_data: List[PDFPageData] = []
        
        for page_idx in range(page_count):
            page = doc[page_idx]
            page_num = page_idx + 1
            full_text = page.get_text("text")
            
            # Extract structured text blocks with bounding boxes
            # format: "dict" mode gives text blocks, lines, spans with bbox
            page_dict = page.get_text("dict")
            blocks: List[Dict[str, Any]] = []
            
            for b in page_dict.get("blocks", []):
                if b.get("type") == 0:  # Text block
                    block_bbox = list(b.get("bbox", [0, 0, 0, 0]))
                    block_text_lines = []
                    for line in b.get("lines", []):
                        line_text = "".join([span.get("text", "") for span in line.get("spans", [])])
                        if line_text.strip():
                            block_text_lines.append(line_text.strip())
                    
                    block_text = " ".join(block_text_lines)
                    if block_text.strip():
                        blocks.append({
                            "bbox": [round(c, 2) for c in block_bbox],
                            "text": block_text,
                            "lines": block_text_lines
                        })
            
            pages_data.append(PDFPageData(
                page_number=page_num,
                text=full_text,
                blocks=blocks
            ))
            
        doc.close()
        return page_count, pages_data
