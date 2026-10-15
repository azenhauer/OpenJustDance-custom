"""AMD device selection, failure recovery and persisted user choices."""

import pytest

from engine.pose_engine.backends.yolo_pose import pick_device


def test_auto_selects_directml_without_cuda(monkeypatch):
    monkeypatch.setattr("torch.cuda.is_available", lambda: False)
    monkeypatch.setattr("engine.pose_engine.backends.directml.directml_available", lambda: True)
    assert pick_device("auto") == "directml"
    assert pick_device("cpu") == "cpu"


def test_directml_setting_roundtrip(monkeypatch, tmp_path):
    from apps.desktop.settings import Settings

    monkeypatch.setenv("APPDATA", str(tmp_path))
    Settings(device="directml").save()
    assert Settings.load().device == "directml"


def test_cpu_provider_cannot_be_reported_as_directml(monkeypatch):
    import onnxruntime as ort
    from engine.pose_engine.backends import directml

    monkeypatch.setattr(directml, "directml_available", lambda: True)
    class CpuSession:
        def disable_fallback(self):
            pass
        def get_providers(self):
            return ["CPUExecutionProvider"]
    monkeypatch.setattr(ort, "InferenceSession", lambda *a, **kw: CpuSession())
    with pytest.raises(RuntimeError, match="refusing to report CPU"):
        directml.create_session("unused.onnx")


@pytest.mark.parametrize("failure", ["creation", "inference"])
def test_directml_failure_recovers_to_cpu(monkeypatch, failure):
    import engine.pose_engine as engine
    from apps.desktop.threads import create_live_yolo_backend

    class Backend:
        def __init__(self, device):
            self.device = device
        def health_check(self):
            if self.device == "directml":
                raise RuntimeError("GPU failure")
        def close(self):
            pass
    def create(name, **kwargs):
        device = kwargs["device"]
        if failure == "creation" and device == "directml":
            raise RuntimeError("GPU failure")
        return Backend(device)
    monkeypatch.setattr(engine, "create_backend", create)
    backend, warning = create_live_yolo_backend("directml")
    assert backend.device == "cpu"
    assert "CPU" in warning


def test_directml_backend_registration_is_local():
    from ultralytics.nn.autobackend import AutoBackend
    from ultralytics.nn.backends.onnx import ONNXBackend
    from engine.pose_engine.backends.directml import DirectMLAutoBackend, DirectMLONNXBackend

    assert AutoBackend._BACKEND_MAP["onnx"] is ONNXBackend
    assert DirectMLAutoBackend._BACKEND_MAP["onnx"] is DirectMLONNXBackend
