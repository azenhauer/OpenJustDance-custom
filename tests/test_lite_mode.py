"""Lite mode must avoid YOLO for solo while preserving multiplayer support."""

from types import SimpleNamespace
import pytest


def test_lite_requests_small_model(monkeypatch):
    from engine.pose_engine.backends.mediapipe import MediaPipeBackend, MediaPipeLiteBackend
    calls = []
    monkeypatch.setattr(MediaPipeBackend, "__init__", lambda self, **opts: calls.append(opts))
    MediaPipeLiteBackend()
    assert calls == [{"model_complexity": 0}]


@pytest.mark.parametrize("players", [1, 2, 3, 4])
def test_lite_only_bypasses_yolo_for_solo(monkeypatch, players):
    import apps.desktop.threads as pipeline
    calls = []
    backend = object()
    def create(device, players):
        calls.append((device, players))
        return backend, None
    monkeypatch.setattr(pipeline, "create_live_yolo_backend", create)
    result = pipeline.create_live_optional_yolo(
        SimpleNamespace(backend="mediapipe-lite", device="directml"), players)
    if players == 1:
        assert result == (None, None)
        assert calls == []
    else:
        assert result == (backend, None)
        assert calls == [("directml", players)]


def test_lite_settings_roundtrip(monkeypatch, tmp_path):
    from apps.desktop.settings import Settings
    monkeypatch.setenv("APPDATA", str(tmp_path))
    Settings(backend="mediapipe-lite").save()
    assert Settings.load().backend == "mediapipe-lite"
