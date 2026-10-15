"""DirectML pose inference with Ultralytics preprocessing and persistent tracking.

Torch tensors, NMS and tracking stay on CPU; the ONNX pose network runs on
the DirectX 12 GPU. No global ONNX Runtime or Ultralytics patches are used.
The extension API is pinned to Ultralytics 8.4.140 in pyproject.toml.
"""

from pathlib import Path

import torch
from ultralytics.models.yolo.pose.predict import PosePredictor
from ultralytics.nn.autobackend import AutoBackend
from ultralytics.nn.backends.onnx import ONNXBackend


def directml_available() -> bool:
    try:
        import onnxruntime as ort

        return "DmlExecutionProvider" in ort.get_available_providers()
    except (ImportError, OSError):
        return False


def create_session(model, *, profiling=False):
    import onnxruntime as ort

    if not directml_available():
        raise RuntimeError("DirectML is unavailable. Install the Windows dependencies with uv sync.")
    options = ort.SessionOptions()
    options.enable_mem_pattern = False
    options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    options.enable_profiling = profiling
    if profiling:
        options.profile_file_prefix = str(Path(model).parent / "directml-profile")
    session = ort.InferenceSession(
        str(model), sess_options=options,
        providers=[("DmlExecutionProvider", {"device_id": 0}), "CPUExecutionProvider"],
    )
    session.disable_fallback()
    if session.get_providers()[0] != "DmlExecutionProvider":
        raise RuntimeError("DirectML GPU initialization failed; refusing to report CPU inference as GPU.")
    return session


class DirectMLONNXBackend(ONNXBackend):
    def load_model(self, weight):
        self.apply_metadata(self.read_metadata(weight))
        self.session = create_session(weight)
        self.output_names = [item.name for item in self.session.get_outputs()]
        self.dynamic = False
        self.fp16 = False
        self.use_io_binding = False


class DirectMLAutoBackend(AutoBackend):
    _BACKEND_MAP = {**AutoBackend._BACKEND_MAP, "onnx": DirectMLONNXBackend}


class DirectMLPosePredictor(PosePredictor):
    def setup_model(self, model, verbose=True):
        # CPU here describes Torch preprocessing, not the ONNX execution provider.
        self.model = DirectMLAutoBackend(model=model, device=torch.device("cpu"), fp16=False)
        self.device = torch.device("cpu")
        self.args.imgsz = self.model.imgsz
        self.model.eval()


def export_model(model, size=640) -> Path:
    """Cache a fixed-shape, FP32, opset-17 graph for DirectML."""
    import hashlib
    import shutil
    import tempfile

    source = Path(model.ckpt_path).resolve()
    digest = hashlib.sha256(source.read_bytes()).hexdigest()[:16]
    cache = Path(__file__).resolve().parents[3] / ".cache" / "directml"
    cache.mkdir(parents=True, exist_ok=True)
    target = cache / f"{source.stem}-{digest}-{size}-op17.onnx"
    if target.is_file():
        return target
    # Export in a private temporary folder so concurrent imports cannot clobber
    # one another or overwrite a user-supplied ONNX model beside the checkpoint.
    from ultralytics import YOLO

    with tempfile.TemporaryDirectory(dir=cache) as work:
        checkpoint = Path(work) / source.name
        shutil.copy2(source, checkpoint)
        output = YOLO(checkpoint).export(
            format="onnx", imgsz=size, opset=17, dynamic=False, simplify=False,
            device="cpu", batch=1, nms=False,
        )
        Path(output).replace(target)
    return target
