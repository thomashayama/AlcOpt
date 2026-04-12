from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO

from alcopt.api.dependencies import require_admin
from alcopt.labels import generate_label_pdf

router = APIRouter(prefix="/api/labels", tags=["labels"])


@router.get("/pdf")
def get_label_pdf(
    min_id: int = 1,
    max_id: int = 12,
    base_url: str = "https://alcopt.thomashayama.com",
    _admin: dict = Depends(require_admin),
):
    if max_id < min_id:
        raise HTTPException(400, "max_id must be >= min_id")
    container_ids = list(range(min_id, max_id + 1))
    pdf_bytes = generate_label_pdf(container_ids, base_url=base_url)
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=container_labels.pdf"},
    )
