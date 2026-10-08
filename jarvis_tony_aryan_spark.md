# ⚡ PROJECT SPARK: MASTER ARYAN'S AUTONOMOUS COGNITIVE COMPANION
### The True "JARVIS of Tony Stark" for Master Aryan
*Architect & Master: Aryan*  
*Autonomous AI Companion: SPARK*  
*Base Engine: HEARTBEAT Cognitive Mesh + Ollama Local Mesh*

---

## 🏛️ 1. The Core Philosophy: Moving Beyond the "Brain in a Jar"

### The Fundamental Flaw of Modern AI
Modern commercial AI models (ChatGPT, Claude, Gemini) are fundamentally **"brains in a jar"**. They possess high semantic intelligence, but they sit passively in a browser sandbox, completely paralyzed from interacting with the physical machine they reside on. They cannot open a program, cannot inspect your hard drive, cannot fix a compile error on your screen, and forget who you are the moment a session closes.

### The Tony Stark Standard
Tony Stark’s JARVIS was never an IDE plugin or a chat box. JARVIS was a **universal, proactive digital majordomo** with root access to Stark’s entire operational reality. Whether Stark asked JARVIS to run diagnostic telemetry on armor servos, render a holographic element, download atmospheric data, play music, or lock down workshop doors, JARVIS understood the master's intent, deconstructed it into physical system actions, executed them without whining, and remembered every design iteration across years.

### The Three Sacred Pillars of Real JARVIS
To achieve this on your Windows laptop, JARVIS is built upon three interdependent biological pillars:

