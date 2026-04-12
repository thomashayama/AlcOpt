"""Printable QR-code label sheets for containers.

Each label has the container ID, a QR code linking to the container's
Information page, the URL as fallback text, and legally required alcohol
labelling information.  A random Truchet-tile pattern fills the background
with the word "Wine" knocked out as negative space.

Labels are arranged in a grid on US Letter paper.
"""

import random
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
MARGIN = 0
GUTTER = 0.1 * inch


def container_url(container_id: int, base_url: str = DEFAULT_BASE_URL) -> str:
    """Full URL for display / fallback."""
    return f"{base_url.rstrip('/')}/info?container_id={container_id}"


def container_short_url(container_id: int, base_url: str = DEFAULT_BASE_URL) -> str:
    """Shorter URL for QR encoding — fewer modules, easier to scan."""
    host = base_url.rstrip("/").removeprefix("https://").removeprefix("http://")
    return f"{host}/c/{container_id}"


def _qr_image(data: str) -> ImageReader:
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def _wrap_text(c: canvas.Canvas, text: str, font: str, size: float, max_w: float):
    """Word-wrap *text* and return a list of lines."""
    words = text.split()
    lines: list[str] = []
    cur = ""
    for word in words:
        test = f"{cur} {word}".strip()
        if c.stringWidth(test, font, size) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ── Truchet tiling ──────────────────────────────────────────────────────


def _draw_truchet_cell(
    c: canvas.Canvas, x, y, size, orientation: int, num_arcs: int = 4
):
    """Draw one curved Truchet tile with *num_arcs* concentric quarter-circles
    from each of the two active corners.  Creates a raked-sand / rock-garden
    aesthetic."""
    spacing = size / (num_arcs + 1)
    if orientation == 0:
        # Arcs from bottom-left and top-right corners
        for i in range(1, num_arcs + 1):
            r = i * spacing
            c.arc(x - r, y - r, x + r, y + r, 0, 90)
            c.arc(x + size - r, y + size - r, x + size + r, y + size + r, 180, 90)
    else:
        # Arcs from bottom-right and top-left corners
        for i in range(1, num_arcs + 1):
            r = i * spacing
            c.arc(x + size - r, y - r, x + size + r, y + r, 90, 90)
            c.arc(x - r, y + size - r, x + r, y + size + r, 270, 90)


def _draw_tiling(c: canvas.Canvas, x0, y0, w, h, seed: int):
    """Fill rectangle (x0, y0, w, h) with random curved Truchet tiles."""
    rng = random.Random(seed)
    tile_s = 0.15 * inch
    num_arcs = 4

    c.setLineCap(1)  # round caps for smooth joins
    ncols = int(w / tile_s) + 2
    nrows = int(h / tile_s) + 2
    for tr in range(nrows):
        for tc in range(ncols):
            _draw_truchet_cell(
                c,
                x0 + tc * tile_s,
                y0 + tr * tile_s,
                tile_s,
                rng.randint(0, 1),
                num_arcs,
            )


# ── Label drawing ───────────────────────────────────────────────────────


