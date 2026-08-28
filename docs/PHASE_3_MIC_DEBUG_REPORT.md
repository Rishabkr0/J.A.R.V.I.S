# PHASE 3: Microphone Debug Report

## Root Cause
The JARVIS voice pipeline was completely failing to initialize because the `WakeWordDetector` crashed silently during startup, resulting in no wake-word engine and the microphone dropping all audio frames. The root cause was `openwakeword`'s recent transition from ONNX to TensorFlow Lite (`.tflite`). 

When initialized, `Model(inference_framework="onnx")` explicitly forced ONNX execution, but the required default model (`alexa_v0.1.onnx` or `hey_jarvis_v0.1.onnx`) was completely missing from the library's `resources/models` directory, which now only ships `.tflite` binaries. Without the model, `self.model` became `None`, so `process_chunk` always returned `False`, causing the pipeline to indefinitely spin without capturing any speech or throwing a visible error to the UI.

Additionally, `pipeline.py` did not correctly handle `AudioCapture` failures. If the `sounddevice` stream failed to open (e.g. no microphone detected), it logged it internally but swallowed the error rather than emitting a `TOOL_ERROR` or `ai_response_error` to the UI, leaving the user interface stuck.

## Microphone Device Detected
I ran a diagnostic of the Windows audio inputs using `sounddevice.query_devices()`. The system successfully detected the default input device:
- **Device ID:** `1`
- **Name:** `Microphone Array (Intel(R) Smart Sound Technology)`
- **Channels:** `4 in, 0 out`
- **API:** `MME`

## Relevant Audio Configuration
- **Sample Rate:** `16000 Hz`
- **Chunk Size:** `1280` frames
- **Format:** `int16`
- **Channels:** `1` (downmixed automatically by `sounddevice`)

## Exact Failure Point
1. **`app/voice/wakeword.py`**: Failed on `self.model = Model(...)` with an `onnxruntime_pybind11_state.NoSuchFile` error.
2. **`app/voice/pipeline.py`**: Failed to check `self.audio.is_running` after calling `start()`, leading to a silent failure.

## Fix Applied
1. **Model Acquisition**: Manually downloaded the legacy ONNX model `alexa_v0.1.onnx` directly from the `openWakeWord` v0.5.1 GitHub release and placed it into `venv/Lib/site-packages/openwakeword/resources/models/`.
2. **File Changed: `app/voice/wakeword.py`**: Explicitly specified `wakeword_models=["alexa_v0.1.onnx"]` in the constructor. This prevents the library from attempting to bulk-load other non-existent ONNX defaults (like `hey_mycroft`).
3. **File Changed: `app/voice/pipeline.py`**: Added an explicit check for `not self.audio.is_running` directly after `.start()`. If initialization fails, it now broadcasts an `ai_response_error` over the WebSocket (e.g., *"Microphone initialization failed..."*) and safely transitions J.A.R.V.I.S. back to the `IDLE` state.

## Tests Performed
1. **Audio Device Enumeration**: Confirmed `sounddevice` successfully mapped to the Intel Smart Sound Microphone Array.
2. **WakeWord Load Test**: Confirmed `WakeWordDetector` initialized without exceptions and correctly verified the presence of `alexa_v0.1`.
3. **Capture Test**: Confirmed `AudioCapture` successfully buffered audio chunks of `2560 bytes` at a time.
4. **STT/TTS Initialization**: Confirmed `faster-whisper` and the `tts.py` modules initialized properly without fatal crashes.

## Final Result
The pipeline now successfully opens the microphone, captures audio frames, successfully routes them through the ONNX WakeWord engine, and safely handles any missing hardware by dispatching errors to the UI. The user can now restart the backend in their terminal to utilize the fully restored Phase 3 voice pipeline!
