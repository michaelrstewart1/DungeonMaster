# Building an Automated AI Dungeon Master: A Comprehensive Technical Guide

## Executive Summary

Building a self-hosted AI Dungeon Master is absolutely feasible today using a combination of open-source projects and AI APIs. The ecosystem has matured significantly — there are already multiple open-source AI DM projects you can build upon (Tavern, NeverEndingQuest, DungeonGod-AGI), fast local LLM inference engines (Ollama, vLLM), real-time speech I/O (faster-whisper for STT, Coqui XTTS/Piper for TTS), and talking-head avatar systems (SadTalker, Linly-Talker). All of these can be containerized and run on a Proxmox homelab server. The key architectural challenge is orchestrating these components for low latency — the system must pipeline speech recognition → LLM reasoning → text-to-speech → avatar rendering to feel responsive. This report covers every layer of the stack: existing projects to build on, LLM options, voice I/O, game state tracking (including physical board vision), character integration, the animated DM face, and a recommended architecture for your Proxmox deployment.

---

## Table of Contents

1. [Existing AI Dungeon Master Projects](#1-existing-ai-dungeon-master-projects)
2. [System Architecture Overview](#2-system-architecture-overview)
3. [LLM Brain — The AI Behind the DM](#3-llm-brain--the-ai-behind-the-dm)
4. [Voice Input — Speech-to-Text](#4-voice-input--speech-to-text)
5. [Voice Output — Text-to-Speech](#5-voice-output--text-to-speech)
6. [Game State Tracking & Rules Engine](#6-game-state-tracking--rules-engine)
7. [Character Management & Roll20 Integration](#7-character-management--roll20-integration)
8. [Physical Board Tracking with Computer Vision](#8-physical-board-tracking-with-computer-vision)
9. [The Animated DM Face](#9-the-animated-dm-face)
10. [Proxmox Deployment Architecture](#10-proxmox-deployment-architecture)
11. [Latency Optimization Strategies](#11-latency-optimization-strategies)
12. [How Cool Can You Make This?](#12-how-cool-can-you-make-this)
13. [Recommended Implementation Roadmap](#13-recommended-implementation-roadmap)
14. [Key Repositories Summary](#14-key-repositories-summary)
15. [Confidence Assessment](#15-confidence-assessment)
16. [Footnotes](#16-footnotes)

---

## 1. Existing AI Dungeon Master Projects

Several open-source projects have already tackled this problem at varying levels of maturity. Rather than building from scratch, you should evaluate these as starting points.

### Tavern (Recommended Starting Point)

[t11z/tavern](https://github.com/t11z/tavern) is the most polished self-hosted AI DM project available. It is brand new (April 2026) but architecturally sound[^1]:

- **Self-hosted via Docker Compose** — literally `docker compose up` to start[^2]
- **SRD 5.2.1 compatible** rules engine with deterministic dice, combat, spells, and conditions implemented in code (not prompts)[^1]
- **Claude as narrator** — the LLM only handles narrative/NPC behavior; numbers come from the rules engine[^1]
- **Two clients**: Browser-based React web UI and a Discord bot with voice support[^1]
- **Persistent campaigns** via PostgreSQL; SRD data served from MongoDB (5e-database)[^3]
- **Cost-efficient**: Prompt caching, mixed model routing (Haiku for simple responses, Sonnet for narration). A solo session costs ~$0.28, a 4-player 3-hour session ~$0.70[^1]
- **Table mode**: Shared display on laptop, each player joins on their phone via QR code[^1]
- **Tech stack**: Python 3.12+/FastAPI backend, React/Vite frontend, PostgreSQL, MongoDB, Docker[^1]

The architecture cleanly separates the **Rules Engine** (deterministic SRD logic) from the **Narrator** (LLM)[^1]. This is the right pattern — it prevents the LLM from hallucinating rules.

### NeverEndingQuest

[MoonlightByte/NeverEndingQuest](https://github.com/MoonlightByte/NeverEndingQuest) is an AI-powered DM for SRD 5.2.1 campaigns[^4]:

- Version 0.3.5 Alpha — quite active development
- Features an "Advanced Token Compression System" for long play sessions[^4]
- Supports infinite adventure generation tailored to party playstyle
- Python-based, designed for API-driven LLM backends

### GPT Dungeon Master

[SverreNystad/gpt-dungeon-master](https://github.com/SverreNystad/gpt-dungeon-master) has planned features that align well with your goals[^5]:

- Text-to-speech with different voices per character
- Speech-to-text for player input
- Generative art for scene visualization
- Knowledgebase integration for rulebook queries
- Still in active development (v0.0.6)

### DungeonGod-AGI

[benjcooley/dungeongod-agi](https://github.com/benjcooley/dungeongod-agi) is a multi-game AI DM with player memory and rules-based gameplay[^6]. It uses a Docker-based deployment and has fine-tuning infrastructure included.

### AIDND

[Transcenduality/AIDND](https://github.com/Transcenduality/AIDND) is a stateful RPG engine with automated DM logic[^7]:

- Manages character sheets, inventory, and stats via structured JSON
- Dynamic Pygame UI for real-time HP, XP, Gold updates
- Built-in save system and history tracking
- Works with OpenAI-compatible APIs including **Ollama** and **LM Studio** locally[^7]
- Includes `pyttsx3` for text-to-speech already

### Dungeon Master AI Project

[fedefreak92/dungeon-master-ai-project](https://github.com/fedefreak92/dungeon-master-ai-project) is a modular Python backend with[^8]:

- Stack-based finite state machine for game phases
- ASCII map system with tile controller
- Entity factory system for dynamic content
- Clean separation of game logic from UI (ready for AI integration)
- Plans for GPT-powered DM, voice synthesis, and AI-generated scenes

---

## 2. System Architecture Overview

Here's the full architecture for what you're building:

```
┌──────────────────────────────────────────────────────────────────────┐
│                        PLAYER INTERFACES                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐    │
│  │ Browser  │  │ Discord  │  │  Phone   │  │  Physical Table  │    │
│  │   UI     │  │   Bot    │  │  (QR)    │  │   + Camera       │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───────┬──────────┘    │
└───────┼──────────────┼──────────────┼───────────────┼───────────────┘
        │              │              │               │
        ▼              ▼              ▼               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION SERVER (FastAPI)                     │
│                                                                      │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │  WebSocket  │  │   REST API   │  │  Session Manager         │   │
│  │  Handler    │  │   Endpoints  │  │  (Campaign State)        │   │
│  └─────────────┘  └──────────────┘  └──────────────────────────┘   │
└──────┬──────────────┬──────────────┬──────────────┬─────────────────┘
       │              │              │              │
       ▼              ▼              ▼              ▼
┌────────────┐ ┌────────────┐ ┌───────────┐ ┌──────────────┐
│  STT       │ │  LLM       │ │  TTS      │ │  Vision      │
│  Service   │ │  Service   │ │  Service  │ │  Service     │
│ (Whisper)  │ │ (Ollama/   │ │ (Coqui/   │ │ (Board      │
│            │ │  vLLM/API) │ │  Piper)   │ │  Tracking)   │
└────────────┘ └────────────┘ └───────────┘ └──────────────┘
       │              │              │              │
       │              ▼              │              │
       │       ┌────────────┐       │              │
       │       │  Rules     │       │              │
       │       │  Engine    │       │              │
       │       │  (5e SRD)  │       │              │
       │       └────────────┘       │              │
       │              │              ▼              │
       │              │       ┌───────────┐        │
       │              │       │  Avatar   │        │
       │              │       │  Renderer │        │
       │              │       │ (Talking  │        │
       │              │       │   Head)   │        │
       │              │       └───────────┘        │
       │              │              │              │
       ▼              ▼              ▼              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │  PostgreSQL  │  │   MongoDB    │  │  Redis (Cache/Queue)     │  │
│  │  (Campaigns, │  │  (5e SRD    │  │  (Session state,         │  │
│  │   State)     │  │   Data)     │  │   streaming buffers)     │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

Each component runs as a Docker container on your Proxmox server, communicating via internal Docker networking.

---

## 3. LLM Brain — The AI Behind the DM

This is the most critical component. You have three tiers of options:

### Option A: Cloud LLM APIs (Fastest, Easiest)

| Provider | Model | Latency | Cost | Best For |
|----------|-------|---------|------|----------|
| **Anthropic** | Claude 3.5 Sonnet | ~1-2s first token | ~$3/MTok input | Narration, roleplay |
| **Anthropic** | Claude 3.5 Haiku | ~0.5s first token | ~$0.25/MTok input | Quick responses, rulings |
| **OpenAI** | GPT-4o | ~1s first token | ~$2.50/MTok input | General purpose |
| **OpenAI** | GPT-4o-mini | ~0.5s first token | ~$0.15/MTok input | Quick interactions |
| **Google** | Gemini 2.0 Flash | ~0.5s first token | Free tier available | Fast interactions |

**Tavern's approach** of mixing Haiku (for simple responses) and Sonnet (for narration) with prompt caching is the gold standard for cost control[^1]. The system prompt and character sheets are cached, so you only pay for new content each turn.

**For streaming responses**: All major APIs support streaming, which means TTS can begin converting the first sentence while the LLM is still generating the rest. This is essential for low latency.

### Option B: Self-Hosted Local LLMs (Privacy, No Ongoing Cost)

For running on your Proxmox server, you need a GPU-equipped VM. Key options:

**[Ollama](https://github.com/ollama/ollama)** (131K+ stars)[^9]:
- Dead simple to set up: `ollama run llama3` 
- OpenAI-compatible REST API
- Supports 200+ models including Llama 3, Gemma 3, Mistral, Qwen
- Manages model downloading, quantization, GPU allocation automatically
- Perfect for homelab — runs as a single binary or Docker container

**[vLLM](https://github.com/vllm-project/vllm)**[^10]:
- Production-grade LLM serving engine from UC Berkeley
- PagedAttention for efficient memory management
- Continuous batching, speculative decoding, tensor parallelism
- 4x higher throughput than naive serving
- Best for: when you need to serve multiple players simultaneously

**Recommended local models for DM'ing:**

| Model | VRAM Needed | Quality | Speed |
|-------|------------|---------|-------|
| Llama 3.1 70B (Q4) | ~40GB | Excellent | Slow without big GPU |
| Llama 3.1 8B (Q8) | ~10GB | Good | Fast |
| Mistral 7B | ~8GB | Good | Fast |
| Qwen 2.5 32B (Q4) | ~20GB | Very Good | Medium |
| Gemma 3 27B | ~18GB | Very Good | Medium |

**Reality check**: For truly fast, low-latency DM narration, you need either a high-end GPU (RTX 4090 / A6000 with 24-48GB VRAM) for local inference, or use cloud APIs. A smaller GPU (RTX 3060 12GB) can run 7-8B models acceptably but will feel sluggish with larger models.

### Option C: Hybrid (Recommended)

Use **cloud APIs for the primary LLM narration** (streaming for speed) and **Ollama locally for secondary tasks** (NPC dialogue generation, encounter planning, background tasks). This gives you the best latency while keeping costs low.

---

## 4. Voice Input — Speech-to-Text

Players need to talk to the DM. Here are your options:

### faster-whisper (Recommended for Self-Hosting)

[SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) is a reimplementation of OpenAI's Whisper using CTranslate2[^11]:

- **4x faster** than OpenAI Whisper with same accuracy
- **GPU**: 13 minutes of audio transcribed in **17 seconds** (batch mode on RTX 3070 Ti)[^11]
- **CPU**: Handles real-time on modern hardware with the `small` or `base` model
- Supports int8 quantization for lower VRAM usage (2.9GB for large-v2)[^11]
- Python library — easy to integrate into your FastAPI backend

**For real-time conversation**, use the `base` or `small` model with Voice Activity Detection (VAD) to detect when someone stops speaking, then transcribe the chunk. Latency: ~200-500ms per utterance on GPU.

### whisper.cpp

[ggerganov/whisper.cpp](https://github.com/ggerganov/whisper.cpp) is a C/C++ port — even faster for CPU-only deployment. Good if your Proxmox server lacks a GPU.

### OpenAI Whisper API

If you prefer cloud: $0.006/minute, extremely accurate, but adds network latency (~500ms-1s round trip).

### Implementation Pattern

```
Microphone → VAD (detect speech end) → faster-whisper → Text → LLM
                                         ~200ms           ~1-2s
```

Use **Silero VAD** (voice activity detection) to detect when a player finishes speaking, then send the audio chunk to faster-whisper. This avoids transcribing silence and gives natural turn-taking.

---

## 5. Voice Output — Text-to-Speech

The DM needs to speak! You have several excellent options:

### Coqui TTS / XTTS v2 (Best Quality, Self-Hosted)

[coqui-ai/TTS](https://github.com/coqui-ai/TTS) with the XTTS v2 model[^12]:

- **Zero-shot voice cloning** — record a 6-second sample of any voice, and XTTS will speak in that voice
- **16 languages** supported
- **Streaming with <200ms latency**[^12]
- Can create unique voices for each NPC (wizard voice, tavern keeper voice, dragon voice)
- Requires GPU for real-time speed (RTX 3060+ recommended)
- Open source (AGPL-3.0, but Coqui the company is defunct — community maintained)

**This is the most impressive option for a DM.** Imagine the DM switching between a gravelly dwarf voice and an ethereal elf voice.

### Piper TTS (Fastest, Lightest)

[rhasspy/piper](https://github.com/rhasspy/piper) — fast, local neural TTS[^13]:

- **Runs on CPU** — no GPU needed, even works on Raspberry Pi
- **10x faster than real-time** on CPU[^13]
- Multiple voice models available
- Perfect for: quick, lightweight responses where voice quality doesn't need to be stellar
- C++ implementation, very efficient
- Downside: No voice cloning, limited voice variety

### Cloud Options

| Service | Latency | Quality | Cost |
|---------|---------|---------|------|
| **ElevenLabs** | ~200ms streaming | Exceptional | $5-22/mo |
| **OpenAI TTS** | ~300ms | Very Good | $15/1M chars |
| **Azure Neural TTS** | ~200ms | Very Good | $16/1M chars |
| **Google Cloud TTS** | ~200ms | Good | Free tier available |

### Recommended Approach

Use **Coqui XTTS v2** for the DM's main narration voice and important NPC voices (GPU-accelerated). Use **Piper** as a fallback for quick, low-priority utterances. Create a voice profile for each recurring NPC character.

### Streaming TTS Pipeline

Critical for low latency — start speaking the first sentence while the LLM is still generating the rest:

```
LLM streaming → sentence boundary detection → TTS chunk → audio output
     ↓ "The dragon"                                          ↓
     ↓ "breathes fire,"    → TTS("The dragon breathes") → 🔊 playing
     ↓ "scorching the"     → TTS("fire, scorching the") → 🔊 queued
     ↓ "stone walls..."    → TTS("stone walls...")       → 🔊 queued
```

---

## 6. Game State Tracking & Rules Engine

### The Tavern Approach (Recommended)

Tavern's architecture is the gold standard here[^1]:

1. **Rules Engine** (deterministic code): Handles all dice rolls, combat resolution, spell effects, conditions, HP tracking, initiative order, movement distances — everything mechanical
2. **LLM Narrator**: Only receives a **structured state snapshot** (not raw rulebooks) and writes narrative descriptions
3. **PostgreSQL** stores persistent campaign state: character positions, inventory, quest progress, NPC relationships, world state[^3]
4. **MongoDB (5e-database)** stores all SRD reference data: spells, monsters, classes, equipment, races[^14]

This separation is critical — the LLM should **never** be responsible for math or rules. It will hallucinate modifiers, forget conditions, and make arithmetic errors.

### Game State Data Model

The game state should track:

```json
{
  "campaign": {
    "id": "uuid",
    "name": "The Lost Mines",
    "session_number": 12,
    "world_state": {
      "time": "Day 34, Evening",
      "weather": "Stormy",
      "location": "Cragmaw Castle, Room 7"
    }
  },
  "characters": [
    {
      "name": "Thorin",
      "class": "Fighter",
      "level": 5,
      "hp": { "current": 34, "max": 52 },
      "position": { "x": 5, "y": 3 },
      "conditions": ["blessed"],
      "inventory": [...],
      "spell_slots": {...}
    }
  ],
  "combat": {
    "active": true,
    "initiative_order": ["Thorin", "Goblin 1", "Elara", "Goblin 2"],
    "current_turn": "Thorin",
    "round": 3
  },
  "map": {
    "grid": "30x20",
    "terrain": [...],
    "tokens": [...]
  },
  "narrative_summary": "The party has infiltrated Cragmaw Castle..."
}
```

### Map / Battle Board Options

For digital map management, you have several options:

**Option 1: Foundry Virtual Tabletop** ($50 one-time purchase)[^15]
- The gold standard for self-hosted virtual tabletop
- Self-hosted (perfect for Proxmox!) via [foundryvtt-docker](https://github.com/felddy/foundryvtt-docker) (864 stars)[^16]
- Full battle maps, token management, fog of war, dynamic lighting
- Robust API for module development — you can write a module that bridges to your AI DM
- 200+ supported game systems[^15]
- Players interact via browser
- **This solves the "how do we track the map" problem perfectly for digital play**

**Option 2: Custom Web-Based Map**
- Build a simple grid-based map renderer in your React frontend
- Use WebSocket for real-time token updates
- AI DM generates map descriptions and token placement instructions
- Lighter weight than Foundry but less feature-rich

**Option 3: Hybrid Physical + Digital**
- Use a camera for physical board tracking (see Section 8)
- Overlay digital elements on a screen/projector showing the map
- Most complex but coolest for in-person play

---

## 7. Character Management & Roll20 Integration

### Roll20 Integration

Roll20 does **not** have a public API for character data export. However:

- **Roll20 Character Vault** allows exporting characters as JSON — you can parse these
- **D&D Beyond** has better integration options: characters can be exported via browser extensions (like Beyond20)
- **Roll20 macros/sheet workers** can be used to output character data to the chat, which can be scraped

### Better Alternatives for Character Management

**Open5e API** ([open5e.com](https://open5e.com))[^17]:
- Free, open-source REST API for all SRD content
- All monsters, spells, classes, races, equipment from the SRD
- Search API for quick lookups
- Your AI DM can query this in real-time for rule references

**5e-database** ([5e-bits/5e-database](https://github.com/5e-bits/5e-database))[^14]:
- MongoDB-based SRD 5.2.1 dataset
- Docker image ready — Tavern uses this as its SRD data source
- Contains everything: spells, monsters, classes, species, equipment

**Custom Character Sheet System**:
Build a simple character creation flow in your web UI:
1. Player selects race, class, background
2. System rolls/assigns ability scores
3. Calculates derived stats (HP, AC, saving throws, skills)
4. Stores in PostgreSQL
5. AI DM has full structured access to character data — no parsing needed

This is more work but gives you full control and eliminates the Roll20/D&D Beyond dependency.

### Foundry VTT as Character Manager

If you deploy Foundry VTT, it already handles complete D&D 5e character sheets with the dnd5e system. Your AI DM module can read character data directly from the Foundry API.

---

## 8. Physical Board Tracking with Computer Vision

This is the most ambitious feature. You want a camera pointed at your physical game board that feeds images to the AI so it understands token positions.

### Approach 1: Periodic Image Capture + Vision LLM

The simplest approach:

1. Mount a camera above the physical game board (a webcam or IP camera)
2. At the start of each turn, capture a high-res image
3. Send the image to a **Vision LLM** (GPT-4o, Claude 3.5 Sonnet, or Gemini 2.0 Flash — all support image input)
4. Prompt: *"Analyze this top-down photo of a D&D battle map. Identify the positions of all miniatures/tokens on the grid. List each token's grid coordinates and describe any terrain features."*
5. LLM returns structured position data that updates the game state

**Pros**: Simple to implement, leverages existing vision LLMs
**Cons**: ~2-5 seconds per image analysis, costs per image (~$0.01-0.05 per frame), may struggle with complex boards

### Approach 2: Computer Vision Pipeline + LLM

More robust but more complex:

1. **Camera calibration**: Detect the grid using OpenCV (Hough line transform)
2. **Token detection**: Use a YOLO model fine-tuned on miniature recognition, or color-based detection (put colored bases on minis)
3. **Grid mapping**: Map detected token positions to grid coordinates
4. **Change detection**: Only process when tokens have moved (frame differencing)
5. Feed structured position data to the AI DM

```
Camera → OpenCV Grid Detection → Token Detection (YOLO/color) →
    Grid Coordinates → Game State Update → AI DM
```

**Pros**: Much faster (real-time capable), works offline, no per-image cost
**Cons**: Requires training/calibrating for your specific setup, miniatures are hard to classify

### Approach 3: QR Codes / ArUco Markers

Put small ArUco markers (printable QR-like codes) on the bottom or base of each miniature:

1. Camera detects ArUco markers using OpenCV (built-in support)
2. Each marker ID maps to a character/monster
3. Position is calculated precisely from marker geometry
4. Near-zero latency, extremely reliable

**Pros**: Most reliable, fast, no ML needed
**Cons**: Requires marking every miniature

### Recommended Approach

Start with **Approach 1** (periodic image + Vision LLM) because:
- Minimal setup — just mount a camera
- Modern vision LLMs are surprisingly good at analyzing game boards
- You can manually confirm/correct positions if needed
- Upgrade to Approach 2 or 3 later if you want real-time tracking

**Hardware needed**: A USB webcam or ESP32-CAM mounted on a gooseneck or overhead arm. Resolution of 1080p is sufficient.

---

## 9. The Animated DM Face

This is the "cool factor" component. You want a screen displaying an animated face that talks and looks around.

### SadTalker (Portrait + Audio → Talking Video)

[OpenTalker/SadTalker](https://github.com/OpenTalker/SadTalker) — CVPR 2023 paper[^18]:

- Input: A single portrait image + audio file
- Output: Realistic talking head video with lip sync and natural head movement
- Licensed under Apache 2.0[^18]
- Generates both lip movement and expressive head poses
- Can be run via GPU (requires CUDA)
- **Limitation**: Generates video offline — not real-time enough for live conversation without optimization

### Linly-Talker (Complete Digital Avatar System — Recommended)

[Kedreamix/Linly-Talker](https://github.com/Kedreamix/Linly-Talker) (3,242 stars) is a full digital avatar conversational system[^19]:

- **End-to-end pipeline**: Whisper (STT) → LLM → TTS → Talking Head Animation
- Integrates SadTalker, Wav2Lip, and other face animation methods
- Supports multiple LLMs (Linly, Qwen, ChatGPT, etc.)
- **Real-time interaction** mode available
- Microsoft Speech Services and multiple TTS backends supported
- **This is essentially what you're trying to build** — but for a general digital human. You'd customize it for a DM persona.

### Wav2Lip (Real-Time Lip Sync)

For truly real-time lip sync (lower quality but faster):
- Takes a video/image of a face + audio → outputs lip-synced video
- Much faster than SadTalker for real-time use
- Can loop a base animation while syncing lips to audio

### Live2D / VTuber Approach (Alternative)

Instead of photorealistic face generation, consider a **stylized animated avatar**:

1. Create a fantasy DM character illustration
2. Rig it as a Live2D model (or use VRM/VTuber tools)
3. Drive mouth/eye movements from audio in real-time
4. **Advantages**: Much lighter on GPU, no uncanny valley, consistent character, can be any fantasy race
5. Tools: [VTube Studio](https://store.steampowered.com/app/1325860/VTube_Studio/), [Live2D Cubism](https://www.live2d.com/en/), or open-source alternatives

### Recommended Approach

**Phase 1**: Use **Linly-Talker** as a base — it already integrates STT, LLM, TTS, and talking head generation into one system[^19]. Create a DM portrait (a wise wizard, a mysterious figure, whatever fits your campaign) and use it as the base image.

**Phase 2**: Upgrade to a **Live2D avatar** for more consistent, stylized results that are lighter on GPU. The DM could be an animated wizard with expressions that change based on the narrative (angry during villain encounters, jovial at the tavern).

**Phase 3**: Add **head tracking / gaze direction** — the avatar looks at the player who is currently speaking (use microphone directionality or name detection to know who's talking).

### Display Setup

Mount a screen (tablet, old monitor, or even a smart display) facing the players at the table. The DM face is displayed full-screen. When the DM speaks, the face animates with lip sync and natural movement.

---

## 10. Proxmox Deployment Architecture

Your Proxmox server in the basement is ideal for this. Here's how to structure the deployment:

### Hardware Requirements

**Minimum viable setup:**
- CPU: Any modern 8+ core CPU (Ryzen 7 / i7)
- RAM: 32GB minimum (64GB recommended)
- GPU: NVIDIA RTX 3060 12GB (for TTS + STT + face animation)
- Storage: 500GB SSD (models take space)

**Recommended setup for all features:**
- CPU: Ryzen 9 / i9 or Xeon
- RAM: 64-128GB
- GPU: NVIDIA RTX 4090 24GB (or dual RTX 3090s)
  - One GPU for LLM inference (if running local models)
  - One GPU for TTS + STT + face animation
- Storage: 1TB NVMe SSD

### Proxmox VM Layout

```
Proxmox Host
├── VM1: "ai-dm-core" (Ubuntu Server 22.04)
│   ├── Docker Compose
│   │   ├── FastAPI Orchestrator
│   │   ├── PostgreSQL
│   │   ├── MongoDB (5e-database)
│   │   ├── Redis
│   │   └── Nginx (reverse proxy)
│   └── Network: Bridge to LAN
│
├── VM2: "ai-dm-gpu" (Ubuntu Server 22.04 + GPU Passthrough)
│   ├── Docker Compose
│   │   ├── Ollama (local LLM)
│   │   ├── faster-whisper server
│   │   ├── Coqui XTTS server
│   │   └── SadTalker/Linly-Talker server
│   └── GPU: PCIe passthrough of NVIDIA GPU
│
├── VM3: "foundry-vtt" (optional)
│   ├── Foundry VTT Docker
│   └── Serves battle maps to players
│
└── LXC: "support-services"
    ├── Tailscale (remote access)
    └── Monitoring (Grafana/Prometheus)
```

### GPU Passthrough in Proxmox

This is essential. You need to pass your NVIDIA GPU through to the GPU VM:

1. Enable IOMMU in BIOS (VT-d for Intel, AMD-Vi for AMD)
2. Edit `/etc/default/grub`: add `intel_iommu=on` or `amd_iommu=on`
3. Blacklist nouveau driver on the host
4. Add GPU PCIe device to VM2 configuration
5. Install NVIDIA drivers inside VM2
6. Install nvidia-container-toolkit for Docker GPU support

### Docker Compose for GPU Services

```yaml
# docker-compose.gpu.yml
services:
  ollama:
    image: ollama/ollama
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

  whisper:
    build: ./whisper-service
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]
    ports:
      - "8001:8001"

  tts:
    build: ./tts-service
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]
    ports:
      - "8002:8002"

  avatar:
    build: ./avatar-service
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]
    ports:
      - "8003:8003"
```

---

## 11. Latency Optimization Strategies

The biggest challenge: making the AI DM feel responsive. Human DMs respond in 1-3 seconds. Here's how to approach that:

### End-to-End Latency Budget

```
Player speaks: "I attack the goblin with my sword"

STT (faster-whisper):    200-500ms  (GPU, small/base model)
LLM first token:         500-2000ms (streaming API)
TTS first audio chunk:   200-500ms  (streaming, Coqui XTTS)
Avatar first frame:      100-300ms  (pre-rendered idle, lip sync overlay)
─────────────────────────────────────
Total to first sound:    1.0 - 3.3 seconds
```

### Key Optimizations

1. **Stream everything**: LLM outputs tokens → TTS converts sentence by sentence → Audio plays while rest is still generating

2. **Sentence-boundary pipelining**: Don't wait for full LLM response. Detect sentence boundaries (`.`, `!`, `?`) and send each sentence to TTS immediately.

3. **Pre-compute common responses**: Cache TTS audio for common phrases ("Roll for initiative!", "Make a perception check", "You take X damage")

4. **Use fast models for routing**: Use a small/fast model to determine response type first:
   - Simple rule lookup → instant rule engine response
   - Quick acknowledgment → pre-cached audio + brief LLM
   - Complex narration → full LLM streaming pipeline

5. **Keep the avatar in "listening" mode**: While processing, the DM face should look attentive (nod, look at speaker) so it doesn't feel like dead air

6. **Use WebSockets not REST**: For real-time bidirectional communication between all components

7. **GPU memory management**: Keep all models loaded in VRAM. Don't swap models in and out.

8. **Prompt caching**: Anthropic and OpenAI both support caching system prompts. Your SRD rules, world state, and character sheets should be in the cached portion — you only pay latency for the new player input.

---

## 12. How Cool Can You Make This?

Here's the full "dream build" feature list, from most to least practical:

### Tier 1: Core (Build this first)
- ✅ AI DM with voice (STT + LLM + TTS)
- ✅ D&D 5e rules engine with automated dice rolls
- ✅ Web UI for character sheets and text chat
- ✅ Persistent campaign state across sessions
- ✅ Docker deployment on Proxmox

### Tier 2: Enhanced (Very doable)
- 🗣️ Different voices for each NPC (XTTS voice cloning)
- 🗺️ Digital battle maps (Foundry VTT integration or custom)
- 📱 Players join on phones via QR code
- 🎵 Dynamic ambient music/sound effects (AI-selected based on scene)
- 🎲 Physical dice detection via camera (optional — digital dice work fine)

### Tier 3: Impressive (Some engineering effort)
- 👤 Animated DM face on a screen at the table
- 📸 Physical board camera tracking (Vision LLM analyzes board photos)
- 🎨 AI-generated scene art (DALL-E / Stable Diffusion for each new location)
- 📖 Campaign journal auto-generation (summarizes each session)
- 🤖 NPC "memory" — recurring NPCs remember past interactions

### Tier 4: Mind-Blowing (Significant R&D)
- 👀 DM avatar that looks at the current speaker
- 🎭 Emotion-aware DM (detects player excitement/boredom from voice tone, adjusts pacing)
- 🌍 Procedurally generated world that evolves between sessions
- 🎬 Post-session "recap video" with narrated highlights and generated art
- 🧠 Fine-tuned DM model trained on actual play transcripts (Critical Role, etc.)
- 🏰 AR overlay on physical table (phone cameras show digital fog of war on the physical map)
- 🖥️ Multiple DM faces for different NPCs (switch avatar when speaking as different characters)

---

## 13. Recommended Implementation Roadmap

### Phase 1: Foundation
- Deploy **Tavern** on Proxmox via Docker Compose[^1]
- Set up Anthropic API key for Claude-powered narration
- Test web client and Discord bot
- Play a session with text + Claude narration

### Phase 2: Voice I/O
- Deploy **faster-whisper** as a service on your GPU VM[^11]
- Deploy **Coqui XTTS** as a TTS service[^12]
- Build a simple FastAPI gateway that connects: microphone → Whisper → Tavern API → Claude response → XTTS → speaker
- Add streaming pipeline for low latency

### Phase 3: Battle Maps
- Deploy **Foundry VTT** on Proxmox[^16]
- Write a Foundry module that syncs with your AI DM's game state
- Or build a custom web-based map renderer in Tavern's React frontend

### Phase 4: The Face
- Deploy **Linly-Talker** on your GPU VM[^19]
- Create a DM portrait (commission art or use AI image generation)
- Connect TTS audio output to the face animation pipeline
- Display on a tablet or monitor at the game table

### Phase 5: Physical Board Vision
- Mount overhead camera
- Implement periodic board capture
- Send board images to Claude/GPT-4o Vision for analysis
- Feed position data back into game state

### Phase 6: Polish & Cool Factor
- Add per-NPC voice profiles
- Add AI scene art generation
- Add ambient music selection
- Add DM gaze tracking (looks at current speaker)
- Generate session recap documents

---

## 14. Key Repositories Summary

| Repository | Purpose | Stars | Language | Key Feature |
|---|---|---|---|---|
| [t11z/tavern](https://github.com/t11z/tavern) | Self-hosted AI DM (SRD 5e) | New | Python/React | Docker Compose, Claude-powered, rules engine |
| [MoonlightByte/NeverEndingQuest](https://github.com/MoonlightByte/NeverEndingQuest) | AI DM with token compression | 59 | Python | Long session support, SRD 5.2.1 |
| [SverreNystad/gpt-dungeon-master](https://github.com/SverreNystad/gpt-dungeon-master) | GPT-powered DM with voice | 51 | Python | TTS, STT, image gen planned |
| [benjcooley/dungeongod-agi](https://github.com/benjcooley/dungeongod-agi) | Multi-game AI DM | 13 | Python | Player memory, fine-tuning |
| [Transcenduality/AIDND](https://github.com/Transcenduality/AIDND) | Stateful RPG engine | 6 | Python | Pygame UI, Ollama-compatible |
| [fedefreak92/dungeon-master-ai-project](https://github.com/fedefreak92/dungeon-master-ai-project) | Modular RPG backend | 28 | Python | FSM architecture, map system |
| [deckofdmthings/GameMasterAI](https://github.com/deckofdmthings/GameMasterAI) | Web-based AI DM | 29 | Vue | MongoDB, GPT-3.5/4, open source |
| [ollama/ollama](https://github.com/ollama/ollama) | Local LLM server | 131K+ | Go | Easiest local LLM deployment |
| [vllm-project/vllm](https://github.com/vllm-project/vllm) | Production LLM serving | Major | Python | PagedAttention, high throughput |
| [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Fast speech-to-text | Major | Python | 4x faster than OpenAI Whisper |
| [coqui-ai/TTS](https://github.com/coqui-ai/TTS) | Text-to-speech (XTTS) | Major | Python | Voice cloning, 16 languages, streaming |
| [rhasspy/piper](https://github.com/rhasspy/piper) | Fast local TTS | 10.8K | C++ | CPU-only, 10x realtime speed |
| [OpenTalker/SadTalker](https://github.com/OpenTalker/SadTalker) | Talking head from portrait | Major | Python | Single image + audio → video |
| [Kedreamix/Linly-Talker](https://github.com/Kedreamix/Linly-Talker) | Digital avatar system | 3.2K | Python | Full STT→LLM→TTS→Face pipeline |
| [felddy/foundryvtt-docker](https://github.com/felddy/foundryvtt-docker) | Foundry VTT Docker | 864 | Shell | Self-hosted virtual tabletop |
| [5e-bits/5e-database](https://github.com/5e-bits/5e-database) | D&D 5e SRD data | Major | MongoDB | All SRD data, Docker-ready |
| [open5e/open5e-api](https://github.com/open5e/open5e-api) | D&D 5e REST API | Major | Python | Free SRD API |

---

## 15. Confidence Assessment

### High Confidence
- **Tavern** is a solid starting point for a self-hosted AI DM — I verified its architecture, Docker Compose setup, and tech stack directly from source[^1][^2][^3]
- **faster-whisper** benchmarks are from the project's own documentation with specific hardware and model details[^11]
- **Coqui XTTS** streaming latency (<200ms) is documented by the project[^12]
- **Ollama** is the standard for local LLM serving in homelabs — extremely well-documented and widely adopted[^9]
- **Foundry VTT** is the leading self-hosted virtual tabletop; Docker deployment is well-established[^15][^16]
- **GPU passthrough in Proxmox** is a well-documented, commonly-used configuration

### Medium Confidence
- **Physical board tracking with Vision LLMs** — I'm confident current vision models can analyze game board photos, but the accuracy for precise grid-coordinate extraction from miniature photos hasn't been extensively benchmarked in published work. Expect some iteration to get reliable results.
- **Latency budget estimates** — these are based on published benchmarks for individual components but the end-to-end pipelined latency depends heavily on your specific hardware, network configuration, and implementation quality
- **Linly-Talker for real-time DM face** — the project supports real-time mode but achieving truly smooth, low-latency talking head animation synchronized with streaming TTS will require optimization work

### Lower Confidence
- **Roll20 character import** — Roll20's export capabilities are limited and may change. I recommend building custom character management instead.
- **Multiple GPU cost/benefit** — whether you need one or two GPUs depends entirely on which services you run locally vs. cloud. The guidance here is directional.
- **Emotion detection from voice** — listed as a Tier 4 feature because while technically possible (speech emotion recognition models exist), integrating this meaningfully into DM behavior is an open research problem.

---

## 16. Footnotes

[^1]: [t11z/tavern README.md](https://github.com/t11z/tavern) — Architecture overview, features, cost estimates, and tech stack
[^2]: [t11z/tavern docker-compose.yml](https://github.com/t11z/tavern/blob/main/docker-compose.yml) — Full Docker Compose configuration showing PostgreSQL, MongoDB, Discord bot services
[^3]: [t11z/tavern docker-compose.yml](https://github.com/t11z/tavern/blob/main/docker-compose.yml) — PostgreSQL 16 with persistent volumes, 5e-database MongoDB container at tag `v4.6.3-tavern.2`
[^4]: [MoonlightByte/NeverEndingQuest README.md](https://github.com/MoonlightByte/NeverEndingQuest) — Version 0.3.5 Alpha, SRD 5.2.1 compatible, token compression system
[^5]: [SverreNystad/gpt-dungeon-master README.md](https://github.com/SverreNystad/gpt-dungeon-master) — Planned features: TTS, STT, generative art, knowledgebase integration
[^6]: [benjcooley/dungeongod-agi README.md](https://github.com/benjcooley/dungeongod-agi) — Multi-game AI DM with player memory and rules-based gameplay
[^7]: [Transcenduality/AIDND README.md](https://github.com/Transcenduality/AIDND) — Stateful RPG engine, Pygame UI, Ollama/LM Studio compatible
[^8]: [fedefreak92/dungeon-master-ai-project README.md](https://github.com/fedefreak92/dungeon-master-ai-project) — Modular Python backend with FSM architecture, tile-based map system
[^9]: [ollama/ollama](https://github.com/ollama/ollama) — 131K+ stars, OpenAI-compatible REST API, Docker support, 200+ models
[^10]: [vllm-project/vllm](https://github.com/vllm-project/vllm) — Production LLM serving with PagedAttention, continuous batching, speculative decoding
[^11]: [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) — Benchmarks: Large-v2 on RTX 3070 Ti, batch_size=8, int8: 16 seconds for 13 minutes audio, 4500MB VRAM
[^12]: [coqui-ai/TTS](https://github.com/coqui-ai/TTS) — XTTS v2: 16 languages, zero-shot voice cloning, streaming with <200ms latency
[^13]: [rhasspy/piper](https://github.com/rhasspy/piper) — C++ neural TTS, 10.8K stars, runs on CPU including Raspberry Pi
[^14]: [5e-bits/5e-database](https://github.com/5e-bits/5e-database) — MongoDB-based SRD 5.2.1 dataset, Docker image available
[^15]: [foundryvtt.com](https://foundryvtt.com/) — Self-hosted virtual tabletop, 200+ game systems, $50 one-time purchase
[^16]: [felddy/foundryvtt-docker](https://github.com/felddy/foundryvtt-docker) — 864 stars, Docker containerized Foundry VTT deployment
[^17]: [open5e.com](https://open5e.com/) — Free open-source REST API for SRD 5e content, monsters, spells, classes, equipment
[^18]: [OpenTalker/SadTalker](https://github.com/OpenTalker/SadTalker) — CVPR 2023, Apache 2.0 license, single portrait + audio → talking head video
[^19]: [Kedreamix/Linly-Talker](https://github.com/Kedreamix/Linly-Talker) — 3,242 stars, integrates Whisper, LLMs, TTS, and SadTalker into complete digital avatar system
