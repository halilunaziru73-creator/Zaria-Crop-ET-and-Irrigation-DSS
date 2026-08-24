"""
panel_layout.py
-----------------
Combines several already-generated matplotlib figures into ONE compact, bordered
grid-panel image with (A), (B), (C)... sub-labels -- the multi-panel research-figure
style (Figure X: (A) ... (B) ... (C) ...) rather than one full-page image per figure,
which was previously running off the bottom of report pages.
"""
import os
import math
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", "figures")

_FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

CELL_LABELS = "ABCDEFGHIJ"


def assemble_grid_panel(image_paths: list, title: str, fname: str, ncols: int = 2,
                         cell_w: int = 620, pad: int = 14, border_color=(40, 60, 55),
                         label_color=(20, 40, 35)) -> str:
    """
    image_paths: list of (path, caption) tuples, in the order they should be labelled
    (A), (B), (C)... Missing/invalid files are skipped gracefully.
    """
    os.makedirs(OUT_DIR, exist_ok=True)
    items = [(p, c) for p, c in image_paths if p and os.path.exists(p)]
    if not items:
        return None
    n = len(items)
    nrows = math.ceil(n / ncols)

    try:
        font_title = ImageFont.truetype(_FONT_BOLD, 26)
        font_label = ImageFont.truetype(_FONT_BOLD, 20)
        font_caption = ImageFont.truetype(_FONT_REG, 16)
    except Exception:
        font_title = font_label = font_caption = ImageFont.load_default()

    # load + resize each source image to a common cell width, preserving aspect ratio
    cells = []
    max_cell_h = 0
    for path, caption in items:
        img = Image.open(path).convert("RGB")
        w, h = img.size
        new_h = int(cell_w * h / w)
        img = img.resize((cell_w, new_h), Image.LANCZOS)
        cells.append((img, caption))
        max_cell_h = max(max_cell_h, new_h)

    label_h = 32
    caption_h = 26
    cell_total_h = label_h + max_cell_h + caption_h
    title_h = 46
    outer_pad = 18

    panel_w = ncols * cell_w + (ncols + 1) * pad
    panel_h = title_h + nrows * cell_total_h + (nrows + 1) * pad + 2 * outer_pad

    canvas = Image.new("RGB", (panel_w + 2 * outer_pad, panel_h), "white")
    draw = ImageDraw.Draw(canvas)

    draw.rounded_rectangle([6, 6, canvas.width - 6, canvas.height - 6], radius=10,
                            outline=border_color, width=3)
    draw.text((outer_pad + 10, outer_pad + 6), title, font=font_title, fill=label_color)

    for i, (img, caption) in enumerate(cells):
        row, col = divmod(i, ncols)
        x = outer_pad + pad + col * (cell_w + pad)
        cy = title_h + outer_pad + pad + row * (cell_total_h + pad)

        draw.rectangle([x - 4, cy - 4, x + cell_w + 4, cy + cell_total_h + 4],
                        outline=(180, 180, 180), width=1)

        label = f"({CELL_LABELS[i]})"
        draw.text((x, cy + 4), label, font=font_label, fill=label_color)
        canvas.paste(img, (x, cy + label_h))
        if caption:
            draw.text((x, cy + label_h + max_cell_h + 4), caption, font=font_caption, fill=(70, 70, 70))

    path = os.path.join(OUT_DIR, fname)
    canvas.save(path, optimize=True)
    return path
