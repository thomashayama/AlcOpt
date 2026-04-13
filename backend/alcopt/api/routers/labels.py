from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO

from alcopt.api.dependencies import require_admin
from alcopt.config import FRONTEND_URL
from alcopt.labels import generate_label_pdf

router = APIRouter(prefix="/api/labels", tags=["labels"])


@router.get("/pdf")
def get_label_pdf(
    min_id: int = 1,
    max_id: int = 12,
    base_url: str = "",
    _admin: dict = Depends(require_admin),
):
    if min_id < 1:
        raise HTTPException(400, "min_id must be >= 1")
    if max_id < min_id:
        raise HTTPException(400, "max_id must be >= min_id")
    if max_id - min_id + 1 > 1000:
        raise HTTPException(400, "Range too large (max 1000 labels)")
    container_ids = list(range(min_id, max_id + 1))
    url = base_url or FRONTEND_URL
    pdf_bytes = generate_label_pdf(container_ids, base_url=url)
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=container_labels.pdf"},
    )