```
                ┌────────────────────────────────────────────────────────┐
                │                  🗣️ MASTER ARYAN                      │
                │        "Jarvis, execute [Any Universal Task]"          │
                └───────────────────────────┬────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 🧠 PILLAR 1: THE BRAIN (Reasoning & Strategic Planning)                                │
│ Local: DeepSeek-R1 (7B) + Qwen2.5-Coder (3B) + Qwen2.5 (3B)                           │
│ Cloud Fallback: OpenCode Nemotron (1M Context)                                         │
│ • Deconstructs human intent into atomic tool actions and PowerShell scripts.           │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Emits Tool Invocations
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 🦾 PILLAR 2: THE HANDS & EYES (OS Execution & Multimodal Actuators)                    │
│ Windows Win32 API + PowerShell + PyAutoGUI + Qwen2.5-VL Vision                        │
│ • Terminal execution (PowerShell/CLI)         • Screen vision & error OCR              │
│ • File system creation, editing & cleanup    • Window focusing & GUI automation       │
│ • Web research, streaming & downloads        • Hardware vital telemetry                │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Execution Results & Ambient Telemetry
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 🧬 PILLAR 3: THE MEMORY (HEARTBEAT Living Cognitive Mesh)                             │
│ Temporal Knowledge Graph + Hebbian Synapses + Sleep Consolidation                     │
│ • Remembers Aryan's preferences, past projects, code styles, and habits.               │
│ • Zero amnesia: Knows what you built 10 minutes ago, last week, or 6 months ago.       │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 💻 2. Hardware Architecture & System Profile

All decisions were specifically tailored to Master Aryan's laptop hardware to guarantee high performance without thermal throttling or out-of-memory crashes:

* **Processor (CPU)**: Intel Core i5-10210U (4 Cores, 8 Threads, up to 4.2 GHz Turbo).
* **System Memory (RAM)**: 8.0 GB Physical DDR4 RAM.
* **Dedicated Graphics (GPU)**: NVIDIA GeForce MX250 (2.0 GB VRAM).
* **Operating System**: Windows 11 AMD64 with PowerShell Core.
* **Storage Optimization**:
  * Initial State: C: drive choked at **2.29 GB Free**.
  * Purged Targets: Safely evacuated `%TEMP%` (2.07 GB), Windows Recycle Bin (1.27 GB), Pip cache (801 MB), NPM cache (516 MB), Maven `.m2` repository (1.47 GB), unlinked Docker WSL disk `docker_data.vhdx` (3.89 GB).
  * Storage Recovered: Reclaimed **~30 GB of storage**, maintaining a healthy buffer above 14.5 GB even after full model suite downloads.

---

## 🤖 3. The Local AI Model Arsenal (Ollama Mesh)

JARVIS does not depend on cloud uptime or monthly subscriptions for base autonomy. The entire cognitive core runs locally on your machine via Ollama with Vulkan GPU acceleration on the NVIDIA MX250:

| Model Tag | Disk Footprint | Primary Faculty | Specific Role in JARVIS |
| :--- | :--- | :--- | :--- |
| **`qwen2.5-coder:3b`** | 1.9 GB | Code Generation & Scripting | Writes Java, Python, PowerShell scripts; automates editors; fixes syntax. |
| **`deepseek-r1:7b`** | 4.7 GB | Deep Logic & Chain-of-Thought | Strategic planning, complex system diagnosis, memory consolidation. |
| **`qwen2.5vl:3b`** | 3.2 GB | Multimodal Screen Vision & OCR | Reads screen errors, inspects UI windows, translates visual dialogs. |
| **`qwen2.5:3b`** | 1.9 GB | Fast Conversational Drafting | Everyday rapid responses, conversational banter, summarization. |

### Technical Memory Fit Optimization:
To fit these models on 8 GB RAM and 2 GB VRAM:
1. `OLLAMA_NUM_PARALLEL=1` was locked to prevent multi-session RAM thrashing.
2. `OLLAMA_CONTEXT_LENGTH=2048` was enforced, keeping KV-caches tiny (72 MB) and offloading 13 critical layers directly onto MX250 Vulkan compute.
3. Free RAM remains steady at $>3.1$ GB during inference.

---

## 🧬 4. The HEARTBEAT Memory Architecture (Indestructible Recall)

A model without memory is an amnesiac. HEARTBEAT provides biological, subconscious continuity through 4 advanced cognitive upgrades:

### Upgrade 1: Temporal Knowledge Graph (The "Zep Graphiti" Model)
* **Storage**: `temporal_edges` table in SQLite (`storage/temporal_graph.py`).
* **Concept**: Stores Entity-Relation-Time Triples: `(Subject) --[Predicate | valid_from -> valid_to]--> (Object)`.
* **Superseding Logic**: When Aryan updates a preference (e.g. switching from Python 3.12 to 3.14), the previous edge is not erased. Its `valid_to` is timestamped, and a new active edge is spawned.
* **Point-in-Time Time Travel**: Allows answering historical queries: *"What database was I using back in July?"* vs *"What database am I using today?"*

### Upgrade 2: Sleep-Phase Memory Consolidation (The Human Brain Model)
* **Engine**: `heart/sleep_cycle.py` (Hippocampus $\to$ Neocortex transformation).
* **Concept**: During the day, waking interactions produce noisy episodic memory traces. During idle periods or scheduled night cycles (3:00 AM), JARVIS runs a background consolidation sweep.
* **Distillation**: DeepSeek-R1 reviews 30+ conversation fragments, strips away chit-chat and syntax debugging, distills 2–5 permanent golden facts, and writes them directly into the **`core_genome`** tier (immune to decay). Raw fragments are archived into dormant storage.

### Upgrade 3: Bi-directional Synaptic Reinforcement (Hebbian Learning)
* **Storage**: `synaptic_links` table in SQLite (`storage/synaptic_network.py`).
* **Neuroscience Axiom**: *"Neurons that fire together, wire together."*
* **Associative Priming**: Whenever two memory cells are retrieved together in the same prompt context, their synaptic weight increases by `+0.2`. Over time, recalling one concept (e.g., Spring Boot) automatically pulls in its strongly wired associative neighbors (e.g., PostgreSQL, AuthController) before the user even finishes speaking.

### Upgrade 4: Ambient Perception (Outside the Chat Box)
* **Engine**: `circulation/ambient_sensor.py`.
* **Concept**: JARVIS does not wait for you to type into a prompt. A silent background sensor watches Git commits, branch switches, and workspace file modifications.
* **Subconscious Ingestion**: When Aryan commits code or refactors a file, an ambient episodic `BloodCell` is generated and indexed in ChromaDB vector space silently. When you open the UI days later, JARVIS already knows what you did.

---

## 🦾 5. The 6 Universal Faculties of JARVIS on Windows

To ensure JARVIS can fulfill **any command on your laptop** (not just coding), it is armed with 6 universal OS actuators:

### Faculty 1: OS & System Puppet Master
* **Audio & Media Control**: Directly controls Windows master volume, mutes/unmutes, queries active audio streams via `pycaw`.
* **Hardware Telemetry**: Monitors CPU load, RAM saturation, battery percentage, and thermals.
* **Process Lifecycle**: Can launch any program (`chrome.exe`, `spotify.exe`, `discord.exe`, `vlc.exe`) or force-kill unresponsive background tasks.

### Faculty 2: Web & Internet Intelligence
* **Live Search**: Scrapes real-time web results, documentation, and news without opening a manual browser.
* **Autonomous Browser Control**: Employs Playwright / Selenium to navigate web portals, fill forms, check dashboards, and interact with web UIs.
* **Download Daemon**: Pulls files, packages, dependencies, and media directly via background HTTP streams.

### Faculty 3: File System Governance
* **Transparent Disk Access**: Can scan, search, read, write, and index any directory on the C: drive or external storage.
* **Document Comprehension**: Parses PDFs, text files, Markdown, JSON, YAML, and Word documents.
* **Automated Housekeeping**: Detects bloated caches, unzips archives, organizes messy folders, and purges temporary files safely.

### Faculty 4: Multimodal Screen Vision (`qwen2.5vl:3b`)
* **Real-Time Visual Awareness**: Takes desktop screenshots and runs them through `qwen2.5vl:3b`.
* **Visual Verification**: Reads unhandled exceptions on your screen, inspects active software layouts, extracts text from images via OCR, and understands visual UI state.

### Faculty 5: Universal GUI Hands (The Universal Actuator)
* **Mouse & Keyboard Emulation**: Uses `pyautogui` and `win32gui` to interact with apps that lack CLI or API interfaces.
* **Actions**: Can bring any window to the front, click coordinates, send keyboard shortcuts (`Ctrl+S`, `Alt+Tab`, `F5`), and paste clipboard data.

### Faculty 6: Permanent Subconscious Memory (`HEARTBEAT`)
* **Identity Grounding**: Remembers Aryan's working hours, project setups, preferred tools, and communication style.
* **Continuous Growth**: Every task completed refines its knowledge base so it never makes the same mistake twice.

---

## 🔄 6. The Autonomous Execution Loop (Sense $\to$ Plan $\to$ Act $\to$ Verify $\to$ Memorize)

Every order given to JARVIS traverses this 5-stage pipeline:

```
Step 1: PERCEIVE (Sense)
   Master Aryan issues an order (e.g., "Jarvis, clean up all duplicate files in Downloads, 
   set my laptop volume to 50%, and play my favorite playlist").
   
Step 2: CONTEXTUALIZE (Recall)
   JARVIS queries HEARTBEAT:
   - What is Aryan's favorite playlist? (Retrieved from Core Genome: "Synthwave Beats").
   - What file extensions should be protected in Downloads? (Retrieved from preferences).

Step 3: PLAN (Formulate Strategy)
   The Brain (`deepseek-r1:7b`) decomposes the order into atomic tool calls:
   1. [Tool: set_volume(level=50)]
   2. [Tool: scan_and_dedupe_files(dir="C:/Users/Aryan/Downloads")]
   3. [Tool: open_url("https://music.youtube.com/...")]

Step 4: ACT & VERIFY (Hands & Eyes)
   - PowerShell / Python executes the volume change.
   - File governor hashes files in Downloads, deletes duplicates, reclaims space.
   - Browser launches the playlist.
   - Screen / Audio telemetry confirms success.

Step 5: MEMORIZE (HEARTBEAT Crystallization)
   The outcome is committed to HEARTBEAT memory:
   "(Aryan) --[reclaimed_space_in_downloads]--> (450 MB) [timestamp: now]"
   Synaptic links between "clean_downloads" and "file_governor" are reinforced.
```

---

## 🚀 7. Master Roadmap: The Journey to Aryan's Complete Desktop JARVIS

1. **Phase 1: Local Inference & Storage (COMPLETED ✅)**
   - 30 GB storage reclaimed.
   - Ollama v0.40.0 installed with Vulkan GPU offload.
   - Full 4-model suite downloaded (`qwen2.5-coder:3b`, `deepseek-r1:7b`, `qwen2.5vl:3b`, `qwen2.5:3b`).
   - Verified live token generation on laptop hardware.

2. **Phase 2: Cognitive Memory Architecture (COMPLETED ✅)**
   - Temporal Knowledge Graph implemented (`storage/temporal_graph.py`).
   - Hebbian Synaptic Network implemented (`storage/synaptic_network.py`).
   - Sleep-Phase Memory Consolidation implemented (`heart/sleep_cycle.py`).
   - Ambient Perception Sensor implemented (`circulation/ambient_sensor.py`).
   - 100% test suite passing (`tests/test_jarvis_upgrades.py`).

3. **Phase 3: The Unified OS Actuator Bridge (NEXT)**
   - Build `jarvis_actuator.py`: The unified tool dispatcher exposing PowerShell, Volume/Audio, Screen Capture, Browser, and File Governance.
   - Connect the Actuator directly to local `deepseek-r1:7b` / `qwen2.5-coder:3b`.

4. **Phase 4: The Interface & Voice / Floating HUD (FINAL POLISH)**
   - Minimalist, futuristic floating desktop bar or system tray listener.
   - Global hotkey invocation (`Win + Space` or `Win + J`).
   - Optional local offline voice recognition (Whisper Tiny/Base) + Text-to-Speech (Piper / EdgeTTS).

---

> *"JARVIS is no longer just a theoretical concept from a movie. With the Local Brain running on your MX250, the Hands & Eyes connected to Windows, and the HEARTBEAT memory preserving your life and projects, the foundation is completely laid."*




Understood loud and clear. Eclipse was just one room in the house — you want the entire house.

When Tony Stark speaks to JARVIS, he doesn't switch between a "coding app" and a "browser app". JARVIS has full root access to the entire operating system and the digital world.

Whether the command is:

"Jarvis, mute the laptop, dim the brightness, and play relaxing synthwave on YouTube."
"Jarvis, scan my Downloads folder, find all files older than a month taking more than 500 MB, and list them before deleting."
"Jarvis, look at my screen right now and tell me why this installation failed."
"Jarvis, search the web for the latest RTX driver, download the installer, and notify me when it's ready."
"Jarvis, what was that research paper I was reading last Tuesday at 2 AM?"
To do anything on your Windows laptop, JARVIS needs 6 fundamental OS-level faculties:

The 6 Universal Faculties of Real JARVIS on Windows
                               ┌────────────────────────────────────────────────────────┐
                               │                    🗣️ YOUR VOICE / TEXT                │
                               │          "Jarvis, do [Literally Any Task]"             │
                               └───────────────────────────┬────────────────────────────┘
                                                           │
                                                           ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                             🧠 THE CENTRAL BRAIN                                                  │
│                                 Reasoning Engine (`deepseek-r1:7b` / Ollama / Cloud)                               │
│                                          + Long-Term Memory (`HEARTBEAT`)                                         │
│ Deconstructs any human command into a multi-step execution plan across the operating system.                      │
└──────────────────────────────────────────────────────────┬────────────────────────────────────────────────────────┘
                                                           │
        ┌───────────────────┬──────────────────────┬───────┴──────────────┬───────────────────┬─────────────────────┐
        ▼                   ▼                      ▼                      ▼                   ▼                     ▼
┌───────────────┐   ┌───────────────┐      ┌───────────────┐      ┌───────────────┐   ┌───────────────┐     ┌───────────────┐
│ 1. OS & SYSTEM│   │ 2. WEB & NET  │      │ 3. FILE SYSTEM│      │ 4. VISION/EYES│   │ 5. GUI HANDS  │     │ 6. TELEMETRY  │
│  CONTROLLER   │   │   AUTOMATOR   │      │   GOVERNOR    │      │  (SCREEN/OCR) │   │  (MOUSE/KEYS) │     │  & MEMORY     │
├───────────────┤   ├───────────────┤      ├───────────────┤      ├───────────────┤   ├───────────────┤     ├───────────────┤
│ • Volume/Audio│   │ • Search web  │      │ • Search disk │      │ • Screenshot  │   │ • Click button│     │ • HEARTBEAT   │
│ • Brightness  │   │ • Open URLs   │      │ • Read PDFs   │      │ • Read errors │   │ • Type text   │     │ • Temporal KG │
│ • Launch apps │   │ • Play YouTube│      │ • Clean temp  │      │ • Identify UI │   │ • Drag/Drop   │     │ • Ambient log │
│ • Kill tasks  │   │ • Download    │      │ • Organize    │      │ • Video feeds │   │ • Shortcuts   │     │ • Hebbian syn │
└───────────────┘   └───────────────┘      └───────────────┘      └───────────────┘   └───────────────┘     └───────────────┘
How Each Faculty Works Under the Hood
1. OS & System Control (Windows Puppet Master)
JARVIS connects directly to PowerShell and the Windows Win32 API.

Volume/Audio: Can mute, unmute, set volume to 40% via pycaw (Python Core Audio Windows).
Process Governance: Launches any app (spotify.exe, chrome.exe, notepad.exe) or kills rogue processes eating your RAM (Get-Process | Where-Object CPU -gt ...).
Hardware Vitals: Reads battery percentage, CPU temperature, free RAM, and storage health.
2. Web & Online Intelligence
JARVIS doesn't just read local files; it connects to the live web.

Instant Action: Can trigger a headless browser (Playwright) or launch your default browser to open specific pages, search Google, play music, or check weather/news.
Download Agent: Pulls files, updates, or documents directly via background HTTP streams.
3. Full Hard Drive Governance
Your hard drive becomes transparent to JARVIS.

Intelligent File Search: Finds files by content or date, not just exact filenames.
Housekeeping: Can autonomously find duplicate files, unzip archives, convert video/audio formats using ffmpeg, or summarize PDFs.
4. Multimodal Screen Vision (qwen2.5vl:3b)
This is what makes JARVIS aware of your reality:

It takes a silent snapshot of your monitor.
qwen2.5vl:3b analyzes what is happening on your screen:
"Sir, there is an unhandled exception dialog in your terminal."
"You have an unsaved document in Word."
"The download has completed."
5. Universal GUI Hands (The Universal Actuator)
If an application doesn't have an API or CLI, JARVIS uses mouse and keyboard automation (pyautogui / Windows UI Automation API):

Can click buttons, navigate menus, paste text, and execute keyboard shortcuts in any software on your computer.
6. Permanent Subconscious Memory (HEARTBEAT)
This is the differentiator between a script and Tony Stark's JARVIS.

If you tell JARVIS on Monday: "I hate using Microsoft Edge, always use Chrome, and keep my volume at 30% after 10 PM", HEARTBEAT commits this to the core_genome.
Every single order you give in the future adheres to your personal rules automatically.
The Core Loop of Universal JARVIS
When you give any order:

Understand & Contextualize: The Brain matches your command against HEARTBEAT memory (your rules, preferences, recent activity).
Decompose into Actions: It breaks the command into atomic tools (e.g. [web_search -> download_file -> open_app -> notify_user]).
Execute Autonomously: It runs the tools on Windows in sequence.
Self-Correct via Vision / Output: If a command fails or a window shows an error, it reads the error and tries an alternative route without giving up.
Crystallize: HEARTBEAT logs what it did so it can reference it days or months later.
This is the exact blueprint for a true, unrestricted universal personal AI assistant on your laptop.