# Windows DirectML support

Windows dependencies now install `onnxruntime-directml` instead of overlapping
CPU and CUDA ONNX Runtime distributions. `uv sync --locked` installs this setup.
InsightFace's transitive CPU-runtime requirement is excluded on Windows using a
uv override; the DirectML package supplies both GPU and CPU providers.

Use Settings → Inference device → GPU (DirectML), or CLI `--device directml`.
Settings also controls the UI's video-import child process. Automatic selection
prefers CUDA, then a registered DirectML provider, then CPU. Live initialization
performs real inference and falls back to CPU with a warning on GPU failure.

Pose checkpoints are exported locally to fixed-shape FP32 ONNX opset 17 graphs
in `.cache/directml/`, keyed by checkpoint content and input resolution. Live
capture uses 640 pixels; the UI's import model uses 960. The custom predictor
keeps Ultralytics preprocessing, keypoint mapping, NMS, and persistent tracking;
only the pose network executes through DirectML. Tracking/ReID, FaceID, and
MediaPipe remain on CPU. No third-party installed source files are modified.

Live solo sessions use ByteTrack to avoid the additional ReID network. With two
or more players, the live pipeline retains BoT-SORT + ReID. Changing the player
count recreates the tracker and resets temporal tracking state at the lobby
boundary. Offline video ingestion always retains the original appearance and
FaceID pipeline. This optimization does not change the pose model or resolution.

A local 40-frame clip measured median 35.2 ms with ReID versus 22.1 ms with solo
ByteTrack. NCNN Vulkan was also benchmarked in an isolated environment: 83.7 ms
with ByteTrack, slower than DirectML on this RX 580. Vulkan dependencies were
not added to the working application. CPU and GPU already share work: GPU pose
inference, CPU tracking and scoring.

## Low-power solo option

Settings → Pose backend → Fast solo — MediaPipe Lite (CPU) selects
`mediapipe-lite`. This uses model complexity 0 and MediaPipe's built-in temporal
tracking. Solo play does not initialize YOLO. The existing single-person shared
state carries track ID 1 and the standard semantic joints, aspect compensation,
normalization, smoothing and scoring. Switching to multiplayer restores YOLO;
switching back returns to Lite. Imports always retain the accurate YOLO/FaceID
pipeline, so processed songs do not need rebuilding.

This is a CPU alternative for laptops, not a claim that CPU beats a dedicated
GPU. Local Lite inference measured about 15 ms per frame and detected the dancer
in 90/90 benchmark frames; Ryzen 5700U performance remains unverified. Smaller
models trade some accuracy for lower inference cost. On a fresh environment,
MediaPipe downloads `pose_landmark_lite.tflite` on first use.

The predictor extension is pinned to Ultralytics 8.4.140. Dependency auto-install
is disabled so Ultralytics cannot overwrite DirectML with a CPU runtime. Manage
dependencies through uv. Cached models can be rebuilt by removing their specific
cache files while the app is closed.

Validated on Radeon RX 580: GPU-only matrix computation, actual pose network
profiling, CPU/GPU output comparison, persistent video tracking, and a 960-pixel
video import. See the local setup verification files under the parent `.setup/`
directory for measured results. CPU recovery and settings round trips have
regression tests in `tests/test_directml.py`.

DirectML session configuration follows
[ONNX Runtime's requirements](https://onnxruntime.ai/docs/execution-providers/DirectML-ExecutionProvider.html):
sequential execution and memory-pattern optimization disabled.
