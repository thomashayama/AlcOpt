"""Printable QR-code label sheets for containers.

Each label has the container ID in large font on top, a QR code linking
to the container's Information page, and the same URL printed underneath
as a fallback. Labels are arranged in a grid on US Letter paper.

Note: Streamlit uses query parameters, not path segments, so the URL the
QR encodes is `<base>/Information?container_id=<id>`. The Information
page reads `container_id` from query params and auto-loads the container.
"""

from io import BytesIO

import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

DEFAULT_BASE_URL = "https://alcopt.thomashayama.com"

# US Letter, 3 x 4 grid (12 labels per page)
PAGE_W, PAGE_H = letter
COLS = 3
ROWS = 4
MARGIN = 0.5 * inch
GUTTER = 0.1 * inch


def container_url(container_id: int, base_url: str = DEFAULT_BASE_URL) -> str:
    return f"{base_url.rstrip('/')}/Information?container_id={container_id}"


def _qr_image(url: str) -> ImageReader:
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def _draw_label(c: canvas.Canvas, container_id: int, x0, y0, w, h, base_url: str):
    url = container_url(container_id, base_url)

    # Cut guide
    c.setStrokeColorRGB(0.75, 0.75, 0.75)
    c.setLineWidth(0.5)
    c.rect(x0, y0, w, h)

    # Layout zones (bottom-up): pad, URL, gap, QR, gap, ID, pad
    pad = 0.12 * inch
    id_band = 0.42 * inch
    url_band = 0.18 * inch
    gap = 0.06 * inch

    # ID at top
    id_baseline = y0 + h - pad - id_band + 0.05 * inch
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 32)
    c.drawCentredString(x0 + w / 2, id_baseline, f"#{container_id}")

    # URL at bottom
    url_baseline = y0 + pad + 0.04 * inch
    font_name = "Helvetica"
    font_size = 8.0
    max_width = w - 0.15 * inch
    while font_size > 5 and c.stringWidth(url, font_name, font_size) > max_width:
        font_size -= 0.5
    c.setFont(font_name, font_size)
    c.drawCentredString(x0 + w / 2, url_baseline, url)

    # QR fills the space between
    qr_top = id_baseline - gap
    qr_bottom = y0 + pad + url_band + gap
    qr_size = min(qr_top - qr_bottom, w - 0.3 * inch)
    qr_size = max(qr_size, 0.5 * inch)
    # Center vertically in the band
    band_mid = (qr_top + qr_bottom) / 2
    qr_y = band_mid - qr_size / 2
    qr_x = x0 + (w - qr_size) / 2
    c.drawImage(
        _qr_image(url),
        qr_x,
        qr_y,
        width=qr_size,
        height=qr_size,
        preserveAspectRatio=True,
        mask="auto",
    )


def generate_label_pdf(
    container_ids: list[int], base_url: str = DEFAULT_BASE_URL
) -> bytes:
    """Render a printable PDF of QR-code labels for the given container IDs."""
    if not container_ids:
        raise ValueError("container_ids must not be empty")

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setTitle("AlcOpt container labels")

    cell_w = (PAGE_W - 2 * MARGIN - (COLS - 1) * GUTTER) / COLS
    cell_h = (PAGE_H - 2 * MARGIN - (ROWS - 1) * GUTTER) / ROWS
    per_page = COLS * ROWS

    for idx, cid in enumerate(container_ids):
        on_page = idx % per_page
        if idx > 0 and on_page == 0:
            c.showPage()
        col = on_page % COLS
        row = on_page // COLS
        x0 = MARGIN + col * (cell_w + GUTTER)
        y0 = PAGE_H - MARGIN - (row + 1) * cell_h - row * GUTTER
        _draw_label(c, cid, x0, y0, cell_w, cell_h, base_url)

    c.save()
    return buf.getvalue()
