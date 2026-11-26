"""Build the README previews in the lesson's visual style (dark canvas, bordered panels, monospace labels).

Run from the repository root:  python docs/assets/src/build_previews.py
Requires ffmpeg (4.4 or newer) and the DejaVu Sans Mono font.
"""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MEDIA = ROOT / "interactive" / "media"
OUT = ROOT / "docs" / "assets"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
# Lesson palette (interactive/styles.*.css)
BG, PANEL, LINE, INK, MUTED, AMBER = "0x080b0f", "0x11161c", "0x2a3038", "0xf3f0e9", "0xa6abb3", "0xffb444"
LABEL_H, GAP, MARGIN, FOOT_H, FPS = 26, 10, 14, 30, 10


def tile(i, label, w, h, color, crop=None):
    """Filter chain: input i -> bordered panel with a monospace label strip."""
    c = f"crop={crop}," if crop else ""
    return (f"[{i}:v]fps={FPS},{c}scale={w}:{h}:flags=lanczos,setsar=1,"
            f"pad={w + 2}:{h + LABEL_H + 1}:1:{LABEL_H}:color={PANEL},"
            f"drawbox=x=0:y=0:w=iw:h=ih:color={LINE}:t=1,"
            f"drawtext=fontfile={FONT}:text='{label}':x=10:y=8:fontsize=12:fontcolor={color}[t{i}]")


def build(name, inputs, labels, cols, w, h, duration, footer, color=AMBER, crops=None, max_colors=144):
    n = len(inputs)
    rows = (n + cols - 1) // cols
    tw, th = w + 2, h + LABEL_H + 1
    cw = MARGIN * 2 + cols * tw + (cols - 1) * GAP
    ch = MARGIN * 2 + rows * th + (rows - 1) * GAP + FOOT_H
    args = ["ffmpeg", "-v", "error", "-y"]
    for p in inputs:
        args += ["-i", str(p)]
    parts = [tile(i, labels[i], w, h, color, crops[i] if crops else None) for i in range(n)]
    parts.append(f"color=c={BG}:s={cw}x{ch}:r={FPS}:d={duration}[c0]")
    last = "c0"
    for i in range(n):
        r, c = divmod(i, cols)
        x, y = MARGIN + c * (tw + GAP), MARGIN + r * (th + GAP)
        parts.append(f"[{last}][t{i}]overlay={x}:{y}:shortest=1[c{i + 1}]")
        last = f"c{i + 1}"
    parts.append(f"[{last}]drawtext=fontfile={FONT_REG}:text='{footer}':x={MARGIN}:y=h-{FOOT_H - 6}:fontsize=11:fontcolor={MUTED},"
                 f"split[a][b];[a]palettegen=max_colors={max_colors}:stats_mode=diff[p];"
                 f"[b][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle")
    out = OUT / f"{name}.gif"
    subprocess.run(args + ["-filter_complex", ";".join(parts), "-t", str(duration), "-loop", "0", str(out)], check=True)
    print(out.name, round(out.stat().st_size / 1e6, 2), "MB", f"{cw}x{ch}")


# Weather montage: four generated conditions from the lesson montage (label strips cropped away).
montage = MEDIA / "montage-rain-fog-night-clear.mp4"
quads = ["480:286:0:34", "480:286:480:34", "480:286:0:354", "480:286:480:354"]
build("weather-montage", [montage] * 4, ["RAIN", "FOG", "NIGHT", "CLEAR"], 2, 352, 210, 4.0,
      "COSMOS TRANSFER 2.5  /  EDGE CONTROL  /  SAME SOURCE DRIVE", crops=quads)

# Candidate pool: the eight fog takes, identical settings, different seeds.
takes = [MEDIA / f"directors_cut_take{i:02d}.mp4" for i in range(1, 9)]
build("candidate-pool", takes, [f"TAKE {i:02d}" for i in range(1, 9)], 4, 208, 117, 3.2,
      "FOG CANDIDATE POOL  /  N = 8  /  ONLY THE RANDOM SEED VARIES")

# Fog comparison used for the blind vote: balanced pick versus the intensity-only pick.
build("fog-vote", [MEDIA / "directors_cut_take04.mp4", MEDIA / "directors_cut_take07.mp4"],
      ["TAKE 04", "TAKE 07"], 2, 384, 216, 3.2, "BLIND COMPARISON  /  SAME DRIVE, PROMPT, AND SETTINGS")
