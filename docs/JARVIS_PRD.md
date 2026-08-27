# J.A.R.V.I.S. — Master Product Requirements Document

**Version:** 1.0  
**Status:** Master specification / source of truth  
**Target:** Windows PC, Intel i3-1215U, 8 GB RAM  
**Development:** Google Antigravity  
**Primary AI:** Gemini  
**Fallback AI:** Small open-source/local models  
**Mandatory cost target:** ₹0

## 1. Vision

Build a real personal AI assistant inspired by cinematic JARVIS: natural voice conversation, wake-word activation, fast PC commands, Windows/browser/file control, screen understanding, web research, persistent memory, a futuristic HUD, a 3D knowledge galaxy, specialized agents, multi-brain support, offline fallback, and eventual Android/iPhone integration.

The product must be functional, not a visual demo with mocked capabilities.

## 2. Core Principles

### Zero mandatory cost
No paid service may be a hard dependency. Gemini is primary where free API access/quota permits. Open-source local models provide fallback capability. Google AI Pro may be used where its included Google/Antigravity/developer benefits apply, but must not be treated as unlimited Gemini API usage.

### Performance first
Simple deterministic commands must bypass the LLM. Streaming and parallel execution should minimize perceived latency. The assistant must not require a five-second cloud round trip for basic commands.

### Modular
AI providers, voice engines, memory, tools, and UI must have replaceable interfaces.

### No fake functionality
A feature is not complete until it actually works and is tested. UI must never pretend an unavailable capability is running.

### Security by design
The LLM must not have unrestricted OS access. Destructive, financial, messaging, installation, security, and other high-risk actions require explicit confirmation.

## 3. Hardware Constraints

Primary machine:
- Intel Core i3-1215U
- 8 GB RAM
- Windows

Assume no dedicated GPU unless later confirmed.

Therefore:
- avoid heavy always-running services
- avoid assuming large local models
- use small quantized local models
- avoid unnecessary Docker/VM infrastructure
- minimize background CPU/RAM use
- benchmark local models before selecting one

Do not automatically prohibit technologies solely because they are theoretically heavy. Instead classify technologies as REQUIRED, OPTIONAL, DEFERRED, or BENCHMARK-DEPENDENT. Any resource-intensive component must be benchmarked before becoming a mandatory runtime dependency.

### Internal Event Architecture

JARVIS Core must publish normalized events/state changes rather than directly coupling backend logic to the HUD.
Define states including:
- IDLE
- LISTENING
- THINKING
- EXECUTING
- SPEAKING
- ERROR
- OFFLINE

The event system should eventually support: HUD, voice system, tools, memory, notifications, and phone clients.
The frontend should receive state/event updates through WebSockets. The core business logic must remain independent of React.

## 4. High-Level Architecture

```text
                         USER
                          |
                    "Jarvis..."
                          |
                          v
                 +----------------+
                 |  Wake Word     |
                 | openWakeWord   |
                 +-------+--------+
                         |
                         v
                 +----------------+
                 | Voice / Audio  |
                 +-------+--------+
                         |
                         v
                 +----------------+
                 | JARVIS CORE    |
                 | Orchestrator   |
                 +-------+--------+
                         |
                  +------+------+
                  |             |
                  v             v
            Fast Router      Brain Router
                  |             |
                  |       +-----+------+
                  |       |            |
                  |       v            v
                  |    Gemini      Local AI
                  |    Primary      Fallback
                  |       |            |
                  +-------+------------+
                          |
                          v
                     TOOL SYSTEM
                          |
       +----------+-------+-------+----------+
       |          |       |       |          |
     Windows   Browser   Files   Vision   Research
                          |
                          v
                       MEMORY
                          |
                          v
                     JARVIS HUD
```

## 5. Technology Direction

### Backend
- Python
- FastAPI
- WebSockets where realtime communication is required
- asyncio for I/O-bound operations

### Frontend
- React
- TypeScript
- Vite
- Three.js for 3D
- lightweight animation system such as Framer Motion

### AI
Primary:
- Gemini API / Gemini realtime voice capabilities where appropriate

Fallback:
- llama.cpp / llama-cpp-python is the preferred lightweight local inference approach for the target 8 GB RAM hardware. Ollama may be used during development or benchmarking if resource usage is acceptable, but JARVIS must not depend on Ollama as a mandatory runtime daemon. The architecture must use a provider abstraction so the local runtime can be replaced without rewriting JARVIS Core.
- small quantized open-source models suitable for 8 GB RAM

