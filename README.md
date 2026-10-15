# OpenJustDance custom edition

Customized Windows build of [OpenJustDance](https://github.com/diegoperea20/OpenJustDance),
with AMD DirectML support, faster solo tracking, an optional MediaPipe Lite mode,
and completed playable song imports.

## Install on another Windows PC

Install [Git LFS](https://git-lfs.com/) and [uv](https://docs.astral.sh/uv/getting-started/installation/), then:

```powershell
git lfs install
git clone https://github.com/azenhauer/OpenJustDance-custom.git
cd OpenJustDance-custom
git lfs pull
uv sync --locked
uv run --locked openjustdance
```

After installation, double-click `Play.cmd` to launch. The Python environment is
created on the new PC; copying an existing `.venv` between computers will not work reliably.
Use a Git LFS clone so the videos contain actual media rather than pointer files.

## Gameplay modes

- **Standard:** select `auto` under Settings → Pose backend. Choose DirectML for AMD graphics.
  Solo play uses ByteTrack; multiplayer retains appearance matching.
- **Low-power solo:** select **Fast solo — MediaPipe Lite (CPU)** under Settings → Pose backend.
  Intended as an alternative for laptops such as Ryzen 7 5700U. Accuracy can be lower
  during difficult poses or occlusion. Selecting multiple players restores YOLO.

The Lite model and YOLO weights download on first use when needed. This repository
does not contain the local Python environment, model caches, personal settings, or credentials.

## Included processed songs

- **OMG (bundled demo) — NewJeans:** 36 seconds, ready to play.
- **All the Stars — Just Dance 2021 Unlimited:** approximately 4 minutes 30 seconds,
  ready to play, including its generated pose-overlay preview.

Each song folder includes `song.json`, `song.mp4`, `song.mp3`, and `cover.png`.
Pose sidecars and available overlay previews are also included. `songs/catalog.json`
records file sizes and SHA-256 checksums. An incomplete duplicate import was excluded.
Completed imports do not need to be processed again on the laptop.

## Validation and performance

The customized source passed 140 tests; 5 fixture-dependent tests were skipped.
The Lite pipeline was checked with prerecorded camera input, stable player ID,
and all 13 scoring joints. MediaPipe Lite measured about 15 ms per frame on the
desktop CPU. The Ryzen 7 5700U itself has not been benchmarked; these timings
exclude webcam capture and UI rendering.

See [DirectML and Lite mode notes](docs/DIRECTML.md) for implementation details,
and [upstream documentation](README_UPSTREAM.md) for the original project guide.

## Attribution

Original OpenJustDance code: Diego Ivan Perea Montealegre, MIT license; see `LICENSE`.
This is a customized snapshot, not the upstream repository. Included music and video
assets are separate from the software license and retain their respective rights.
