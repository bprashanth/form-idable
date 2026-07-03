import base64
import io

import fitz
from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter()


@router.post("/pdf/pages")
async def pdf_pages(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "File must be a PDF")

    data = await file.read()
    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception as e:
        raise HTTPException(400, f"Could not open PDF: {e}")

    pages = []
    for i, page in enumerate(doc):
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        jpeg_bytes = pix.tobytes("jpeg", jpg_quality=92)
        pages.append({
            "page": i + 1,
            "image": base64.b64encode(jpeg_bytes).decode(),
            "width": pix.width,
            "height": pix.height,
        })

    doc.close()
    return {"page_count": len(pages), "pages": pages}
