# JARVIS PRD Changelog

The following architectural corrections have been applied to `JARVIS_PRD.md` following the pre-implementation architecture review.

### 1. Local AI Runtime
- **Change Made:** Relaxed the prohibition on Ollama. Specified `llama.cpp` / `llama-cpp-python` as the preferred runtime for 8 GB RAM, but allowed Ollama for development/benchmarking provided JARVIS does not depend on it as a mandatory daemon. Enforced a provider abstraction.
- **Reason:** Provides flexibility during development while ensuring the final product remains lightweight and decoupled from heavy background services.
- **Architectural Impact:** BrainRouter must implement a generic `LocalProvider` interface that can hot-swap between Ollama and llama-cpp.
- **Affected Phase:** Phase 15 — Multi-Brain / Offline (and Phase 0 for interface definition).

### 2. Latency Targets
- **Change Made:** Clarified that latency numbers are targets to be benchmarked on actual hardware, not guarantees. Defined specific latency metrics to measure (wake-word, STT, Fast Router, tool execution, TTS, Gemini tokens). Emphasized sub-second targets for local commands.
- **Reason:** Sets realistic expectations and provides concrete metrics for optimization on an Intel i3 processor.
- **Architectural Impact:** Requires integrating timing metrics and telemetry into the core orchestration loop.
- **Affected Phase:** Phase 4 — Fast Command Engine & Phase 20 — Performance.

### 3. Implementation Order
- **Change Made:** Added an explicit dependency order to the implementation phases. Most importantly, forced Fast Command Engine and Windows Tools to be built *before* the Voice Engine and Wake Word.
- **Reason:** Ensures the text-based deterministic pipeline and OS controls are fully functional and testable before adding the complexity of audio streaming and STT/TTS.
- **Architectural Impact:** Shifts the critical path. Core tools and routing must be completely headless and text-driven first.
- **Affected Phase:** Phase 2, 3, 4, 5 (Reordered).

### 4. Internal Event Architecture
- **Change Made:** Added a section explicitly defining the internal event architecture. JARVIS Core must publish normalized states (`IDLE`, `LISTENING`, `THINKING`, `EXECUTING`, `SPEAKING`, `ERROR`, `OFFLINE`).
- **Reason:** Prevents tight coupling between the backend Python logic and the React HUD.
- **Architectural Impact:** Requires an internal pub/sub event bus or state machine in the Orchestrator, which then broadcasts over WebSockets to any connected client.
- **Affected Phase:** Phase 0 (Foundation) & Phase 12 (HUD).

### 5. Hardware Constraints
- **Change Made:** Replaced the automatic prohibition of heavy technologies with a classification system (`REQUIRED`, `OPTIONAL`, `DEFERRED`, `BENCHMARK-DEPENDENT`).
- **Reason:** Prevents prematurely closing doors on capabilities (like 3D) while still enforcing strict benchmarking before they can become mandatory runtime dependencies.
- **Architectural Impact:** Encourages a plugin or lazy-loading architecture for heavy components.
- **Affected Phase:** All Phases.

### 6. Three.js / 3D Visualization
- **Change Made:** Added a note to defer heavy 3D rendering in favor of CSS/Canvas for the initial HUD, while keeping the underlying data architecture independent so Three.js can optionally be added later.
- **Reason:** Protects the i3's integrated GPU from being starved while keeping the futuristic vision alive for optimized future iterations.
- **Architectural Impact:** The Knowledge Base (graph data) must be fully decoupled from the UI rendering layer.
- **Affected Phase:** Phase 13 — Knowledge Galaxy & Phase 12 — HUD.

### 7. Memory System
- **Change Made:** Explicitly specified SQLite with FTS5 for initial memory, and allowed `sqlite-vec` later if benchmarked. Removed the possibility of a mandatory heavyweight vector database.
- **Reason:** Conserves RAM by avoiding Java/Docker-based vector databases (like Milvus or Chroma).
- **Architectural Impact:** Memory retrieval will initially rely on BM25/keyword semantic search rather than true vector embeddings.
- **Affected Phase:** Phase 8 — Memory.

### 8. Security
- **Change Made:** Explicitly banned the exposure of a generic `run_command(command: str)` tool to the LLM.
- **Reason:** Prevents prompt injection attacks from resulting in arbitrary shell execution or destructive OS commands.
- **Architectural Impact:** All OS interactions must be wrapped in strictly typed, narrow-scope Pydantic tools (e.g., `open_application`).
- **Affected Phase:** Phase 5 — Windows Control & Phase 19 — Security Hardening.

### 9. Voice Pipeline
- **Change Made:** Clarified that the `STT → text router → LLM → TTS` pipeline is the primary architecture. Realtime voice APIs are optional optimizations that must not bypass security.
- **Reason:** Ensures that fast local commands can be intercepted locally via text, and that the security architecture remains intact even if a direct audio-to-audio model is used.
- **Architectural Impact:** The Orchestrator must always be in the loop; a realtime voice model cannot act autonomously on the OS.
- **Affected Phase:** Phase 2 — Voice.
