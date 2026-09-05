"""Tile several clips into one labelled mp4.

    python -m cosmos_ray.montage /mnt/user_storage/cosmos-runs/weather_tour
    python -m cosmos_ray.montage <run_dir> --cols 2 --width 480 --out grid.mp4

Comparing variants means watching them together. Four separate players are four
things to start, keep in sync and scrub. One grid is one player.

Encoding uses PyAV with libx264, not cv2. cv2 on this machine can only write
mp4v, which browsers refuse to play, so a cv2 written grid would look correct on
disk and show a black rectangle in a notebook.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LABEL_BAND = 34


def _read(path: Path, width: int, height: int, label: str):
    """Decode one clip, resize, and draw a label band across the top."""
    import cv2
    import numpy as np

    capture = cv2.VideoCapture(str(path))
    frames = []
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        frame = cv2.resize(frame, (width, height - LABEL_BAND), interpolation=cv2.INTER_AREA)
        band = np.full((LABEL_BAND, width, 3), 255, np.uint8)
        cv2.putText(band, label, (10, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (17, 24, 39), 1, cv2.LINE_AA)
        frames.append(np.vstack([band, frame]))
    capture.release()
    return frames


def build(clips: list[tuple[str, Path]], out: Path, cols: int = 2,
          width: int = 480, height: int = 320, fps: int = 16) -> Path:
    """Tile clips into a grid and write one H.264 mp4."""
    import av
    import numpy as np

    decoded = [_read(path, width, height, label) for label, path in clips]
    decoded = [d for d in decoded if d]
    if not decoded:
        raise SystemExit("nothing decoded")

    # Shortest clip sets the length, so no cell freezes or runs black.
    length = min(len(d) for d in decoded)
    rows = (len(decoded) + cols - 1) // cols
    blank = np.full((height, width, 3), 245, np.uint8)

    container = av.open(str(out), "w")
    stream = container.add_stream("libx264", rate=fps)
    stream.width, stream.height = cols * width, rows * height
    stream.pix_fmt = "yuv420p"
    stream.options = {"crf": "23", "preset": "veryfast"}

    for i in range(length):
        cells = [d[i] for d in decoded]
        cells += [blank] * (rows * cols - len(cells))
        grid = np.vstack([np.hstack(cells[r * cols:(r + 1) * cols]) for r in range(rows)])
        # cv2 decodes BGR, libx264 wants RGB.
        frame = av.VideoFrame.from_ndarray(grid[:, :, ::-1].copy(), format="rgb24")
        for packet in stream.encode(frame):
            container.mux(packet)
    for packet in stream.encode():
        container.mux(packet)
    container.close()
    return out


def write_gif(clips: list[tuple[str, Path]], out: Path, cols: int, width: int,
              height: int, stride: int = 4, fps: int = 8) -> Path:
    """Tile clips and write an animated GIF.

    GitHub renders a committed mp4 as a download link, never inline, so a GIF is
    the only way to get motion onto a README page. Frames are subsampled and the
    tiles kept small to hold the file to a few MB.
    """
    import numpy as np
    from PIL import Image

    decoded = [_read(path, width, height, label) for label, path in clips]
    decoded = [d for d in decoded if d]
    if not decoded:
        raise SystemExit("nothing decoded")
    length = min(len(d) for d in decoded)
    rows = (len(decoded) + cols - 1) // cols
    blank = np.full((height, width, 3), 245, np.uint8)

    frames = []
    for i in range(0, length, stride):
        cells = [d[i] for d in decoded]
        cells += [blank] * (rows * cols - len(cells))
        grid = np.vstack([np.hstack(cells[r * cols:(r + 1) * cols]) for r in range(rows)])
        frames.append(Image.fromarray(grid[:, :, ::-1]).convert(
            "P", palette=Image.ADAPTIVE, colors=128))

    out.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(out, save_all=True, append_images=frames[1:], loop=0,
                   duration=int(1000 / fps), optimize=True)
    return out


def pair_clips(run_root: Path, label_key: str | None) -> list[tuple[str, Path]]:
    """Interleave each control video with the output it produced.

    Returns [control, output, control, output, ...] so a two column grid puts the
    edge map on the left and the generated frame on its right.
    """
    manifest = run_root / "manifest.jsonl"
    pairs: list[tuple[str, Path]] = []
    for line in manifest.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("status") != "ok" or not row.get("output_path"):
            continue
        produced = Path(row["output_path"])
        control = produced.with_name(produced.stem + "_control_edge.mp4")
        tags = row.get("tags") or {}
        name = (tags.get(label_key) if label_key else " ".join(tags.values())) or row["name"]
        if control.exists() and produced.exists():
            pairs.append((f"{name}  edge control", control))
            pairs.append((f"{name}  generated", produced))
    return pairs


def from_run(run_root: Path, cols: int, width: int, height: int,
             out: Path | None, label_key: str | None) -> Path:
    """Collect the produced videos of a run, in manifest order."""
    manifest = run_root / "manifest.jsonl"
    clips: list[tuple[str, Path]] = []
    if manifest.exists():
        for line in manifest.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("status") != "ok" or not row.get("output_path"):
                continue
            tags = row.get("tags") or {}
            label = tags.get(label_key) if label_key else " ".join(tags.values())
            clips.append((label or row.get("name", "?"), Path(row["output_path"])))
    else:
        for path in sorted(run_root.rglob("*.mp4")):
            if "control" not in path.name:
                clips.append((path.parent.name, path))

    clips = [(lab, p) for lab, p in clips if p.exists()]
    if not clips:
        raise SystemExit(f"no produced videos under {run_root}")
    target = out or run_root / "montage.mp4"
    print(f"tiling {len(clips)} clip(s): {', '.join(lab for lab, _ in clips)}")
    return build(clips, target, cols=cols, width=width, height=height)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run_root", help="directory containing manifest.jsonl")
    parser.add_argument("--cols", type=int, default=2)
    parser.add_argument("--width", type=int, default=480, help="per cell width")
    parser.add_argument("--height", type=int, default=320, help="per cell height")
    parser.add_argument("--out", default=None)
    parser.add_argument("--label", default=None,
                        help="tag to use as the cell label, default is all tags")
    parser.add_argument("--pairs", action="store_true",
                        help="put each edge control on the left and its output on the right")
    parser.add_argument("--gif", default=None, help="also write an animated GIF here")
    parser.add_argument("--gif-width", type=int, default=300, help="per cell width in the GIF")
    parser.add_argument("--gif-stride", type=int, default=4, help="keep every Nth frame")
    args = parser.parse_args(argv)

    root = Path(args.run_root)
    if args.pairs:
        clips = pair_clips(root, args.label)
        if not clips:
            raise SystemExit(f"no control and output pairs under {root}")
        cols = 2
        print(f"pairing {len(clips) // 2} control and output clip(s)")
        out = build(clips, Path(args.out) if args.out else root / "pairs.mp4",
                    cols=cols, width=args.width, height=args.height)
    else:
        clips = None
        cols = args.cols
        out = from_run(root, cols, args.width, args.height,
                       Path(args.out) if args.out else None, args.label)
    print(f"wrote {out}  ({out.stat().st_size / 1e6:.1f} MB)")

    if args.gif:
        if clips is None:
            clips = pair_clips(root, args.label) if args.pairs else None
        if clips is None:
            manifest_clips = []
            for line in (root / "manifest.jsonl").read_text().splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                if row.get("status") == "ok" and row.get("output_path"):
                    tags = row.get("tags") or {}
                    lab = (tags.get(args.label) if args.label else " ".join(tags.values()))
                    manifest_clips.append((lab or row["name"], Path(row["output_path"])))
            clips = manifest_clips
        gif = write_gif(clips, Path(args.gif), cols, args.gif_width,
                        int(args.gif_width * args.height / args.width),
                        stride=args.gif_stride)
        print(f"wrote {gif}  ({gif.stat().st_size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())


def hero_gif(top: tuple[str, Path], left: tuple[str, Path], right: tuple[str, Path],
             out: Path, width: int = 380, height: int = 250,
             stride: int = 5, fps: int = 7) -> Path:
    """Original on top, control on the left, generated on the right.

    Three panels of equal size on a two row canvas, the top one centred. Reads as
    "this went in, this is what conditioned it, this came out".
    """
    import numpy as np
    from PIL import Image

    cells = [_read(p, width, height, lab) for lab, p in (top, left, right)]
    if any(not c for c in cells):
        raise SystemExit("one of the clips did not decode")
    length = min(len(c) for c in cells)
    pad = np.full((height, width // 2, 3), 255, np.uint8)

    frames = []
    for i in range(0, length, stride):
        row_top = np.hstack([pad, cells[0][i], pad])
        row_bottom = np.hstack([cells[1][i], cells[2][i]])
        grid = np.vstack([row_top, row_bottom])
        frames.append(Image.fromarray(grid[:, :, ::-1]).convert(
            "P", palette=Image.ADAPTIVE, colors=128))

    out.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(out, save_all=True, append_images=frames[1:], loop=0,
                   duration=int(1000 / fps), optimize=True)
    return out