### Voice
Potential local components:
- openWakeWord
- faster-whisper
- Piper

Realtime:
- Gemini Live/realtime voice where appropriate and within available quota/access.

The local STT → text router → Gemini/local AI → TTS architecture is the primary architecture. Realtime voice APIs may be evaluated later as an optional optimization, but they must not bypass the JARVIS tool/security architecture.

### Storage
- SQLite initially
- vector database only when justified
- Markdown/plain files
- optional Obsidian compatibility

### Browser
- Playwright

### Windows
- Windows APIs
- controlled subprocess use
- PyAutoGUI only where appropriate
- typed tools instead of unrestricted shell access

## 6. JARVIS Personality

JARVIS should be calm, intelligent, professional, concise, British-butler inspired, occasionally dry/witty, context-aware, and honest about uncertainty.

Use "sir" occasionally, not constantly.

For simple commands, answer briefly. Never claim an action succeeded if it did not.

## 7. Brain Architecture

### BrainRouter

All reasoning must pass through a provider abstraction:

```text
BrainRouter
   |
   +-- GeminiProvider
   |
   +-- LocalProvider
   |
   +-- FutureProvider(s)
```

### Gemini
Use for:
- complex reasoning
- conversation
- vision
- research
- planning
- tool selection
- multimodal tasks

Prefer fast Gemini models for latency-sensitive work.

### Local fallback
Use when Gemini is unavailable, rate-limited, quota-exhausted, offline, or deliberately disabled.

The local model must be selected by actual benchmarks on the target machine.

### Fast command router
Before invoking an LLM, detect deterministic commands such as:
- launch/close applications
- volume/mute
- screenshots
- system status
- lock PC
- open websites
- media controls

## 8. Voice

### Wake word
Target: "Jarvis"

Must run locally where possible, use low CPU, and control false positives.

### Realtime conversation
Preferred:
Microphone → realtime voice model → JARVIS reasoning → streamed audio.

Requirements:
- low latency
- streaming
- interruption/barge-in
- natural turn taking
- accurate state reporting

### Fallback
Audio → local STT → BrainRouter → reasoning → TTS.

Preferred local components:
- faster-whisper
- Piper

## 9. Computer Control

Initial Windows tools:
- launch application
- close application
- list applications
- CPU/RAM/disk/network status
- volume/mute
- screenshot
- lock computer
- open folder
- open URL

Later:
- controlled keyboard/mouse automation
- settings navigation
- multi-step computer tasks

Every tool must have a schema, validation, error handling, permission level, and appropriate audit logging.

## 10. Browser Agent

Use Playwright.

Capabilities:
- navigate
- search
- read pages
- click/fill
- download
- extract structured information
- multi-step workflows

Require confirmation for purchasing, sending/submitting consequential information, destructive cloud actions, etc.

## 11. File Agent

Capabilities:
- search files
- inspect metadata
- read supported documents
- create files
- organize files
- rename/move files
- summarize documents

Destructive actions require confirmation. Never expose unrestricted arbitrary shell execution.

## 12. Vision

Eventually:
- screen capture
- Gemini vision analysis
- explain errors/settings
- controlled visual interaction

Example:
"Jarvis, what am I looking at?"

Vision must be grounded in an actual screen capture and must never fabricate observations.

## 13. Memory

### Short-term
Maintain current conversation context.

### Persistent
Store structured:
- preferences
- facts
- projects
- tasks
- people
- events
- conversation summaries

Initial database: SQLite. Use FTS5 initially. Allow sqlite-vec or another lightweight embedding solution later if benchmarking demonstrates that semantic memory provides enough benefit. Do not make a heavyweight vector database mandatory.

### User control
Support:
- "Remember this..."
- "Forget that..."
- "What do you remember about X?"
- "Show me what you remember about me."

Obsidian is optional; it must not be required.

## 14. Knowledge Base

Support:
- Markdown
- documents
- project folders
- optional Obsidian vault

The knowledge system should later feed the 3D knowledge galaxy.

## 15. Research Agent

Eventually:
1. understand research goal
2. search web
3. gather sources
4. compare information
5. identify conflicts/uncertainty
6. answer
7. optionally save research

Distinguish sourced facts from inference.

## 16. HUD

The HUD is an interface layer, not the assistant itself.

Visual direction:
- dark background
- futuristic cyan/blue accents
- central reactor/core
- audio visualization
- status indicators
- command transcript
- system information
- tool activity
- memory/knowledge visualization

