from argparse import ArgumentParser
from pathlib import Path
import xml.sax.saxutils as saxutils

import qrcode
from PIL import Image, ImageDraw, ImageFont


# ── shared layout constants ────────────────────────────────────────────────────
PADDING      = 4    # top/bottom white gap between QR and frame
SIDE_PADDING = 4    # left/right white gap between QR and frame
FOOTER_H     = 100  # height of the black caption band
FRAME_W      = 14   # black border stroke width
BOX_SIZE     = 10   # pixels / SVG units per QR module


def load_font(size: int):
    # Prefer bold variants for better legibility and 3D printing
    for font_name in ("arialbd.ttf", "Arial Bold.ttf", "segoeuib.ttf", "verdanab.ttf", "calibrib.ttf", "arial.ttf", "segoeui.ttf"):
        try:
            return ImageFont.truetype(font_name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def fit_font(draw: ImageDraw.ImageDraw, text: str, max_width: int, max_height: int, start_size: int = 26):
    for size in range(start_size, 11, -1):
        font = load_font(size)
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        text_width = right - left
        text_height = bottom - top
        if text_width <= max_width and text_height <= max_height:
            return font, text_width, text_height

    fallback_font = load_font(12)
    left, top, right, bottom = draw.textbbox((0, 0), text, font=fallback_font)
    return fallback_font, right - left, bottom - top


# ── PNG export ─────────────────────────────────────────────────────────────────
def create_qr_with_caption(
    url: str,
    caption: str,
    output_path: str = "qr_code_with_frame.png",
) -> str:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=BOX_SIZE,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    qr_image = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    padding      = PADDING
    side_padding = SIDE_PADDING
    footer_height = FOOTER_H
    frame_color      = "black"
    background_color = "white"
    text_color       = "white"
    canvas_width  = qr_image.width  + side_padding * 2
    canvas_height = qr_image.height + padding * 2 + footer_height

    framed_image = Image.new("RGB", (canvas_width, canvas_height), background_color)
    draw = ImageDraw.Draw(framed_image)

    draw.rectangle(
        (0, 0, canvas_width - 1, canvas_height - 1),
        outline=frame_color,
        width=FRAME_W,
        fill=background_color,
    )

    # black footer band — plain rectangle (no rounded corners)
    draw.rectangle(
        (2, qr_image.height + padding, canvas_width - 3, canvas_height - 3),
        fill=frame_color,
    )

    framed_image.paste(qr_image, (side_padding, padding))

    font, text_width, text_height = fit_font(
        draw,
        caption,
        max_width=canvas_width - 16,
        max_height=footer_height - 16,
        start_size=40,
    )
    text_x = (canvas_width - text_width) // 2
    text_y = qr_image.height + padding + ((footer_height - text_height) // 2)
    draw.text((text_x, text_y), caption, fill=text_color, font=font)

    framed_image.save(output_path)
    return output_path


# ── SVG export ─────────────────────────────────────────────────────────────────
def create_qr_svg(
    url: str,
    caption: str,
    output_path: str = "qr_code_with_frame.svg",
) -> str:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=1,   # 1 unit per module; we scale with BOX_SIZE below
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    matrix      = qr.get_matrix()
    n_modules   = len(matrix)
    box         = BOX_SIZE
    qr_px       = n_modules * box        # QR code rendered size in SVG units

    padding       = PADDING
    side_padding  = SIDE_PADDING
    footer_height = FOOTER_H

    canvas_w = qr_px + side_padding * 2
    canvas_h = qr_px + padding * 2 + footer_height
    footer_y = qr_px + padding

    # ── build module path (all dark cells as a single <path>) ─────────────────
    path_cmds = []
    for r, row in enumerate(matrix):
        for c, cell in enumerate(row):
            if cell:
                x = side_padding + c * box
                y = padding      + r * box
                path_cmds.append(f"M{x},{y}h{box}v{box}h-{box}z")
    module_path = "".join(path_cmds)

    # ── font-size: fit caption into the footer band ───────────────────────────
    # Approximate: each character is ~0.6× the font-size wide
    max_font = footer_height - 16
    approx_font = min(max_font, int((canvas_w - 16) / max(len(caption), 1) / 0.6))
    font_size = max(12, min(40, approx_font))

    safe_caption = saxutils.escape(caption)

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     width="{canvas_w}" height="{canvas_h}"
     viewBox="0 0 {canvas_w} {canvas_h}">

  <!-- white background + outer black border -->
  <rect x="0" y="0" width="{canvas_w}" height="{canvas_h}"
        fill="white" stroke="black" stroke-width="{FRAME_W}"/>

  <!-- black footer band -->
  <rect x="2" y="{footer_y}" width="{canvas_w - 4}" height="{canvas_h - footer_y - 2}"
        fill="black"/>

  <!-- QR code modules -->
  <path d="{module_path}" fill="black"/>

  <!-- caption text -->
  <text x="{canvas_w // 2}" y="{footer_y + footer_height // 2}"
        font-family="Arial, Helvetica, sans-serif"
        font-weight="bold"
        font-size="{font_size}"
        fill="white"
        text-anchor="middle"
        dominant-baseline="middle">{safe_caption}</text>

</svg>"""

    Path(output_path).write_text(svg, encoding="utf-8")
    return output_path


# ── CLI ────────────────────────────────────────────────────────────────────────
def build_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Generate a QR code for a URL with a caption frame.")
    parser.add_argument("url",     nargs="?", default="https://example.com",      help="URL to embed in the QR code")
    parser.add_argument("caption", nargs="?", default="Visit website",             help="Text shown in the frame")
    parser.add_argument("output",  nargs="?", default="qr_code_with_frame.png",   help="Output file (.png or .svg)")
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    if Path(args.output).suffix.lower() == ".svg":
        saved_path = create_qr_svg(args.url, args.caption, args.output)
    else:
        saved_path = create_qr_with_caption(args.url, args.caption, args.output)
    print(f"Saved QR code to {saved_path}")
