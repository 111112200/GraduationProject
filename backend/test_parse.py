from app.services.docx_parser_service import parse_docx_report
from pathlib import Path


import torch;
print('PyTorch version:', torch.__version__);
print('CUDA available:', torch.cuda.is_available());
print('CUDA build:', torch.version.cuda)

# for f in sorted(Path('uploads').glob('*.docx')):
#     try:
#         blocks = parse_docx_report(str(f))
#         print(f"{f.name}: {len(blocks)} blocks")
#         for b in blocks[:2]:
#             print(f"  [{b['section_type']}] {b['content'][:80]}...")
#     except Exception as e:
#         print(f"{f.name}: ERROR - {e}")
