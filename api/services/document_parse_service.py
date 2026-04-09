import os
import logging
import torch
from pathlib import Path
from magic_pdf.data.batch_build_dataset import batch_build_dataset
from magic_pdf.tools.common import batch_do_parse
from api.core.config import get_settings

# Workaround for torch.load security blocks (weights_only=True) in newer torch versions
import torch
import functools
_original_torch_load = torch.load
@functools.wraps(_original_torch_load)
def _hooked_torch_load(*args, **kwargs):
    if 'weights_only' not in kwargs:
        kwargs['weights_only'] = False
    return _original_torch_load(*args, **kwargs)
torch.load = _hooked_torch_load

settings = get_settings()

class DocumentParseService:
    def __init__(self):
        self.output_dir = Path(settings.DATA_DIR) / "parsed_documents"
        os.makedirs(self.output_dir, exist_ok=True)

    def parse_pdf(self, pdf_path: str, method: str = "auto") -> dict:
        """
        Parses a PDF file using magic-pdf.
        Returns metadata about the parsed content.
        """
        pdf_path_obj = Path(pdf_path)
        file_id = pdf_path_obj.stem
        
        # Build dataset using the recommended utility
        datasets = batch_build_dataset([str(pdf_path_obj)], 1)
        
        batch_do_parse(
            str(self.output_dir),
            [file_id],
            datasets,
            method,
            False # debug_able
        )
        
        result_dir = self.output_dir / file_id / method
        
        return {
            "file_id": file_id,
            "result_dir": str(result_dir),
            "markdown_file": str(result_dir / f"{file_id}.md"),
            "content_list_file": str(result_dir / f"{file_id}_content_list.json")
        }