Real states:
- IDLE
- LISTENING
- THINKING
- EXECUTING
- SPEAKING
- ERROR
- OFFLINE

Animations must reflect actual backend state; no fake processing.

## 17. Knowledge Galaxy

Interactive Three.js visualization of:
*(Note: Defer heavy 3D rendering. Use lightweight CSS/Canvas for the initial HUD. Keep the underlying knowledge graph/data architecture independent from its visualization technology. Do not permanently remove the possibility of Three.js in a future optimized visualization phase.)*
- projects
- documents
- memories
- tasks
- concepts
- people
- events

Features:
- zoom/pan
- node selection
- filtering
- search
- fly-to-node animation
- related-node highlighting
- detail panel

## 18. Specialized Agents

Introduce agents only when complexity justifies separation:
- Computer
- Browser
- File
- Research
- Vision
- Email
- Calendar
- Task
- Knowledge

The Orchestrator selects appropriate tools/agents.

## 19. Phone Integration

### Android
Potential companion app with authenticated connection, supported actions, notifications, and status.

### iPhone
Use supported mechanisms such as Shortcuts, APIs, and app integrations. Do not assume unrestricted iOS control.

## 20. Proactive JARVIS

Later:
- morning briefings
- reminders
- deadlines
- system alerts
- completed long-running tasks
- monitored information

Must be opt-in, configurable, transparent, and non-annoying.

## 21. Permission System

### Level 0 — Safe
Automatic:
- read system status
- open application
- search files
- answer questions

### Level 1 — User-impacting
Usually automatic/configurable:
- move files
- close applications
- change settings

### Level 2 — Risky
Explicit confirmation:
- delete files
- send messages/email
- install software
- submit forms
- purchases

### Level 3 — Highly sensitive
Strong confirmation/safeguards:
- financial actions
- security/account changes
- destructive bulk operations

JARVIS must never bypass confirmation because an LLM requested it.

## 22. Security

- secrets in environment variables/secure storage
- never expose API keys to frontend
- .env in .gitignore
- validate tool arguments
- restrict filesystem paths where practical
- restrict executable commands
- no arbitrary shell tool exposed directly to Gemini (Never expose a generic `run_command(command: str)` tool to the LLM)
- audit important tool calls
- confirmation UX
- safe failure behavior
- authentication for phone/remote clients

## 23. Performance

Performance is a first-class requirement. Latency numbers are TARGETS that must be benchmarked on the actual target hardware.

The system must measure at minimum:
- wake-word detection latency
- STT latency
- Fast Router latency
- local tool execution latency
- TTS first-audio latency
- Gemini first-token latency
- Gemini-to-TTS first-speech latency
- total perceived response latency

Simple commands:
- local routing
- no unnecessary cloud call
- measure execution time
- target sub-second to low-single-digit-second response where technically achievable
- Cloud AI should NEVER be required for simple deterministic local commands

Complex commands:
- stream responses
- progressive status
- speak as soon as useful audio is available
- parallelize independent operations
- avoid unnecessary serial API calls

JARVIS must remain usable alongside normal Windows applications.

## 24. Observability

Track:
- wake-word latency
- STT latency
- model latency
- tool latency
- TTS latency
- total response time
- CPU/RAM usage
- provider errors
- quota/rate-limit errors

Provide a developer/debug mode.

## 25. Antigravity Development Rules

Antigravity must:
1. Read this PRD before implementing any phase.
2. Implement only the requested phase.
3. Never silently implement future phases.
4. Never create fake functionality.
5. Preserve completed functionality.
6. Run tests after implementation.
7. Start and validate the application where possible.
8. Fix discovered errors.
9. Report what was implemented.
10. Report what was not implemented.
11. Report test results.
12. Never expose secrets.
13. Prefer lightweight solutions for the target hardware.
14. Avoid heavy dependencies without justification.
15. Do not rewrite working architecture without a documented reason.

## 26. Implementation Phases

**Dependency Order:**
Phase 0 — Foundation
↓
Phase 1 — Text Brain / Gemini
↓
Fast Command Engine
↓
Windows Tools
↓
Voice Engine
↓
Wake Word
↓
Memory
↓
Browser / Research
↓
Local AI Fallback
↓
HUD
↓
Vision
↓
Phone Integration
↓
Advanced Agents / Knowledge Visualization

*Note: Text commands and Windows tools must work BEFORE voice is integrated. Voice should then be layered on top of the already-working text command pipeline.*

