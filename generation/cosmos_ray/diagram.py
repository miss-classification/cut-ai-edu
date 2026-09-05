"""Generate the architecture diagram as a black and white PNG.

    python -m cosmos_ray.diagram --out assets/architecture.png

Kept in the package rather than drawn by hand, so the picture cannot drift away
from the code it describes.

Deliberately sparse: names only, no subtitles, no grey. Arial if present, else
the closest clean grotesque available on the machine.
"""

from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

W, H = 1056, 462
INK = (0, 0, 0)
WHITE = (255, 255, 255)
STROKE = 3


def _font(size: int, bold: bool = True):
    from PIL import ImageFont

    names = (["Arial Bold.ttf", "arialbd.ttf", "LiberationSans-Bold.ttf", "DejaVuSans-Bold.ttf"]
             if bold else
             ["Arial.ttf", "arial.ttf", "LiberationSans-Regular.ttf", "DejaVuSans.ttf"])
    pool: list[str] = []
    for pat in ("/usr/share/fonts/**/*.ttf", "/home/ray/anaconda3/**/*.ttf",
                "/opt/conda/**/*.ttf"):
        pool += glob.glob(pat, recursive=True)
    for want in names:
        for path in pool:
            if Path(path).name.lower() == want.lower():
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    pass
    return ImageFont.load_default()


def _pill(d, xy, text, font, radius=14):
    d.rounded_rectangle(xy, radius=radius, fill=WHITE, outline=INK, width=STROKE)
    cx = (xy[0] + xy[2]) // 2
    cy = (xy[1] + xy[3]) // 2
    d.text((cx, cy), text, font=font, fill=INK, anchor="mm")


def _chip(d, x, y, size, font, label):
    """A little square with pins, so a GPU reads as hardware."""
    d.rounded_rectangle((x, y, x + size, y + size), radius=7, fill=WHITE,
                        outline=INK, width=STROKE)
    pin, gap = 9, size / 4
    for i in range(1, 4):
        d.line([(x - pin, y + gap * i), (x, y + gap * i)], fill=INK, width=STROKE)
        d.line([(x + size, y + gap * i), (x + size + pin, y + gap * i)], fill=INK, width=STROKE)
    d.text((x + size // 2, y + size // 2), label, font=font, fill=INK, anchor="mm")


def _play(d, x, y, r):
    """A play triangle, meaning a finished video."""
    d.ellipse((x - r, y - r, x + r, y + r), fill=WHITE, outline=INK, width=STROKE)
    k = r * 0.45
    d.polygon([(x - k * 0.7, y - k), (x - k * 0.7, y + k), (x + k, y)], fill=INK)


# A bat silhouette, normalised to x in [-1, 1] and y in [-0.3, 0.3].
# Top edge left wingtip to right wingtip, then the scalloped underside back.
_BAT = [
    # top edge, left wingtip to right wingtip: flat-ish wings, two tall ears
    # close to the centre, which is what makes it read as a bat and not a crown
    (-1.00, 0.06), (-0.62, -0.06), (-0.30, 0.01), (-0.17, -0.40), (-0.08, -0.06),
    (0.00, -0.12), (0.08, -0.06), (0.17, -0.40), (0.30, 0.01), (0.62, -0.06),
    (1.00, 0.06),
    # underside, right to left: deep scallops and a small tail point
    (0.80, 0.30), (0.55, 0.10), (0.30, 0.34), (0.12, 0.13), (0.00, 0.32),
    (-0.12, 0.13), (-0.30, 0.34), (-0.55, 0.10), (-0.80, 0.30),
]


def _bat(d, cx, cy, width, stretch=1.25):
    """Draw a bat, because an actor that lurks and does the work deserves one.

    stretch exaggerates the vertical so the wings and ears stay legible when the
    glyph is only a few dozen pixels wide.
    """
    half = width / 2
    d.polygon([(cx + x * half, cy + y * half * stretch) for x, y in _BAT], fill=INK)


def _arrow(d, x0, y, x1, head=9):
    d.line([(x0, y), (x1 - head, y)], fill=INK, width=STROKE)
    d.polygon([(x1, y), (x1 - head, y - head * 0.66), (x1 - head, y + head * 0.66)], fill=INK)


def build(out: Path) -> Path:
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)

    f_title = _font(34)
    f_lane = _font(19)
    f_hub = _font(22)
    f_chip = _font(15)
    f_foot = _font(20)

    d.text((W // 2, 40), "Cosmos Transfer 2.5 on Ray", font=f_title, fill=INK, anchor="ma")

    # Three concrete lanes, an ellipsis, then the Nth, so the picture says
    # "one per GPU, however many there are" rather than naming a fixed number.
    lanes = [136, 196, 256]
    last = 348
    top, bottom = lanes[0], last
    mid = (top + bottom) // 2

    # sweep file
    _pill(d, (56, mid - 34, 216, mid + 34), "sweep.yaml", f_hub)
    _arrow(d, 222, mid, 268)

    # the driver: reads the sweep, expands the axes, hands tasks to actors
    _pill(d, (272, mid - 40, 452, mid + 40), "Ray driver", f_hub, radius=20)

    # fan out
    d.line([(468, mid), (500, mid)], fill=INK, width=STROKE)
    d.line([(500, top), (500, bottom)], fill=INK, width=STROKE)

    def lane(y, gpu_label):
        d.line([(500, y), (536, y)], fill=INK, width=STROKE)
        _arrow(d, 536, y, 566)
        d.rounded_rectangle((568, y - 24, 748, y + 24), radius=14, fill=WHITE,
                            outline=INK, width=STROKE)
        _bat(d, 614, y, 74)
        d.text((706, y), "actor", font=f_lane, fill=INK, anchor="mm")
        _arrow(d, 754, y, 812)
        _chip(d, 818, y - 25, 50, f_chip, gpu_label)
        _arrow(d, 888, y, 946)
        _play(d, 972, y, 23)

    for i, y in enumerate(lanes):
        lane(y, str(i + 1))

    # vertical ellipsis in each column, standing for the lanes not drawn
    gap_mid = ((lanes[-1] + 24) + (last - 24)) // 2
    for cx in (658, 843, 972):
        for k in (-1, 0, 1):
            r, cy = 3, gap_mid + k * 12
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=INK)

    lane(last, "N")

    d.text((W // 2, 412), "the model loads once per GPU, then stays",
           font=f_foot, fill=INK, anchor="ma")

    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", default="assets/architecture.png")
    a = p.parse_args(argv)
    out = build(Path(a.out))
    print(f"wrote {out}  ({out.stat().st_size / 1e3:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
