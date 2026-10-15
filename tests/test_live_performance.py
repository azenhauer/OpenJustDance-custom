"""Solo speedup must preserve pose quality and multiplayer appearance matching."""

import pytest


@pytest.mark.parametrize("players, tracker", [(1, "bytetrack-dance"),
    (2, "botsort-reid"), (3, "botsort-reid"), (4, "botsort-reid")])
def test_live_tracker_matches_player_count(monkeypatch, players, tracker):
    import engine.pose_engine as engine
    from apps.desktop.threads import create_live_yolo_backend

    calls = []
    class Backend:
        def health_check(self):
            pass
    def create(name, **options):
        calls.append(options)
        return Backend()
    monkeypatch.setattr(engine, "create_backend", create)
    backend, warning = create_live_yolo_backend("directml", players=players)
    assert backend is not None and warning is None
    assert calls == [dict(model="yolo11n-pose.pt", max_persons=players,
        conf=0.4, iou=0.6, tracker=tracker, device="directml")]