def _draw_label(c: canvas.Canvas, container_id: int, x0, y0, w, h, base_url: str):
    display_url = container_url(container_id, base_url)
    display_url = display_url.removeprefix("https://").removeprefix("http://")
    qr_data = container_url(container_id, base_url)

    cx = x0 + w / 2
    pad = 0.10 * inch
    text_left = x0 + pad
    text_right = x0 + w - pad
    max_text_w = w - 2 * pad

    # ── Truchet tiling background (clipped to label) ──
    c.saveState()
    clip = c.beginPath()
    clip.rect(x0, y0, w, h)
    c.clipPath(clip, stroke=0)

    c.setStrokeColorRGB(0.78, 0.78, 0.78)
    c.setLineWidth(0.35)
    _draw_tiling(c, x0, y0, w, h, seed=container_id)

    # "Wine" embedded in the tiling — dark tiling inside letters, black outline
    wine_size = 36
    c.setFont("Helvetica-Bold", wine_size)
    wine_tw = c.stringWidth("Wine", "Helvetica-Bold", wine_size)
    wine_y = y0 + h - pad - wine_size * 0.82

    # Draw dark tiling clipped to text shape
    c.saveState()
    textobj = c.beginText()
    textobj.setTextOrigin(cx - wine_tw / 2, wine_y)
    textobj.setFont("Helvetica-Bold", wine_size)
    textobj.setTextRenderMode(7)  # add text outline to clip path
    textobj.textLine("Wine")
    c.drawText(textobj)

    c.setStrokeColorRGB(0.25, 0.25, 0.25)
    c.setLineWidth(0.5)
    _draw_tiling(c, x0, y0, w, h, seed=container_id)
    c.restoreState()

    # Black outline around the letters
    textobj2 = c.beginText()
    textobj2.setTextOrigin(cx - wine_tw / 2, wine_y)
    textobj2.setFont("Helvetica-Bold", wine_size)
    textobj2.setTextRenderMode(1)  # stroke only
    textobj2.textLine("Wine")
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(1)
    c.drawText(textobj2)

    c.restoreState()  # restore label clip

    # ── Top-down: separator + container ID ──
    c.setFillColorRGB(0, 0, 0)
    top = wine_y - 7

    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.3)
    c.line(text_left, top, text_right, top)
    top -= 2

    id_size = 18
    c.setFont("Helvetica-Bold", id_size)
    id_text = str(container_id)
    id_tw = c.stringWidth(id_text, "Helvetica-Bold", id_size)
    id_baseline = top - id_size * 0.8

    # White halo — thick white stroke erases tiling behind the number
    c.saveState()
    c.setFillColorRGB(1, 1, 1)
    c.setStrokeColorRGB(1, 1, 1)
    c.setLineWidth(6)
    c.setLineJoin(1)  # round joins
    textobj = c.beginText()
    textobj.setTextOrigin(text_right - id_tw, id_baseline)
    textobj.setFont("Helvetica-Bold", id_size)
    textobj.setTextRenderMode(2)  # fill + stroke
    textobj.textLine(id_text)
    c.drawText(textobj)
    c.restoreState()

    # Black number on top
    c.setFillColorRGB(0, 0, 0)
    c.drawRightString(text_right, id_baseline, id_text)
    top = id_baseline - 4

    # ── Bottom-up: legal text ──
    bot = y0 + pad

    # Government warning
    gov_warning = (
        "GOVERNMENT WARNING: (1) According to the Surgeon "
        "General, women should not drink alcoholic beverages "
        "during pregnancy because of the risk of birth defects. "
        "(2) Consumption of alcoholic beverages impairs your "
        "ability to drive a car or operate machinery, and may "
        "cause health problems."
    )
    gov_size = 4.5
    gov_lines = _wrap_text(c, gov_warning, "Helvetica", gov_size, max_text_w)
    c.setFont("Helvetica", gov_size)
    for line in reversed(gov_lines):
        c.drawString(text_left, bot, line)
        bot += gov_size + 1.5
    bot += 3

    # Separator
    c.setLineWidth(0.3)
    c.line(text_left, bot, text_right, bot)
    bot += 5

    # Producer — left-aligned
    info_size = 5.5
    c.setFont("Helvetica", info_size)
    c.drawString(text_left, bot, "Produced & bottled by AlcOpt")
    bot += info_size + 3

    # May contain sulfites — left-aligned
    c.drawString(text_left, bot, "May Contain Sulfites")
    # ABV + volume — right-aligned, same line, same size
    c.drawRightString(text_right, bot, "Alc. xx% by vol.  |  xxx mL")
    bot += info_size + 4

    # Separator
    c.setLineWidth(0.3)
    c.line(text_left, bot, text_right, bot)
    bot += 4

    # ── QR code + centered URL ──
    url_size = 6.0
    while (
        url_size > 4 and c.stringWidth(display_url, "Helvetica", url_size) > max_text_w
    ):
        url_size -= 0.5
    url_band = url_size + 4

    qr_top = top
    qr_bottom = bot + url_band + 2
    available = qr_top - qr_bottom
    qr_size = min(available, w - 0.3 * inch)
    qr_size = max(qr_size, 0.4 * inch)
    band_mid = (qr_top + qr_bottom) / 2
    qr_y = band_mid - qr_size / 2
    qr_x = x0 + (w - qr_size) / 2

    # White background behind QR for reliable scanning
    qr_pad = 1
    c.setFillColorRGB(1, 1, 1)
    c.rect(
        qr_x - qr_pad,
        qr_y - qr_pad,
        qr_size + 2 * qr_pad,
        qr_size + 2 * qr_pad,
        fill=1,
        stroke=0,
    )

    c.drawImage(
        _qr_image(qr_data),
        qr_x,
        qr_y,
        width=qr_size,
        height=qr_size,
        preserveAspectRatio=True,
        mask="auto",
    )

    # URL centered below QR
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", url_size)
    c.drawCentredString(cx, qr_y - url_size - 2, display_url)


# ── PDF generation ──────────────────────────────────────────────────────


def generate_label_pdf(
    container_ids: list[int], base_url: str = DEFAULT_BASE_URL
) -> bytes:
    """Render a printable PDF of QR-code labels for the given container IDs."""
    if not container_ids:
        raise ValueError("container_ids must not be empty")

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setTitle("AlcOpt container labels")

    cell_w = (PAGE_W - 2 * MARGIN) / COLS
    cell_h = (PAGE_H - 2 * MARGIN) / ROWS
    per_page = COLS * ROWS

    def _draw_grid(cv: canvas.Canvas):
        """Draw shared grid lines so adjacent labels share a single cut line."""
        cv.setStrokeColorRGB(0, 0, 0)
        cv.setLineWidth(4.5)
        grid_left = MARGIN
        grid_right = MARGIN + COLS * cell_w
        grid_top = PAGE_H - MARGIN
        grid_bottom = PAGE_H - MARGIN - ROWS * cell_h
        cv.rect(grid_left, grid_bottom, grid_right - grid_left, grid_top - grid_bottom)
        for col in range(1, COLS):
            x = MARGIN + col * cell_w
            cv.line(x, grid_top, x, grid_bottom)
        for row in range(1, ROWS):
            y = PAGE_H - MARGIN - row * cell_h
            cv.line(grid_left, y, grid_right, y)

    grid_drawn_on_page = -1

    for idx, cid in enumerate(container_ids):
        on_page = idx % per_page
        page_num = idx // per_page
        if idx > 0 and on_page == 0:
            c.showPage()
        if page_num != grid_drawn_on_page:
            _draw_grid(c)
            grid_drawn_on_page = page_num
        col = on_page % COLS
        row = on_page // COLS
        x0 = MARGIN + col * cell_w
        y0 = PAGE_H - MARGIN - (row + 1) * cell_h
        _draw_label(c, cid, x0, y0, cell_w, cell_h, base_url)

    c.save()
    return buf.getvalue()
