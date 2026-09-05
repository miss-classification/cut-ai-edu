"""Object detection over generated videos. The second pipeline stage.

Notebook 3 needs a detector scored on every generated variant, so the
degradation curve is detections against severity. That is a different kind of
work from generation: a detector is tens of milliseconds per frame where
diffusion is a hundred seconds per clip, so it wants its own pool at its own
size rather than a share of a GPU that should be generating.

It also runs in a different environment. Generation needs the cosmos venv and
therefore a child process; detection needs only torch, torchvision and a video
decoder, all of which the cluster python already has. So this stage is a plain
Ray actor with nothing underneath it.

The model loads once per actor, the same residency argument as generation.
"""

from __future__ import annotations

import json
from typing import Any

# COCO categories worth reporting for a street scene. Everything else is
# counted but not broken out, to keep manifest rows readable.
STREET_CLASSES = ("person", "bicycle", "car", "motorcycle", "bus", "truck", "traffic light")


class DetectorActor:
    """Holds one loaded detector and scores videos against it."""

    def __init__(
        self,
        model_name: str = "fasterrcnn_resnet50_fpn_v2",
        score_threshold: float = 0.5,
        frame_stride: int = 5,
        device: str = "cuda",
    ) -> None:
        import torch
        import torchvision.models.detection as detection

        self.score_threshold = score_threshold
        self.frame_stride = frame_stride

        builder = getattr(detection, model_name)
        # "DEFAULT" resolves to the current best COCO weights for the model.
        self.model = builder(weights="DEFAULT")
        self.model.eval()

        self.device = device if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)

        weights_enum = getattr(detection, f"{_weights_name(model_name)}", None)
        self.categories = (
            weights_enum.DEFAULT.meta["categories"] if weights_enum else []
        )
        self.videos_scored = 0

    def ready(self) -> dict[str, Any]:
        import socket

        return {
            "host": socket.gethostname(),
            "device": self.device,
            "classes": len(self.categories),
        }

    def _frames(self, video_path: str):
        """Decode every frame_stride-th frame as RGB uint8."""
        import cv2

        capture = cv2.VideoCapture(video_path)
        index = 0
        try:
            while True:
                ok, frame = capture.read()
                if not ok:
                    break
                if index % self.frame_stride == 0:
                    yield cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                index += 1
        finally:
            capture.release()

    def score(self, video_path: str) -> dict[str, Any]:
        """Detections for one video. Never raises; failures come back as a row."""
        import numpy as np
        import torch

        self.videos_scored += 1
        result: dict[str, Any] = {"video_path": video_path, "detector_ok": False}
        try:
            frames = list(self._frames(video_path))
            if not frames:
                result["detector_error"] = "no frames decoded"
                return result

            per_frame_counts: dict[str, list[int]] = {c: [] for c in STREET_CLASSES}
            per_frame_conf: dict[str, list[float]] = {c: [] for c in STREET_CLASSES}
            total_detections = 0

            with torch.no_grad():
                for start in range(0, len(frames), 8):
                    batch = frames[start : start + 8]
                    tensors = [
                        torch.from_numpy(f).permute(2, 0, 1).float().div(255).to(self.device)
                        for f in batch
                    ]
                    for output in self.model(tensors):
                        keep = output["scores"] >= self.score_threshold
                        labels = output["labels"][keep].tolist()
                        scores = output["scores"][keep].tolist()
                        total_detections += len(labels)

                        names = [
                            self.categories[i] if i < len(self.categories) else str(i)
                            for i in labels
                        ]
                        for cls in STREET_CLASSES:
                            hits = [s for n, s in zip(names, scores) if n == cls]
                            per_frame_counts[cls].append(len(hits))
                            per_frame_conf[cls].append(max(hits) if hits else 0.0)

            result.update(
                {
                    "detector_ok": True,
                    "frames_scored": len(frames),
                    "detections_total": total_detections,
                    "detections_per_frame": round(total_detections / len(frames), 3),
                    # Mean count per frame is the quantity that degrades with
                    # severity, and the one Notebook 3 plots.
                    "counts": {
                        c: round(float(np.mean(v)), 3)
                        for c, v in per_frame_counts.items()
                        if any(v)
                    },
                    "confidence": {
                        c: round(float(np.mean(v)), 3)
                        for c, v in per_frame_conf.items()
                        if any(v)
                    },
                }
            )
        except Exception as exc:
            result["detector_error"] = f"{type(exc).__name__}: {exc}"
        return result

    def __call__(self, batch: dict[str, Any]) -> dict[str, Any]:
        """Ray Data stage. Takes rows from generation, adds detections."""
        import numpy as np

        out = []
        for blob in batch["result_json"]:
            row = json.loads(str(blob))
            if row.get("status") == "ok" and row.get("output_path"):
                row["detections"] = self.score(row["output_path"])
            out.append(json.dumps(row))
        return {"result_json": np.array(out, dtype=object)}


def _weights_name(model_name: str) -> str:
    """fasterrcnn_resnet50_fpn_v2 -> FasterRCNN_ResNet50_FPN_V2_Weights."""
    special = {
        "fasterrcnn_resnet50_fpn_v2": "FasterRCNN_ResNet50_FPN_V2_Weights",
        "fasterrcnn_resnet50_fpn": "FasterRCNN_ResNet50_FPN_Weights",
        "retinanet_resnet50_fpn_v2": "RetinaNet_ResNet50_FPN_V2_Weights",
        "ssd300_vgg16": "SSD300_VGG16_Weights",
    }
    return special.get(model_name, "")