### Phase 0 — Foundation
Repository, backend/frontend structure, configuration, logging, provider interfaces, security baseline, testing.

### Phase 1 — Gemini Brain
Gemini provider, BrainRouter, personality, conversation, streaming, basic UI, errors.

### Phase 2 — Voice
Microphone, realtime voice, audio streaming, interruption, voice states, fallback STT/TTS architecture.

### Phase 3 — Wake Word
openWakeWord, "Jarvis" activation, idle/listening states, false-positive tuning.

### Phase 4 — Fast Command Engine
Local command classification, instant Windows commands, Gemini bypass, latency benchmarks.

### Phase 5 — Windows Control
Applications, system status, volume, screenshots, controlled settings, permissions.

### Phase 6 — Browser Agent
Playwright, navigation, search, interaction, downloads, confirmations.

### Phase 7 — File Agent
Search, reading, creation, organization, destructive-action confirmation.

### Phase 8 — Memory
SQLite, persistent facts, preferences, projects, memory commands, deletion.

### Phase 9 — Knowledge Base
Markdown, document ingestion, retrieval, optional Obsidian integration.

### Phase 10 — Vision
Screen capture, Gemini vision, screen explanation, controlled visual interaction.

### Phase 11 — Research Agent
Web research, sources, comparisons, citations, saved research.

### Phase 12 — HUD
Cinematic JARVIS reactor, audio visualization, real state synchronization, command/activity panels.

### Phase 13 — Knowledge Galaxy
Three.js, graph, nodes, relationships, navigation, filtering.

### Phase 14 — Specialized Agents
Computer, browser, research, knowledge, email, calendar, tasks as justified.

### Phase 15 — Multi-Brain / Offline
Local runtime, small open-source model, automatic fallback, offline mode, provider health.

### Phase 16 — Android
Companion app, authentication, supported actions, notifications, status.

### Phase 17 — iPhone
Shortcuts, supported integrations, authentication, limited device actions.

### Phase 18 — Proactive Assistant
Briefings, reminders, monitoring, configurable notifications.

### Phase 19 — Security Hardening
Permission audit, secret handling, tool sandboxing, audit logs, remote-client security.

### Phase 20 — Performance / Release
Latency benchmarks, startup/RAM/CPU optimization, failure testing, packaging, installation, documentation.

## 27. Acceptance Criteria

A phase is complete only when its behavior works and is tested.

Example Phase 4:
"Jarvis, open Chrome."
- Chrome actually opens
- Gemini is not called
- execution latency is measured

Example Phase 2:
- user speaks
- JARVIS receives audio
- JARVIS understands
- JARVIS responds audibly
- interruption works

Example Phase 8:
- "remember X" stores X
- X can be retrieved later
- X can be deleted

Example Phase 10:
- actual screen is captured
- vision model analyzes it
- answer reflects the actual screen
- no fabricated observation

## 28. Final Target Architecture

```text
                           J.A.R.V.I.S.
                                |
                         +------+------+
                         | Orchestrator|
                         +------+------+
                                |
       +------------------------+------------------------+
       |                        |                        |
       v                        v                        v
   Voice System            Brain Router             Memory
       |                        |                        |
       |              +---------+---------+              |
       |              |                   |              |
       |           Gemini              Local AI          |
       |              |                   |              |
       +--------------+-------------------+--------------+
                              |
                         Tool Router
                              |
       +----------+-----------+-----------+-----------+
       |          |           |           |           |
     Windows   Browser      Files       Vision     Research
                              |
                              v
                           JARVIS HUD
                              |
                    +---------+---------+
                    |                   |
                 Reactor           Knowledge
                                    Galaxy
```

## 29. Definition of Done

JARVIS is successful when the user can naturally say "Jarvis" and use it to:
- converse
- control the PC
- use applications/browser
- work with files
- understand the screen
- research information
- remember useful facts
- retrieve personal knowledge
- switch/fallback between AI brains
- continue working when Gemini is unavailable
- interact naturally through voice
- see meaningful real-time activity in the HUD
- explore knowledge visually
- eventually use supported phone functionality

while remaining fast, reliable, secure, modular, free-first, and appropriate for the target hardware.

## 30. Source-of-Truth Rule

This document is the master product specification.

Every future Antigravity implementation prompt should reference `JARVIS_PRD.md`, identify the phase being implemented, list acceptance criteria, and explicitly avoid future phases.

The project must evolve through verified increments rather than one giant generated implementation.
