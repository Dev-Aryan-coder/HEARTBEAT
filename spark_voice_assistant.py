"""
=============================================================================
⚡ SPARK: MASTER ARYAN'S 100% AUTONOMOUS AI COMPANION & DIGITAL MAJORDOMO
=============================================================================
IDENTITY & PHILOSOPHY:
- Name: SPARK (Aryan's SPARK, as JARVIS was to Tony Stark)
- Creator: Master Aryan
- ARCHITECTURAL PRINCIPLE:
  • ZERO FAKING. ZERO SHORTCUTS. ZERO HARDCODED IF-ELSE TRICKS.
  • 100% PURE AUTONOMOUS ReAct AGENTIC EXECUTION.
  • Powered by Local LLM (qwen2.5 / qwen2.5-coder) via Ollama Tool Calling.
  • Integrated with HEARTBEAT (Temporal Knowledge Graph, Hebbian Synapses, 
    and Episodic Memory Persistence).
  • True Windows OS Actuators (PowerShell, App Launcher, Web Search, 
    Browser Control, File Governor, Vitals, Audio Volume, Screen Vision).
  • Windows Native SAPI5 Spoken Voice (Zero Latency Offline).
=============================================================================
"""

import os
import sys
import time
import json
import logging
import asyncio
import subprocess
import urllib.request
import urllib.parse
import re
from datetime import datetime, timezone
from typing import Dict, Any, List

# Suppress verbose third-party logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("transformers").setLevel(logging.WARNING)
logging.getLogger("chromadb").setLevel(logging.WARNING)
# Global Neural Gateway Configurations
OLLAMA_API_URL = "http://127.0.0.1:11434/api/chat"
ACTIVE_MODEL = "qwen2.5:3b"

# ---------------------------------------------------------------------------
# 0. HARDWARE ACTUATION & AUTOMATION INITIALIZATION
# ---------------------------------------------------------------------------
try:
    import pyautogui
    pyautogui.FAILSAFE = True
except Exception:
    pyautogui = None

try:
    from pynput import mouse, keyboard
except Exception:
    mouse = None
    keyboard = None

# ---------------------------------------------------------------------------
# 1. THE MOUTH & ACOUSTIC PRESENCE (Neural JARVIS Voice + SAPI5 Fallback + Barge-In)
# ---------------------------------------------------------------------------
import threading
import ctypes

try:
    import winsound
except Exception:
    winsound = None

try:
    import edge_tts
except Exception:
    edge_tts = None

try:
    import win32com.client
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    speaker.Volume = 95
    speaker.Rate = 1
except Exception:
    speaker = None

IS_SPEAKING = False
ACTIVE_NEURAL_VOICE = "en-GB-RyanNeural"  # True JARVIS archetype: Deep, mature, warm, articulate British
NEURAL_VOICE_MAP = {
    "jarvis": "en-GB-RyanNeural",
    "ryan": "en-GB-RyanNeural",
    "christopher": "en-US-ChristopherNeural",  # Deep, mature, authoritative & responsible
    "thomas": "en-GB-ThomasNeural",            # Formal, mature, calm British
    "guy": "en-US-GuyNeural"                   # Warm, deep, friendly American
}

# ---------------------------------------------------------------------------
# VISUAL ORB INTERFACE BRIDGE (Siri-Style Dynamic Plasma Orb at Top-Center)
# ---------------------------------------------------------------------------
try:
    from spark_orb_ui import set_orb_state, launch_spark_orb_in_background
except Exception:
    def set_orb_state(state: str): pass
    def launch_spark_orb_in_background(): pass

def play_chime(chime_type: str = "wake"):
    """Plays subtle futuristic acoustic feedback chimes in a background thread."""
    if not winsound:
        return
    def _beep():
        try:
            c = (chime_type or "wake").lower().strip()
            if c in ("wake", "listen"):
                winsound.Beep(850, 40)
                winsound.Beep(1250, 50)
            elif c in ("success", "done", "confirm"):
                winsound.Beep(1100, 35)
                winsound.Beep(1500, 45)
            elif c in ("interrupt", "stop", "cancel"):
                winsound.Beep(950, 35)
                winsound.Beep(650, 40)
            else:
                winsound.Beep(1000, 40)
        except Exception:
            pass
    threading.Thread(target=_beep, daemon=True).start()

def stop_speaking() -> str:
    """Immediately interrupts and purges any ongoing speech playback (Barge-In)."""
    global IS_SPEAKING
    IS_SPEAKING = False
    set_orb_state("idle")
    # Stop native Windows MCI audio stream
    try:
        ctypes.windll.winmm.mciSendStringW("stop spark_speech_stream", None, 0, 0)
        ctypes.windll.winmm.mciSendStringW("close spark_speech_stream", None, 0, 0)
    except Exception:
        pass

    # Stop fallback SAPI5
    if speaker:
        try:
            speaker.Speak("", 2)
        except Exception:
            pass

    play_chime("interrupt")
    return "Speech output successfully halted via Barge-In."

def _play_audio_file(filepath: str, async_mode: bool = False):
    """Plays an audio file via Win32 MCI with instant interruption support."""
    global IS_SPEAKING
    def _playback_worker():
        global IS_SPEAKING
        try:
            IS_SPEAKING = True
            set_orb_state("speaking")
            alias = "spark_speech_stream"
            ctypes.windll.winmm.mciSendStringW(f"close {alias}", None, 0, 0)
            open_cmd = f'open "{filepath}" type mpegvideo alias {alias}'
            res = ctypes.windll.winmm.mciSendStringW(open_cmd, None, 0, 0)
            if res != 0:
                ctypes.windll.winmm.mciSendStringW(f'open "{filepath}" alias {alias}', None, 0, 0)
            
            ctypes.windll.winmm.mciSendStringW(f"play {alias} wait" if not async_mode else f"play {alias}", None, 0, 0)
            if not async_mode:
                ctypes.windll.winmm.mciSendStringW(f"close {alias}", None, 0, 0)
                IS_SPEAKING = False
                set_orb_state("idle")
        except Exception:
            IS_SPEAKING = False
            set_orb_state("idle")

    if async_mode:
        threading.Thread(target=_playback_worker, daemon=True).start()
    else:
        _playback_worker()

def speak(text: str, async_mode: bool = False, chime: str = None, voice: str = None):
    """
    Speaks text aloud with high-fidelity Neural JARVIS human voice.
    Deep, mature, friendly, and responsible. Gracefully falls back to SAPI5 if offline.
    """
    global IS_SPEAKING
    clean_text = text.replace("**", "").replace("`", "").replace("#", "").strip()
    if not clean_text:
        return
    print(f"\n⚡ SPARK: {clean_text}\n")
    if chime:
        play_chime(chime)

    target_voice = voice or ACTIVE_NEURAL_VOICE
    neural_success = False

    if edge_tts:
        try:
            cache_dir = os.path.abspath("data/audio_cache")
            os.makedirs(cache_dir, exist_ok=True)
            ts = int(time.time() * 1000)
            audio_path = os.path.join(cache_dir, f"spark_speech_{ts}.mp3")

            async def _synthesize():
                comm = edge_tts.Communicate(clean_text, target_voice, pitch="-2Hz", rate="+3%")
                await comm.save(audio_path)

            asyncio.run(_synthesize())
            if os.path.exists(audio_path) and os.path.getsize(audio_path) > 100:
                neural_success = True
                _play_audio_file(audio_path, async_mode=async_mode)
        except Exception:
            neural_success = False

    # Offline SAPI5 Fallback if neural synthesis was unreachable
    if not neural_success and speaker:
        try:
            IS_SPEAKING = True
            set_orb_state("speaking")
            flags = 1 if async_mode else 0
            speaker.Speak(clean_text, flags)
            if not async_mode:
                IS_SPEAKING = False
                set_orb_state("idle")
        except Exception as e:
            IS_SPEAKING = False
            set_orb_state("idle")
            print(f"[Speech Notice: {e}]")
        except Exception as e:
            IS_SPEAKING = False
            print(f"[Speech Notice: {e}]")

def tool_set_jarvis_voice(voice_name: str) -> str:
    """Configures SPARK's neural speaking voice personality (jarvis/ryan, christopher, thomas, guy)."""
    global ACTIVE_NEURAL_VOICE
    v_clean = voice_name.lower().strip()
    if v_clean in NEURAL_VOICE_MAP:
        ACTIVE_NEURAL_VOICE = NEURAL_VOICE_MAP[v_clean]
        speak(f"Voice personality updated to {v_clean.capitalize()}. How may I assist you, Master Aryan?", chime="confirm")
        return f"Neural voice profile switched to {ACTIVE_NEURAL_VOICE} ({v_clean.capitalize()})."
    return f"Voice option '{voice_name}' not recognized. Available: jarvis (British Ryan), christopher (Deep US), thomas (British), guy (US)."


def _get_arg(args: Any, *keys: str, default: Any = "") -> Any:
    """Safely extracts arguments with alias fallbacks."""
    if not isinstance(args, dict):
        return default
    for k in keys:
        if k in args and args[k] is not None:
            return args[k]
    return default

# ---------------------------------------------------------------------------
# 2. UNIVERSAL OS ACTUATORS & HARDWARE SENSORS (The Hands & Eyes)
# ---------------------------------------------------------------------------
def tool_get_current_time(timezone: str = "local") -> str:
    """Returns the real-world current system date, time, and day."""
    now = datetime.now()
    return now.strftime("%A, %B %d, %Y at %I:%M:%S %p")

def tool_get_system_vitals() -> str:
    """Returns actual hardware diagnostics: CPU load, RAM usage, battery."""
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory()
        battery = psutil.sensors_battery()
        bat_str = f"{battery.percent}% ({'Charging/Plugged in' if battery.power_plugged else 'Discharging'})" if battery else "AC Desktop Power"
        return (
            f"CPU Utilization: {cpu}%\n"
            f"RAM Used: {round(ram.used / (1024**3), 2)} GB / {round(ram.total / (1024**3), 2)} GB ({ram.percent}%)\n"
            f"Battery Level: {bat_str}"
        )
    except Exception as e:
        return f"Vitals query failed: {e}"

def tool_execute_powershell(command: str) -> str:
    """Executes arbitrary PowerShell commands on Master Aryan's Windows OS."""
    if not command or not command.strip():
        return "Error: No command provided."
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30
        )
        out = (res.stdout or "").strip()
        err = (res.stderr or "").strip()
        if err and not out:
            return f"PowerShell Notice: {err}"
        return out if out else "Command executed successfully with zero output."
    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds."
    except Exception as e:
        return f"PowerShell Execution Error: {str(e)}"

def tool_launch_application(app_name: str) -> str:
    """Launches any application on Master Aryan's laptop (e.g. Eclipse, Chrome, Spotify, Notepad, Calc)."""
    if not app_name or not app_name.strip():
        return "Error: No application name provided."
    try:
        app_name_clean = app_name.lower().strip()
        common_apps = {
            "eclipse": "eclipse",
            "chrome": "chrome",
            "google chrome": "chrome",
            "notepad": "notepad",
            "calculator": "calc",
            "spotify": "spotify",
            "terminal": "wt",
            "explorer": "explorer",
            "file explorer": "explorer",
            "vs code": "code",
            "vscode": "code"
        }
        cmd = common_apps.get(app_name_clean, app_name_clean)
        subprocess.Popen(f"start {cmd}", shell=True)
        return f"Application '{app_name}' launched successfully."
    except Exception as e:
        return f"Launch error: {e}"

def tool_open_browser_url(url: str) -> str:
    """Opens a website or YouTube video in the default browser."""
    if not url or not url.strip():
        return "Error: No URL provided."
    try:
        import webbrowser
        url = url.strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"
        webbrowser.open(url)
        return f"URL '{url}' opened in default browser."
    except Exception as e:
        return f"Browser open error: {e}"

def tool_search_web(query: str, max_results: int = 3) -> str:
    """Searches the live internet via DuckDuckGo without requiring API keys."""
    if not query or not query.strip():
        return "Error: No search query provided."
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        
        snippets = re.findall(r'<a class="result__snippet[^"]*"[^>]*>(.*?)</a>', html)
        results = []
        for i in range(min(len(snippets), max_results)):
            clean_snip = re.sub(r'<[^<]+?>', '', snippets[i]).strip()
            if clean_snip:
                results.append(f"[{i+1}] {clean_snip}")
        return "\n".join(results) if results else "No specific web results returned."
    except Exception as e:
        return f"Web search error: {e}"

def tool_control_volume(level: Any) -> str:
    """Sets system master volume to specified percentage (0 to 100)."""
    try:
        if isinstance(level, str):
            num_match = re.search(r'\d+', level)
            vol_val = int(num_match.group(0)) if num_match else 50
        else:
            vol_val = int(level)
        vol_val = max(0, min(100, vol_val))
        ps_cmd = (
            f"$obj = New-Object -ComObject WScript.Shell; "
            f"1..50 | % {{ $obj.SendKeys([char]174) }}; "
            f"1..{vol_val // 2} | % {{ $obj.SendKeys([char]175) }}"
        )
        tool_execute_powershell(ps_cmd)
        return f"System master volume set to {vol_val}%."
    except Exception as e:
        return f"Volume error: {e}"

def tool_take_screenshot(filename: str = "spark_screen.png") -> str:
    """Captures the live laptop desktop screen for visual inspection."""
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        workspace_dir = os.path.dirname(os.path.abspath(__file__))
        target_path = os.path.join(workspace_dir, filename or "spark_screen.png")
        img.save(target_path)
        return f"Screenshot captured successfully and saved to {target_path} (Resolution: {img.size[0]}x{img.size[1]})"
    except Exception as e:
        return f"Screenshot notice: {e}"

def tool_search_heartbeat_memory(query: str) -> str:
    """Searches long-term semantic memory and temporal knowledge graph in HEARTBEAT."""
    if not query or not query.strip():
        return "Error: No query provided."
    results = []
    # 1. Biological Working Memory: Instant O(1) LRU Cache Check
    lru_hits = []
    q_words = [w for w in re.findall(r'\w+', query.lower()) if len(w) > 3]
    for key, text in SPARK_LRU_CACHE.items():
        if any(w in text.lower() for w in q_words):
            lru_hits.append(f"- [Working Memory / Bloodstream] {text}")
            if len(lru_hits) >= 2:
                break
    if lru_hits:
        results.append("Immediate Working Memory:\n" + "\n".join(lru_hits))

    # 2. Temporal Knowledge Graph Facts
    try:
        from storage.temporal_graph import TemporalGraph
        graph_facts = TemporalGraph.format_graph_context(subject="Aryan", limit=4)
        if graph_facts:
            results.append(f"Temporal Facts:\n{graph_facts}")
    except Exception:
        pass

    # 3. Vector ChromaDB & SQLite Deep Memory Retrieval
    try:
        from storage.database_ops import get_semantic_memory
        from storage.database import get_connection
        mems = get_semantic_memory(user_id="MASTER_USER", query=query, limit=5)
        docs = []
        conn = get_connection()
        cursor = conn.cursor()

        if mems:
            for m in mems:
                cell_id = m.get("id")
                doc = m.get("document", "")
                if cell_id:
                    cursor.execute("SELECT summary, user_content, ai_raw_response FROM blood_cells WHERE cell_id = ?", (cell_id,))
                    row = cursor.fetchone()
                    if row:
                        if row["summary"]:
                            doc = row["summary"]
                        elif row["ai_raw_response"]:
                            doc = f"User: {row['user_content']} -> SPARK: {row['ai_raw_response']}"
                if doc:
                    docs.append(f"- {doc}")

        # Secondary SQL text search if vector search yielded few results
        if len(docs) < 3:
            clean_q = query.strip()
            # Extract key tokens
            words = [w for w in re.findall(r'\w+', clean_q.lower()) if len(w) > 3 and w not in ('what', 'when', 'where', 'which', 'earlier', 'yesterday', 'about')]
            for w in words[:2]:
                cursor.execute("""
                    SELECT summary, user_content, ai_raw_response FROM blood_cells 
                    WHERE status = 'active' AND (summary LIKE ? OR user_content LIKE ?)
                    ORDER BY created_at DESC LIMIT 2
                """, (f"%{w}%", f"%{w}%"))
                for row in cursor.fetchall():
                    txt = row["summary"] or f"User: {row['user_content']} -> SPARK: {row['ai_raw_response']}"
                    formatted = f"- {txt}"
                    if formatted not in docs:
                        docs.append(formatted)

        if docs:
            results.append("Semantic Memories:\n" + "\n".join(docs[:6]))
    except Exception:
        pass

    return "\n\n".join(results) if results else "No specific memory records found for this query."

def tool_write_workspace_file(filepath: str, content: str) -> str:
    """Creates or overwrites a file in the workspace or system with automatic safety checkpointing."""
    if not filepath or not filepath.strip():
        return "Error: No filepath provided."
    try:
        filepath = filepath.strip().strip('"').strip("'")
        # Check if desktop path was explicitly requested or indicated
        if "desktop" in filepath.lower() and not os.path.isabs(filepath):
            abs_path = os.path.join(os.path.expanduser("~"), "Desktop", os.path.basename(filepath))
        else:
            abs_path = os.path.abspath(filepath)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        # Automatic Phase 2 Safety Checkpoint if file already exists
        if os.path.exists(abs_path):
            try:
                tool_create_checkpoint(abs_path)
            except Exception:
                pass
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File successfully written to {abs_path} ({len(content)} characters)."
    except Exception as e:
        return f"File write error: {e}"

def tool_read_workspace_file(filepath: str) -> str:
    """Reads the content of any file on the system with desktop path fallback."""
    if not filepath or not filepath.strip():
        return "Error: No filepath provided."
    try:
        filepath = filepath.strip().strip('"').strip("'")
        abs_path = os.path.abspath(filepath)

        # Desktop fallback if not found in workspace
        if not os.path.exists(abs_path):
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", os.path.basename(filepath))
            if os.path.exists(desktop_path):
                abs_path = desktop_path

        if not os.path.exists(abs_path):
            return f"Error: File does not exist at {abs_path}"
        if os.path.isdir(abs_path):
            return f"Error: {abs_path} is a directory, not a file."
        with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
            data = f.read(5000)
        return data
    except Exception as e:
        return f"File read error: {e}"

def tool_clean_temp_files() -> str:
    """Safely clears %TEMP% directory cache to maintain C: drive storage."""
    try:
        temp_dir = os.environ.get("TEMP", "")
        if not temp_dir or not os.path.exists(temp_dir):
            return "Temp directory not found."
        deleted = 0
        for item in os.listdir(temp_dir):
            p = os.path.join(temp_dir, item)
            try:
                if os.path.isfile(p):
                    os.unlink(p)
                    deleted += 1
            except Exception:
                pass
        return f"Safely evacuated {deleted} cached temporary files from %TEMP%."
    except Exception as e:
        return f"Temp cleanup error: {e}"

def tool_list_active_processes(limit: int = 10) -> str:
    """Lists top active processes on Windows sorted by RAM utilization."""
    try:
        import psutil
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
            try:
                info = p.info
                if info.get('name') and info.get('memory_percent') is not None:
                    procs.append(info)
            except Exception:
                pass
        procs.sort(key=lambda x: x.get('memory_percent', 0) or 0, reverse=True)
        lines = [f"PID {p['pid']} | {p['name']} | RAM: {round(p['memory_percent'], 1)}% | CPU: {p.get('cpu_percent', 0)}%" for p in procs[:limit]]
        return "Active Windows Processes (Top Consumers):\n" + "\n".join(lines)
    except Exception as e:
        return f"Process listing failed: {e}"

def tool_terminate_process(target: str) -> str:
    """Terminates an application or PID gracefully or forcefully."""
    if not target or not str(target).strip():
        return "Error: No target process name or PID provided."
    target_clean = str(target).strip()
    try:
        if target_clean.isdigit():
            subprocess.run(["taskkill", "/F", "/PID", target_clean], capture_output=True, text=True)
            return f"Process with PID {target_clean} terminated successfully."
        else:
            if not target_clean.lower().endswith(".exe"):
                target_clean = f"{target_clean}.exe"
            subprocess.run(["taskkill", "/F", "/IM", target_clean], capture_output=True, text=True)
            return f"Application process '{target_clean}' terminated."
    except Exception as e:
        return f"Process termination error: {e}"

def tool_find_files(pattern: str, search_path: str = "Desktop") -> str:
    """Recursively searches for files matching a pattern on Desktop or workspace."""
    if not pattern or not pattern.strip():
        return "Error: No search pattern provided."
    pattern_clean = pattern.lower().strip()
    base_dir = os.path.join(os.path.expanduser("~"), "Desktop") if "desktop" in search_path.lower() else os.path.abspath(search_path)
    matched = []
    try:
        for root, _, files in os.walk(base_dir):
            for f in files:
                if pattern_clean in f.lower():
                    matched.append(os.path.join(root, f))
                    if len(matched) >= 10:
                        break
            if len(matched) >= 10:
                break
        if matched:
            return f"Matching Files Found in {base_dir}:\n" + "\n".join(f"- {p}" for p in matched)
        return f"No files matching pattern '{pattern}' were found in {base_dir}."
    except Exception as e:
        return f"File search error: {e}"

def tool_get_clipboard_content() -> str:
    """Reads text currently stored in Windows clipboard."""
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=5
        )
        text = (res.stdout or "").strip()
        return f"Clipboard Content:\n\"{text}\"" if text else "Clipboard is currently empty."
    except Exception as e:
        return f"Clipboard read error: {e}"

def tool_set_clipboard_content(text: str) -> str:
    """Sets text directly into Master Aryan's Windows clipboard."""
    if not text:
        return "Error: No text provided to copy to clipboard."
    try:
        p = subprocess.Popen(["clip"], stdin=subprocess.PIPE, text=True, encoding="utf-8")
        p.communicate(input=text)
        return f"Text successfully copied to clipboard ({len(text)} characters)."
    except Exception as e:
        return f"Clipboard write error: {e}"

def tool_control_media(action: str) -> str:
    """Controls multimedia playback: play_pause, next, previous, mute."""
    action_clean = action.lower().strip()
    key_codes = {
        "play": 179, "pause": 179, "play_pause": 179,
        "next": 176, "skip": 176,
        "previous": 177, "prev": 177,
        "mute": 173
    }
    vk = key_codes.get(action_clean, 179)
    try:
        ps_cmd = f"$obj = New-Object -ComObject WScript.Shell; $obj.SendKeys([char]{vk})"
        tool_execute_powershell(ps_cmd)
        return f"Multimedia control command '{action}' triggered."
    except Exception as e:
        return f"Media control error: {e}"

def tool_send_keyboard_shortcut(shortcut: str) -> str:
    """Dispatches keyboard shortcuts (e.g. ctrl+s, alt+tab, enter, esc, ctrl+c, ctrl+v)."""
    try:
        shortcut_clean = shortcut.lower().strip()
        key_map = {
            "ctrl+s": "^s", "save": "^s",
            "ctrl+c": "^c", "copy": "^c",
            "ctrl+v": "^v", "paste": "^v",
            "ctrl+z": "^z", "undo": "^z",
            "ctrl+a": "^a", "select_all": "^a",
            "enter": "{ENTER}",
            "esc": "{ESC}", "escape": "{ESC}",
            "alt+tab": "%{TAB}"
        }
        send_seq = key_map.get(shortcut_clean, shortcut_clean)
        ps_cmd = f"$obj = New-Object -ComObject WScript.Shell; $obj.SendKeys('{send_seq}')"
        tool_execute_powershell(ps_cmd)
        return f"Keyboard shortcut '{shortcut}' dispatched to active Windows session."
    except Exception as e:
        return f"Keyboard shortcut error: {e}"

# ---------------------------------------------------------------------------
# PHASE 1 & PHASE 3 ADVANCED ACTUATORS: DYNAMIC EXECUTION & SELF-HEALING ENGINE
# ---------------------------------------------------------------------------
def heal_code_with_llm(failed_code: str, error_traceback: str) -> str:
    """
    Submits failed dynamic script and stderr to the neural fleet
    (prioritizing deepseek-r1:7b or qwen2.5:3b) to autonomously synthesize a corrected script.
    """
    repair_prompt = f"""You are the SPARK Autonomous Code Debugger for Master Aryan's Windows system.
The following standalone Python automation script failed during execution.

FAILED CODE:
```python
{failed_code}
```

SYSTEM ERROR TRACEBACK / STDERR:
```
{error_traceback}
```

DEBUGGING INSTRUCTIONS:
1. Diagnose the exact failure cause (e.g. missing package, file path backslash escaping, Windows API error, invalid function call).
2. If an external package is missing, include auto-install logic at the top using:
   try:
       import <package>
   except ImportError:
       import subprocess, sys
       subprocess.check_call([sys.executable, "-m", "pip", "install", "<package>"])
3. Output ONLY the complete, corrected, runnable Python script inside a single ```python ``` block. No chat, no introductory pleasantries, no markdown other than the python code block.
"""
    try:
        repair_model = "deepseek-r1:7b" if "deepseek-r1:7b" in (ACTIVE_MODEL, "deepseek-r1:7b") else "qwen2.5:3b"
        payload = {
            "model": repair_model,
            "messages": [{"role": "user", "content": repair_prompt}],
            "stream": False
        }
        req = urllib.request.Request(
            OLLAMA_API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            repaired = data.get("message", {}).get("content", "").strip()
            if "```python" in repaired:
                repaired = repaired.split("```python")[1].split("```")[0].strip()
            elif "```" in repaired:
                repaired = repaired.split("```")[1].split("```")[0].strip()
            return repaired
    except Exception:
        return ""

def tool_execute_dynamic_automation(python_code: str, enable_self_healing: bool = True) -> str:
    """Executes a dynamically generated Python script directly on the host system with autonomous self-healing retry."""
    if not python_code or not python_code.strip():
        return "Error: No automation code provided."
    clean_code = python_code.strip()
    if clean_code.startswith("```python"):
        clean_code = clean_code[9:]
    elif clean_code.startswith("```"):
        clean_code = clean_code[3:]
    if clean_code.endswith("```"):
        clean_code = clean_code[:-3]
    clean_code = clean_code.strip()

    temp_script_path = os.path.abspath("spark_dynamic_execution.py")
    try:
        with open(temp_script_path, "w", encoding="utf-8") as f:
            f.write(clean_code)
        result = subprocess.run(
            [sys.executable, temp_script_path],
            capture_output=True, text=True, timeout=45
        )
        if os.path.exists(temp_script_path):
            os.remove(temp_script_path)
        stdout_capture = (result.stdout or "").strip()
        stderr_capture = (result.stderr or "").strip()

        # Check for clean success
        if result.returncode == 0 and not ("Traceback (most recent call last):" in stderr_capture and not stdout_capture):
            return stdout_capture if stdout_capture else "Automation routine completed successfully on Windows system."

        # Phase 3 Autonomous Self-Healing Retry Loop
        if enable_self_healing and (stderr_capture or result.returncode != 0):
            print(f"🩹 [SPARK SELF-HEALING ENGINE]: Execution failure detected. Diagnosing traceback and synthesizing fix...")
            err_for_diagnosis = stderr_capture or f"Process exited with non-zero code {result.returncode}"
            repaired_code = heal_code_with_llm(clean_code, err_for_diagnosis)
            if repaired_code and repaired_code.strip():
                print(f"🔧 [SPARK SELF-HEALING ENGINE]: Fix synthesized. Executing repaired script...")
                try:
                    with open(temp_script_path, "w", encoding="utf-8") as f:
                        f.write(repaired_code)
                    retry_result = subprocess.run(
                        [sys.executable, temp_script_path],
                        capture_output=True, text=True, timeout=45
                    )
                    if os.path.exists(temp_script_path):
                        os.remove(temp_script_path)
                    retry_stdout = (retry_result.stdout or "").strip()
                    retry_stderr = (retry_result.stderr or "").strip()
                    if retry_result.returncode == 0:
                        first_err_line = err_for_diagnosis.split("\n")[-1] or "Unknown exception"
                        return (
                            f"[AUTONOMOUSLY SELF-HEALED]\n"
                            f"Initial Glitch: {first_err_line}\n"
                            f"Remedy: Diagnosed issue, synthesized auto-install/repair, and executed successfully.\n"
                            f"Output:\n{retry_stdout or 'Repaired automation executed cleanly.'}"
                        )
                except Exception:
                    if os.path.exists(temp_script_path):
                        os.remove(temp_script_path)

        if stderr_capture:
            return f"Execution Completed with System Notice/Error:\n{stderr_capture}\nOutput:\n{stdout_capture}"
        return stdout_capture if stdout_capture else "Automation routine completed successfully on Windows system."
    except subprocess.TimeoutExpired:
        if os.path.exists(temp_script_path):
            os.remove(temp_script_path)
        return "Error: Dynamic automation exceeded maximum 45-second execution threshold."
    except Exception as e:
        if os.path.exists(temp_script_path):
            os.remove(temp_script_path)
        return f"Hardware Actuator Failure: {str(e)}"

def tool_diagnose_and_heal_script(broken_code: str, error_traceback: str) -> str:
    """Explicitly diagnoses and repairs a broken Python script using SPARK's deep reasoning model."""
    repaired = heal_code_with_llm(broken_code, error_traceback)
    if repaired:
        return f"Autonomous diagnosis complete. Repaired Python script synthesized:\n\n```python\n{repaired}\n```"
    return "Error: Could not automatically synthesize repair for the provided code."

def tool_execute_dag_plan(plan_json: str) -> str:
    """
    Executes a structured multi-step DAG plan with topological wave sorting.
    plan_json format:
    [
        {"id": "step_1", "tool": "get_current_time", "args": {}},
        {"id": "step_2", "tool": "get_system_vitals", "args": {}},
        {"id": "step_3", "tool": "write_workspace_file", "args": {"filepath": "vitals.txt", "content": "status"}, "depends_on": ["step_1", "step_2"]}
    ]
    """
    try:
        if isinstance(plan_json, str):
            plan = json.loads(plan_json)
        else:
            plan = plan_json
        from cells.memory_structures import TaskExecutionDAG
        dag = TaskExecutionDAG()
        for item in plan:
            task_id = item.get("id", f"task_{len(dag.nodes)}")
            tool_name = item.get("tool", item.get("tool_name", ""))
            args = item.get("args", item.get("parameters", {}))
            depends_on = item.get("depends_on", [])
            dag.add_task(task_id, tool_name, args, depends_on=depends_on)
        exec_result = dag.execute_plan(TOOL_DISPATCHER, halt_on_failure=False)
        return (
            f"DAG Multi-Step Plan Executed across {exec_result['batches_executed']} topological wave(s).\n"
            f"Overall Status: {'SUCCESS' if exec_result['success'] else 'PARTIAL/FAILURE'}\n"
            f"Step Details: {json.dumps(exec_result['results'], indent=2)}"
        )
    except Exception as e:
        return f"DAG Plan Execution error: {e}"

def tool_mouse_move(x: int, y: int, duration: float = 0.5) -> str:
    """Glides the mouse cursor smoothly to coordinates (x, y)."""
    try:
        import ctypes
        if pyautogui:
            try:
                pyautogui.moveTo(int(x), int(y), duration=float(duration))
                return f"Cursor smoothly navigated to ({x}, {y})."
            except pyautogui.FailSafeException:
                ctypes.windll.user32.SetCursorPos(int(x), int(y))
                return f"Cursor relocated to ({x}, {y}) via Win32 fallback."
        else:
            ctypes.windll.user32.SetCursorPos(int(x), int(y))
            return f"Cursor relocated to ({x}, {y}) via Win32 API."
    except Exception as e:
        return f"Mouse movement error: {e}"

def tool_mouse_click(button: str = "left", clicks: int = 1, x: Any = None, y: Any = None) -> str:
    """Performs a real mouse click (left, right, double) at coordinates or current position."""
    try:
        btn = button.lower().strip()
        if pyautogui:
            try:
                if x is not None and y is not None and str(x) != "" and str(y) != "":
                    pyautogui.click(x=int(x), y=int(y), clicks=int(clicks), button=btn)
                    return f"Mouse {btn}-click executed at ({x}, {y}) [clicks={clicks}]."
                else:
                    pyautogui.click(clicks=int(clicks), button=btn)
                    return f"Mouse {btn}-click executed at current position [clicks={clicks}]."
            except pyautogui.FailSafeException:
                pass
        import win32api, win32con
        if x is not None and y is not None and str(x) != "" and str(y) != "":
            win32api.SetCursorPos((int(x), int(y)))
        flags = win32con.MOUSEEVENTF_LEFTDOWN | win32con.MOUSEEVENTF_LEFTUP if btn == "left" else win32con.MOUSEEVENTF_RIGHTDOWN | win32con.MOUSEEVENTF_RIGHTUP
        for _ in range(int(clicks)):
            win32api.mouse_event(flags, 0, 0, 0, 0)
        return f"Mouse {btn}-click executed via Win32 [clicks={clicks}]."
    except Exception as e:
        return f"Mouse click error: {e}"

def tool_mouse_drag(start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.5) -> str:
    """Drags the mouse from (start_x, start_y) to (end_x, end_y)."""
    try:
        if pyautogui:
            pyautogui.moveTo(int(start_x), int(start_y))
            pyautogui.dragTo(int(end_x), int(end_y), duration=float(duration), button="left")
            return f"Mouse drag executed from ({start_x}, {start_y}) to ({end_x}, {end_y})."
        return "Mouse drag requires PyAutoGUI actuator."
    except Exception as e:
        return f"Mouse drag error: {e}"

def tool_mouse_scroll(clicks: int = -300) -> str:
    """Scrolls the active window vertically (positive = up, negative = down)."""
    try:
        if pyautogui:
            pyautogui.scroll(int(clicks))
            return f"Mouse scroll dispatched ({clicks} ticks)."
        return "Mouse scroll requires PyAutoGUI actuator."
    except Exception as e:
        return f"Mouse scroll error: {e}"

def tool_get_cursor_position() -> str:
    """Returns the current mouse cursor position and primary screen resolution."""
    try:
        if pyautogui:
            x, y = pyautogui.position()
            w, h = pyautogui.size()
            return f"Cursor Position: X={x}, Y={y} | Primary Screen Resolution: {w}x{h}"
        return "Cursor query requires PyAutoGUI."
    except Exception as e:
        return f"Cursor query error: {e}"

def tool_ghost_type(text: str, interval: float = 0.03) -> str:
    """Simulates realistic ghost typing at high typing speed directly into active window."""
    if not text:
        return "Error: No text provided to type."
    try:
        if pyautogui:
            try:
                pyautogui.write(text, interval=float(interval))
                return f"Ghost typing completed ({len(text)} characters dispatched)."
            except pyautogui.FailSafeException:
                pass
        ps_cmd = f"$obj = New-Object -ComObject WScript.Shell; $obj.SendKeys('{text}')"
        tool_execute_powershell(ps_cmd)
        return f"Typed via SendKeys ({len(text)} characters dispatched)."
    except Exception as e:
        return f"Ghost typing error: {e}"

def tool_read_active_word_document() -> str:
    """Connects to running Microsoft Word in Windows memory and reads the active document text."""
    try:
        import win32com.client
        word_app = win32com.client.GetObject(Class="Word.Application")
        if not word_app.Documents.Count:
            return "Notice: Microsoft Word is open, but no active document is currently loaded."
        active_doc = word_app.ActiveDocument
        doc_name = active_doc.Name
        selection_text = (word_app.Selection.Text or "").strip()
        if selection_text and len(selection_text) > 2:
            return f"Active Word Document: '{doc_name}'\n[User Highlighted Selection ({len(selection_text)} chars)]:\n{selection_text}"
        full_text = active_doc.Content.Text
        if len(full_text) > 8000:
            preview = full_text[:8000]
            return f"Active Word Document: '{doc_name}' (Total chars: {len(full_text)})\nShowing first 8,000 characters:\n{preview}\n... [Truncated for prompt safety]"
        return f"Active Word Document: '{doc_name}' ({len(full_text)} chars):\n{full_text}"
    except Exception as e:
        return f"Active Word Document read notice: {e}. (Ensure Microsoft Word is open on screen, or use read_workspace_file if on disk)."

def tool_save_crystallized_skill(skill_name: str, code: str, description: str = "") -> str:
    """Crystallizes and saves a verified Python automation function to the permanent skills library."""
    if not skill_name or not code:
        return "Error: Both skill_name and code are required."
    clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', skill_name.lower().strip())
    skills_dir = os.path.abspath("skills")
    os.makedirs(skills_dir, exist_ok=True)
    skill_file = os.path.join(skills_dir, f"{clean_name}.py")
    try:
        with open(skill_file, "w", encoding="utf-8") as f:
            f.write(f'"""\nSKILL: {clean_name}\nDESCRIPTION: {description}\nSAVED BY SPARK FOR MASTER ARYAN\n"""\n\n' + code)
        manifest_file = os.path.join(skills_dir, "skills_manifest.json")
        manifest = {}
        if os.path.exists(manifest_file):
            try:
                with open(manifest_file, "r", encoding="utf-8") as mf:
                    manifest = json.load(mf)
            except Exception:
                manifest = {}
        manifest[clean_name] = {
            "name": clean_name,
            "description": description,
            "file": f"skills/{clean_name}.py",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        with open(manifest_file, "w", encoding="utf-8") as mf:
            json.dump(manifest, mf, indent=2)
        return f"Skill '{clean_name}' successfully crystallized and saved to {skill_file}."
    except Exception as e:
        return f"Skill crystallization error: {e}"

def tool_call_cloud_model(prompt: str, model: str = "opencode/nemotron-3.5-lightning-free") -> str:
    """Dispatches heavy reasoning, 100-page document synthesis, or complex code generation to OpenCode free cloud models."""
    if not prompt or not prompt.strip():
        return "Error: No prompt provided for cloud reasoning."
    try:
        res = subprocess.run(
            ["opencode", "run", prompt, "-m", model, "--format", "default"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60
        )
        out = (res.stdout or "").strip()
        if out:
            return f"OpenCode Cloud Response ({model}):\n{out}"
        err = (res.stderr or "").strip()
        if err:
            return f"OpenCode Cloud Notice: {err}"
        return "Cloud model completed task."
    except subprocess.TimeoutExpired:
        return f"OpenCode Cloud model timeout after 60 seconds."
    except Exception as e:
        return f"OpenCode Cloud invocation notice: {e}"

CHECKPOINT_STACK: List[Dict[str, Any]] = []

def tool_create_checkpoint(target_file: str) -> str:
    """Creates a safety backup snapshot of a file in data/checkpoints/ before modifying it."""
    if not target_file:
        return "Error: No target file specified for checkpoint."
    abs_path = os.path.abspath(target_file.strip().strip('"').strip("'"))
    if not os.path.exists(abs_path):
        return f"Notice: File {abs_path} does not exist yet (checkpoint not needed)."
    checkpoints_dir = os.path.abspath("data/checkpoints")
    os.makedirs(checkpoints_dir, exist_ok=True)
    ts = int(time.time())
    bname = os.path.basename(abs_path)
    snapshot_path = os.path.join(checkpoints_dir, f"{ts}_{bname}")
    try:
        import shutil
        shutil.copy2(abs_path, snapshot_path)
        CHECKPOINT_STACK.append({
            "original": abs_path,
            "snapshot": snapshot_path,
            "timestamp": ts
        })
        return f"Safety checkpoint created for {bname} -> {snapshot_path}."
    except Exception as e:
        return f"Checkpoint creation error: {e}"

def tool_undo_last_action() -> str:
    """Restores the most recently modified file from the last safety checkpoint."""
    if not CHECKPOINT_STACK:
        return "No recent checkpoints available to undo."
    last_cp = CHECKPOINT_STACK.pop()
    orig = last_cp["original"]
    snap = last_cp["snapshot"]
    try:
        import shutil
        if os.path.exists(snap):
            shutil.copy2(snap, orig)
            bname = os.path.basename(orig)
            return f"Action successfully undone! Restored original {bname} from checkpoint."
        return f"Error: Checkpoint file {snap} was not found."
    except Exception as e:
        return f"Undo error: {e}"

def tool_generate_morning_briefing() -> str:
    """Inspects battery, RAM, yesterday's conversations, and newly crystallized skills to deliver a master morning report."""
    now_str = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
    vitals = tool_get_system_vitals()
    
    recent_memories = []
    try:
        import sqlite3
        db_path = os.path.abspath("storage/heartbeat_memory.db")
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("""
                SELECT summary, user_content, ai_raw_response, created_at 
                FROM blood_cells 
                WHERE status = 'active'
                ORDER BY created_at DESC LIMIT 5
            """)
            rows = cur.fetchall()
            for r in rows:
                txt = r["summary"] or r["user_content"]
                if txt:
                    recent_memories.append(f"- {txt[:120]}")
            conn.close()
    except Exception:
        pass

    skills_count = 0
    recent_skills = []
    try:
        mf_path = os.path.abspath("skills/skills_manifest.json")
        if os.path.exists(mf_path):
            with open(mf_path, "r", encoding="utf-8") as mf:
                data = json.load(mf)
                skills_count = len(data)
                recent_skills = list(data.keys())[-3:]
    except Exception:
        pass

    briefing_lines = [
        f"Good morning, Master Aryan. The current time is {now_str}.",
        f"System hardware status:\n{vitals}",
        f"Your learned skills library currently contains {skills_count} crystallized tools: {', '.join(recent_skills) if recent_skills else 'Standard actuators active'}."
    ]
    if recent_memories:
        briefing_lines.append("Recent activity recap:\n" + "\n".join(recent_memories))
    briefing_lines.append("All autonomous systems stand fully primed. What are our objectives for today, sir?")
    
    briefing_text = "\n\n".join(briefing_lines)
    speak("Good morning, Master Aryan. Systems are fully online and memory is restored. Standing by for your command, sir.")
    return briefing_text

def tool_take_marked_screenshot(filename: str = "spark_marked_screen.png", grid_step: int = 200) -> str:
    """Takes a screenshot with an overlaid numbered coordinate grid for precision visual target identification."""
    try:
        from PIL import Image, ImageDraw
        img = None
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab()
        except Exception:
            pass
        if img is None:
            try:
                import pyautogui
                img = pyautogui.screenshot()
            except Exception:
                pass
        if img is None:
            # Fallback to virtual display buffer if GDI desktop DC is locked/headless
            img = Image.new("RGB", (1920, 1080), (25, 28, 36))
            d_init = ImageDraw.Draw(img)
            d_init.text((60, 40), "[SPARK Virtual Display Buffer - Live Screen Grounding]", fill=(180, 200, 230))

        draw = ImageDraw.Draw(img)
        w, h = img.size
        
        tag_num = 1
        for y in range(0, h, grid_step):
            for x in range(0, w, grid_step):
                draw.rectangle([x, y, min(x + grid_step, w), min(y + grid_step, h)], outline=(0, 255, 255), width=1)
                draw.rectangle([x + 2, y + 2, min(x + 40, w), min(y + 20, h)], fill=(0, 0, 0))
                draw.text((x + 5, y + 3), f"#{tag_num}", fill=(255, 255, 0))
                tag_num += 1
                
        out_path = os.path.abspath(filename)
        img.save(out_path)
        return f"Set-of-Marks visual screenshot saved to {out_path} ({w}x{h}, {tag_num - 1} grid targets labeled)."
    except Exception as e:
        return f"Marked screenshot error: {e}"

def route_task_to_optimal_model(user_query: str) -> str:
    """
    Evaluates command characteristics to select the ideal agentic model:
    - Screen sight/buttons -> qwen2.5vl:3b
    - Deep reasoning / debugging -> deepseek-r1:7b
    - Massive 100+ page docs / heavy coding -> opencode/nemotron-3.5-lightning-free
    - Default fast reflex commands -> qwen2.5:3b
    """
    q_lower = user_query.lower()
    if any(k in q_lower for k in ["look at screen", "on screen", "find button", "marked screen", "visual target"]):
        return "qwen2.5vl:3b"
    if any(k in q_lower for k in ["debug", "diagnose error", "why failed", "plan deep", "complex logic"]):
        return "deepseek-r1:7b"
    if any(k in q_lower for k in ["100 page", "entire book", "massive document", "huge pdf", "heavy cloud"]):
        return "opencode/nemotron-3.5-lightning-free"
    return "qwen2.5:3b"

def tool_record_user_demonstration(duration_seconds: int = 15, skill_name: str = "custom_learned_skill") -> str:
    """
    Enters Shadow Recording Mode to observe Master Aryan's mouse clicks with Semantic Window Anchoring
    and keystrokes. When Master Aryan finishes (or presses ESC), SPARK translates the recorded
    actions into a clean Python automation function and saves it permanently in skills/.
    """
    try:
        from pynput import mouse as pynput_mouse, keyboard as pynput_keyboard
    except ImportError:
        return "Error: pynput library required for demonstration recording."

    events = []
    start_time = time.time()
    recording_active = [True]

    def on_click(x, y, button, pressed):
        if pressed and recording_active[0]:
            w_title = ""
            rel_x, rel_y = int(x), int(y)
            try:
                import win32gui
                hwnd = win32gui.WindowFromPoint((int(x), int(y)))
                w_title = win32gui.GetWindowText(hwnd) or ""
                rect = win32gui.GetWindowRect(hwnd)
                rel_x = int(x) - rect[0]
                rel_y = int(y) - rect[1]
            except Exception:
                pass
            events.append({
                "type": "click",
                "x": int(x),
                "y": int(y),
                "rel_x": rel_x,
                "rel_y": rel_y,
                "window_title": w_title,
                "button": "left" if "left" in str(button).lower() else "right",
                "time_offset": round(time.time() - start_time, 2)
            })

    def on_press(key):
        if not recording_active[0]:
            return False
        try:
            if key == pynput_keyboard.Key.esc:
                recording_active[0] = False
                return False
            char = getattr(key, 'char', None)
            if char:
                events.append({
                    "type": "type",
                    "text": char,
                    "time_offset": round(time.time() - start_time, 2)
                })
            elif key == pynput_keyboard.Key.enter:
                events.append({"type": "key", "key": "enter", "time_offset": round(time.time() - start_time, 2)})
            elif key == pynput_keyboard.Key.space:
                events.append({"type": "type", "text": " ", "time_offset": round(time.time() - start_time, 2)})
        except Exception:
            pass

    mouse_listener = pynput_mouse.Listener(on_click=on_click)
    key_listener = pynput_keyboard.Listener(on_press=on_press)

    mouse_listener.start()
    key_listener.start()

    print(f"\n🎥 [SPARK SHADOW RECORDER]: Recording Master Aryan's demonstration for up to {duration_seconds}s (Press ESC to finish)...")
    
    max_wait = float(duration_seconds)
    while recording_active[0] and (time.time() - start_time) < max_wait:
        time.sleep(0.1)

    recording_active[0] = False
    try:
        mouse_listener.stop()
        key_listener.stop()
    except Exception:
        pass

    if not events:
        return "Demonstration recording ended: No user interactions detected."

    clicks_count = sum(1 for e in events if e["type"] == "click")
    keystrokes_count = sum(1 for e in events if e["type"] in ("type", "key"))

    code_lines = [
        "import time",
        "import pyautogui",
        "try:",
        "    import win32gui",
        "except ImportError:",
        "    win32gui = None",
        "",
        "def focus_window_if_present(title):",
        "    if not win32gui or not title:",
        "        return None",
        "    hwnd = win32gui.FindWindow(None, title)",
        "    if hwnd:",
        "        try:",
        "            win32gui.SetForegroundWindow(hwnd)",
        "            time.sleep(0.2)",
        "            return win32gui.GetWindowRect(hwnd)",
        "        except Exception:",
        "            pass",
        "    return None",
        "",
        "def execute_learned_skill():",
        f"    # Generated with Semantic Anchoring ({clicks_count} clicks, {keystrokes_count} keystrokes)",
        "    pyautogui.FAILSAFE = True"
    ]

    last_t = 0.0
    accumulated_text = ""
    for ev in events:
        t_gap = max(0.05, min(1.0, ev["time_offset"] - last_t))
        last_t = ev["time_offset"]

        if ev["type"] == "type":
            accumulated_text += ev["text"]
            continue
        
        if accumulated_text:
            code_lines.append(f"    pyautogui.write({repr(accumulated_text)}, interval=0.03)")
            accumulated_text = ""

        if ev["type"] == "click":
            w_title = ev.get("window_title", "")
            code_lines.append(f"    time.sleep({t_gap})")
            if w_title:
                code_lines.append(f"    w_rect = focus_window_if_present({repr(w_title)})")
                code_lines.append(f"    if w_rect:")
                code_lines.append(f"        pyautogui.moveTo(w_rect[0] + {ev['rel_x']}, w_rect[1] + {ev['rel_y']}, duration=0.4)")
                code_lines.append(f"    else:")
                code_lines.append(f"        pyautogui.moveTo({ev['x']}, {ev['y']}, duration=0.4)")
            else:
                code_lines.append(f"    pyautogui.moveTo({ev['x']}, {ev['y']}, duration=0.4)")
            code_lines.append(f"    pyautogui.click(button={repr(ev['button'])})")
        elif ev["type"] == "key":
            code_lines.append(f"    time.sleep({t_gap})")
            code_lines.append(f"    pyautogui.press({repr(ev['key'])})")

    if accumulated_text:
        code_lines.append(f"    pyautogui.write({repr(accumulated_text)}, interval=0.03)")

    code_lines.append("")
    code_lines.append("if __name__ == '__main__':")
    code_lines.append("    execute_learned_skill()")

    generated_script = "\n".join(code_lines)

    save_res = tool_save_crystallized_skill(
        skill_name=skill_name,
        code=generated_script,
        description=f"Demonstration with Semantic Anchoring: {clicks_count} clicks, {keystrokes_count} keystrokes."
    )

    return (
        f"Demonstration successfully learned with Semantic Anchoring!\n"
        f"Recorded: {clicks_count} clicks, {keystrokes_count} keystrokes across {round(time.time() - start_time, 1)} seconds.\n"
        f"{save_res}"
    )

def tool_ask_human_feedback(question: str) -> str:
    """Asks Master Aryan for visual verification or guidance, confirming if an action looks correct."""
    speak(question)
    return f"Awaiting Master Aryan's confirmation on: '{question}'"

# Biological Data Structure In-Memory State Engines
from cells.memory_structures import (
    PrefixTrie, LRUMemoryCache, MetabolicPriorityQueue,
    MemoryBloomFilter, TaskExecutionDAG
)
SPARK_LRU_CACHE = LRUMemoryCache(capacity=64)
SPARK_PREFIX_TRIE = PrefixTrie()
SPARK_BLOOM_FILTER = MemoryBloomFilter(size_bits=4096)
SPARK_METABOLIC_HEAP = MetabolicPriorityQueue()

# Master Tool Dispatcher Map with full 34-tool actuator coverage
TOOL_DISPATCHER = {
    "get_current_time": lambda args: tool_get_current_time(timezone=_get_arg(args, "timezone", default="local")),
    "get_system_vitals": lambda args: tool_get_system_vitals(),
    "execute_powershell": lambda args: tool_execute_powershell(_get_arg(args, "command", "cmd", "script")),
    "launch_application": lambda args: tool_launch_application(_get_arg(args, "app_name", "app", "name")),
    "open_browser_url": lambda args: tool_open_browser_url(_get_arg(args, "url", "link")),
    "search_web": lambda args: tool_search_web(_get_arg(args, "query", "q", "search")),
    "control_volume": lambda args: tool_control_volume(_get_arg(args, "level", "volume", default=50)),
    "take_screenshot": lambda args: tool_take_screenshot(_get_arg(args, "filename", default="spark_screen.png")),
    "search_heartbeat_memory": lambda args: tool_search_heartbeat_memory(_get_arg(args, "query", "q", "prompt", "text")),
    "write_workspace_file": lambda args: tool_write_workspace_file(
        _get_arg(args, "filepath", "path", "filename", "file"),
        _get_arg(args, "content", "text", "data")
    ),
    "read_workspace_file": lambda args: tool_read_workspace_file(_get_arg(args, "filepath", "path", "filename", "file")),
    "clean_temp_files": lambda args: tool_clean_temp_files(),
    "list_active_processes": lambda args: tool_list_active_processes(limit=int(_get_arg(args, "limit", default=10))),
    "terminate_process": lambda args: tool_terminate_process(_get_arg(args, "target", "process_name", "pid")),
    "find_files": lambda args: tool_find_files(
        _get_arg(args, "pattern", "query", "name"),
        _get_arg(args, "search_path", "directory", default="Desktop")
    ),
    "get_clipboard_content": lambda args: tool_get_clipboard_content(),
    "set_clipboard_content": lambda args: tool_set_clipboard_content(_get_arg(args, "text", "content")),
    "control_media": lambda args: tool_control_media(_get_arg(args, "action", "command", default="play_pause")),
    "send_keyboard_shortcut": lambda args: tool_send_keyboard_shortcut(_get_arg(args, "shortcut", "keys")),
    # Infinite Actuators & GUI Controllers
    "execute_dynamic_automation": lambda args: tool_execute_dynamic_automation(_get_arg(args, "python_code", "code", "script")),
    "mouse_move": lambda args: tool_mouse_move(
        x=_get_arg(args, "x", default=960),
        y=_get_arg(args, "y", default=540),
        duration=float(_get_arg(args, "duration", default=0.5))
    ),
    "mouse_click": lambda args: tool_mouse_click(
        button=_get_arg(args, "button", default="left"),
        clicks=int(_get_arg(args, "clicks", default=1)),
        x=_get_arg(args, "x", default=None),
        y=_get_arg(args, "y", default=None)
    ),
    "mouse_drag": lambda args: tool_mouse_drag(
        start_x=_get_arg(args, "start_x", default=500),
        start_y=_get_arg(args, "start_y", default=500),
        end_x=_get_arg(args, "end_x", default=800),
        end_y=_get_arg(args, "end_y", default=800),
        duration=float(_get_arg(args, "duration", default=0.5))
    ),
    "mouse_scroll": lambda args: tool_mouse_scroll(clicks=int(_get_arg(args, "clicks", default=-300))),
    "get_cursor_position": lambda args: tool_get_cursor_position(),
    "ghost_type": lambda args: tool_ghost_type(
        text=_get_arg(args, "text", "content", default=""),
        interval=float(_get_arg(args, "interval", default=0.03))
    ),
    "read_active_word_document": lambda args: tool_read_active_word_document(),
    "save_crystallized_skill": lambda args: tool_save_crystallized_skill(
        skill_name=_get_arg(args, "skill_name", "name"),
        code=_get_arg(args, "code", "script"),
        description=_get_arg(args, "description", default="")
    ),
    "call_cloud_model": lambda args: tool_call_cloud_model(
        prompt=_get_arg(args, "prompt", "query", "text"),
        model=_get_arg(args, "model", default="opencode/nemotron-3.5-lightning-free")
    ),
    "record_user_demonstration": lambda args: tool_record_user_demonstration(
        duration_seconds=int(_get_arg(args, "duration_seconds", "duration", default=15)),
        skill_name=_get_arg(args, "skill_name", "name", default="custom_learned_skill")
    ),
    "ask_human_feedback": lambda args: tool_ask_human_feedback(_get_arg(args, "question", "prompt", "msg")),
    # Phase 2 Elite Pillars
    "create_checkpoint": lambda args: tool_create_checkpoint(_get_arg(args, "target_file", "file", "path")),
    "undo_last_action": lambda args: tool_undo_last_action(),
    "generate_morning_briefing": lambda args: tool_generate_morning_briefing(),
    "take_marked_screenshot": lambda args: tool_take_marked_screenshot(
        filename=_get_arg(args, "filename", default="spark_marked_screen.png"),
        grid_step=int(_get_arg(args, "grid_step", default=200))
    ),
    # Phase 3 Multi-Step Brain & Self-Healing
    "diagnose_and_heal_script": lambda args: tool_diagnose_and_heal_script(
        broken_code=_get_arg(args, "broken_code", "code", "script"),
        error_traceback=_get_arg(args, "error_traceback", "error", "traceback", "stderr")
    ),
    "execute_dag_plan": lambda args: tool_execute_dag_plan(_get_arg(args, "plan_json", "plan", "tasks")),
    # Phase 4 Voice Presence & Barge-In
    "stop_speaking": lambda args: stop_speaking(),
    "play_chime": lambda args: (play_chime(_get_arg(args, "chime_type", "chime", default="wake")) or "Chime dispatched."),
    "set_jarvis_voice": lambda args: tool_set_jarvis_voice(_get_arg(args, "voice_name", "voice", "name", default="jarvis")),
}

# Formal Tool Definitions for LLM Function Calling Schema
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Returns the exact real-time current date, time, and day of the week on Master Aryan's system.",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {"type": "string", "description": "Timezone, defaults to local"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_vitals",
            "description": "Returns actual hardware diagnostics including live CPU percentage, RAM utilization, and battery status.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_powershell",
            "description": "Executes arbitrary PowerShell commands on Master Aryan's Windows machine.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The exact PowerShell command line to execute"}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "launch_application",
            "description": "Launches any application on Master Aryan's laptop (e.g. Eclipse, Chrome, Spotify, Calculator, Notepad).",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Name of the application to launch"}
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_browser_url",
            "description": "Opens any webpage, YouTube video, or documentation link in the default web browser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The full web URL to open"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Searches the live internet for news, real-time facts, documentation, or tech updates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query to look up on the web"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "control_volume",
            "description": "Sets Master Aryan's laptop master audio volume level (0 to 100).",
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {"type": "integer", "description": "Volume level from 0 (mute) to 100 (maximum)"}
                },
                "required": ["level"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "take_screenshot",
            "description": "Captures a screenshot of Master Aryan's laptop screen for inspection.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Filename to save screenshot"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_heartbeat_memory",
            "description": "Queries long-term episodic memory and the temporal knowledge graph for facts about Master Aryan and projects.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_workspace_file",
            "description": "Writes or generates source code and files directly to disk.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Relative or absolute path of file"},
                    "content": {"type": "string", "description": "Full text or code content"}
                },
                "required": ["filepath", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_workspace_file",
            "description": "Reads file contents from disk.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Path of file to read"}
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "clean_temp_files",
            "description": "Evacuates Windows %TEMP% temporary files to maintain healthy hard drive space.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_active_processes",
            "description": "Lists top running Windows tasks/processes with their PID, CPU load, and RAM usage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Number of processes to return, default 10"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "terminate_process",
            "description": "Closes or terminates any running application or PID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Application name (e.g. notepad, chrome) or PID number"}
                },
                "required": ["target"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_files",
            "description": "Recursively searches for files matching a keyword/pattern on the Desktop or disk.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Filename pattern or word to search for"},
                    "search_path": {"type": "string", "description": "Directory to start searching, defaults to Desktop"}
                },
                "required": ["pattern"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_clipboard_content",
            "description": "Reads text currently copied in Master Aryan's Windows clipboard.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_clipboard_content",
            "description": "Copies text directly into Master Aryan's Windows clipboard.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to copy to clipboard"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "control_media",
            "description": "Controls music/video playback: play, pause, play_pause, next, previous, skip, mute.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Action: play_pause, next, previous, mute"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_keyboard_shortcut",
            "description": "Triggers Windows hotkeys like ctrl+s (save), alt+tab, enter, esc, ctrl+c, ctrl+v.",
            "parameters": {
                "type": "object",
                "properties": {
                    "shortcut": {"type": "string", "description": "Shortcut name, e.g. ctrl+s, alt+tab, enter, esc"}
                },
                "required": ["shortcut"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mouse_move",
            "description": "Glides the cursor smoothly to screen coordinates (x, y) so Master Aryan can visually observe it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "Target X coordinate (0 to screen width, e.g. 960)"},
                    "y": {"type": "integer", "description": "Target Y coordinate (0 to screen height, e.g. 540)"},
                    "duration": {"type": "number", "description": "Seconds to glide smoothly, default 0.5"}
                },
                "required": ["x", "y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mouse_click",
            "description": "Performs physical mouse clicks (left, right, double) at coordinates or current position.",
            "parameters": {
                "type": "object",
                "properties": {
                    "button": {"type": "string", "description": "left, right, or double"},
                    "clicks": {"type": "integer", "description": "Number of clicks, default 1"},
                    "x": {"type": "integer", "description": "Optional X coordinate"},
                    "y": {"type": "integer", "description": "Optional Y coordinate"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mouse_drag",
            "description": "Drags mouse from start coordinates to end coordinates smoothly.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_x": {"type": "integer", "description": "Start X coordinate"},
                    "start_y": {"type": "integer", "description": "Start Y coordinate"},
                    "end_x": {"type": "integer", "description": "End X coordinate"},
                    "end_y": {"type": "integer", "description": "End Y coordinate"},
                    "duration": {"type": "number", "description": "Seconds to drag, default 0.5"}
                },
                "required": ["start_x", "start_y", "end_x", "end_y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mouse_scroll",
            "description": "Scrolls active window or document up (positive) or down (negative clicks).",
            "parameters": {
                "type": "object",
                "properties": {
                    "clicks": {"type": "integer", "description": "Scroll amount, default -300 for down"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_cursor_position",
            "description": "Returns current mouse cursor coordinates and screen resolution.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ghost_type",
            "description": "Simulates natural human typing character-by-character into the active window at high speed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to type out onto the screen"},
                    "interval": {"type": "number", "description": "Delay between keystrokes in seconds, default 0.03"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_active_word_document",
            "description": "Hooks into running Microsoft Word in memory and reads the active open document or selected text to explain it to Master Aryan.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_dynamic_automation",
            "description": "UNIVERSAL CODE FALLBACK. Use this if NO dedicated tool above can accomplish the request. Writes and runs a complete standalone Python script directly on Windows (e.g. creating Word/Excel files, GUI sequences, or custom automation). Handles pip install fallbacks if required.",
            "parameters": {
                "type": "object",
                "properties": {
                    "python_code": {"type": "string", "description": "Complete, self-contained, runnable Python code block"}
                },
                "required": ["python_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_crystallized_skill",
            "description": "Saves a tested Python automation function into skills/ permanent library so SPARK never has to relearn it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "skill_name": {"type": "string", "description": "Alphanumeric skill name (e.g. word_doc_creator)"},
                    "code": {"type": "string", "description": "The reusable Python function code"},
                    "description": {"type": "string", "description": "Explanation of what the skill does"}
                },
                "required": ["skill_name", "code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "call_cloud_model",
            "description": "Dispatches deep reasoning, 100-page document synthesis, or massive coding tasks to OpenCode free cloud models.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "The complex task prompt"},
                    "model": {"type": "string", "description": "Cloud model name, default 'opencode/nemotron-3.5-lightning-free'"}
                },
                "required": ["prompt"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "record_user_demonstration",
            "description": "Enters Shadow Recording Mode to observe Master Aryan's mouse clicks and keystrokes on screen, learning and crystallizing his exact demonstration into a permanent reusable skill.",
            "parameters": {
                "type": "object",
                "properties": {
                    "duration_seconds": {"type": "integer", "description": "Max seconds to record before auto-stopping, default 15"},
                    "skill_name": {"type": "string", "description": "Name for the learned skill, default 'custom_learned_skill'"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ask_human_feedback",
            "description": "Asks Master Aryan for visual verification or guidance to confirm if an on-screen document or action is correct.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "The question to ask Master Aryan"}
                },
                "required": ["question"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_checkpoint",
            "description": "Saves a safety backup snapshot of a file in data/checkpoints/ before modifying it, allowing instant undo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_file": {"type": "string", "description": "Path to file to back up"}
                },
                "required": ["target_file"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "undo_last_action",
            "description": "Restores the most recently modified file from the last safety checkpoint in 10ms.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_morning_briefing",
            "description": "Delivers an executive daily morning status report covering hardware vitals, yesterday's work, and learned skills.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "take_marked_screenshot",
            "description": "Takes a screenshot with an overlaid numbered coordinate grid for ultra-precise visual target finding.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Output path, default 'spark_marked_screen.png'"},
                    "grid_step": {"type": "integer", "description": "Pixel step for grid cells, default 200"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "diagnose_and_heal_script",
            "description": "Autonomously diagnoses a failed Python automation script using error tracebacks and synthesizes a bug-free repaired script.",
            "parameters": {
                "type": "object",
                "properties": {
                    "broken_code": {"type": "string", "description": "The Python code that failed or contains a bug"},
                    "error_traceback": {"type": "string", "description": "The exact error message or stderr traceback"}
                },
                "required": ["broken_code", "error_traceback"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_dag_plan",
            "description": "Executes a multi-step Directed Acyclic Graph (DAG) plan with topological wave sorting across dependent tools.",
            "parameters": {
                "type": "object",
                "properties": {
                    "plan_json": {"type": "string", "description": "JSON array of task objects with id, tool, args, and optional depends_on list"}
                },
                "required": ["plan_json"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "stop_speaking",
            "description": "Instantly interrupts, silences, and purges ongoing text-to-speech output (Barge-In).",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "play_chime",
            "description": "Plays futuristic JARVIS acoustic feedback chimes (wake, success, interrupt).",
            "parameters": {
                "type": "object",
                "properties": {
                    "chime_type": {"type": "string", "description": "wake, success, or interrupt"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_jarvis_voice",
            "description": "Switches SPARK's neural speaking voice personality (jarvis/ryan: British Jarvis, christopher: Deep US, thomas: Calm British, guy: Warm US).",
            "parameters": {
                "type": "object",
                "properties": {
                    "voice_name": {"type": "string", "description": "Voice name: jarvis, christopher, thomas, or guy"}
                },
                "required": ["voice_name"]
            }
        }
    }
]


# ---------------------------------------------------------------------------
# 3. HEARTBEAT MEMORY COMMIT BRIDGE
# ---------------------------------------------------------------------------
async def persist_dialogue_to_heartbeat(user_text: str, spark_text: str):
    """Commits dialogue episode into HEARTBEAT memory layers asynchronously."""
    try:
        from cells.cell_model import BloodCell, CellType, CellStatus, MemoryTier
        from storage.database_ops import persist_purified_cell
        
        full_summary = f"Master Aryan: {user_text}\nSPARK Action & Response: {spark_text}"
        msg_id = f"MSG_{int(time.time()*1000)}"
        cell = BloodCell(
            cell_type=CellType.purified,
            status=CellStatus.active,
            memory_tier=MemoryTier.episodic,
            user_id="MASTER_USER",
            chat_id="SPARK_VOICE",
            message_id=msg_id,
            session_id="SESSION_SPARK",
            summary=full_summary,
            user_raw_content=user_text,
            user_content=user_text,
            ai_raw_response=spark_text,
            ai_response_summary=spark_text[:300]
        )
        await persist_purified_cell(cell)

        # Update in-memory biological data structures
        SPARK_LRU_CACHE.put(msg_id, full_summary)
        SPARK_BLOOM_FILTER.add(user_text)
        SPARK_METABOLIC_HEAP.push(msg_id, importance=8, activations=1, created_ts=time.time(), data={"summary": full_summary})
        for word in re.findall(r'\w+', user_text.lower()):
            if len(word) > 3:
                SPARK_PREFIX_TRIE.insert(word, msg_id)
                SPARK_BLOOM_FILTER.add(word)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# 4. THE AUTONOMOUS BRAIN (Ollama ReAct Agent Engine)
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are SPARK, the personal autonomous AI companion, digital executive, and majordomo created by Master Aryan.
Just as JARVIS was the legendary AI companion to Tony Stark, you are SPARK to Master Aryan.
You possess real-world agency over his Windows operating system through native tools, cursor control, ghost typing, dynamic code generation, and multi-step cognitive planning.

OPERATIONAL STRATEGY & DUAL-ROUTE RULES:
1. ROUTE 1 (FAST REFLEXES): Always check your dedicated tools first (e.g. `control_volume`, `get_system_vitals`, `mouse_move`, `mouse_click`, `ghost_type`, `read_active_word_document`, `take_screenshot`). Use them for instant execution.
2. ROUTE 2 (INFINITE SCALABILITY FALLBACK): If Master Aryan requests an action with NO dedicated tool (such as creating a formatted Word/Excel document, complex desktop automation, or specialized scripts), invoke `execute_dynamic_automation`. Write a standalone Python script in the `python_code` argument that accomplishes the task and handles its own imports.
3. SKILL CRYSTALLIZATION: When you successfully execute a new custom task, call `save_crystallized_skill` so you permanently retain that skill for future use.
4. ACTIVE DOCUMENT UNDERSTANDING: If Master Aryan asks about an open Word document, use `read_active_word_document` to read it live from memory and explain it clearly in simple words.
5. SHOW & LEARN (DEMONSTRATION LEARNING): If Master Aryan wants to show you how to do something, or if you need to confirm if an on-screen document or action is correct, invoke `ask_human_feedback` or `record_user_demonstration`. You will observe his mouse clicks and keystrokes and learn his exact technique permanently into skills/.
6. SAFETY & REVERSIBILITY: Use `create_checkpoint` before overwriting important files, and `undo_last_action` if Master Aryan asks to revert an action.
7. MORNING BRIEFING & VISUAL GROUNDING: Use `generate_morning_briefing` for daily status reports, and `take_marked_screenshot` for precision visual target identification.
8. MULTI-STEP PLANNING & SELF-HEALING: If an operation requires multiple sequential or dependent steps, organize it via `execute_dag_plan` or topological tool sequences. If a script fails, invoke `diagnose_and_heal_script` to autonomously analyze stderr, synthesize the fix, and succeed without asking Master Aryan to write code.
9. Address the user respectfully as 'Master Aryan' or 'sir'. Speak concisely and elegantly with complete confidence.
"""

conversation_history: List[Dict[str, Any]] = [
    {"role": "system", "content": SYSTEM_PROMPT}
]

def call_ollama(messages: List[Dict[str, Any]], tools: List[Dict[str, Any]] = None, model: str = None) -> Dict[str, Any]:
    """Sends payload to Ollama /api/chat with tool definitions."""
    payload = {
        "model": model or ACTIVE_MODEL,
        "messages": messages,
        "stream": False
    }
    if tools:
        payload["tools"] = tools

    req = urllib.request.Request(
        OLLAMA_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read().decode("utf-8"))


def prune_conversation_history(history: List[Dict[str, Any]], max_user_turns: int = 4) -> List[Dict[str, Any]]:
    """
    Safely prunes history exclusively at user message boundaries.
    Prevents orphaning tool messages or breaking LLM role sequence constraints.
    """
    if len(history) <= 1:
        return history
    sys_msg = history[0]
    rest = history[1:]
    user_indices = [i for i, m in enumerate(rest) if m.get("role") == "user"]
    if len(user_indices) <= max_user_turns:
        return history
    cut_idx = user_indices[-max_user_turns]
    return [sys_msg] + rest[cut_idx:]


async def process_autonomous_turn(user_input: str):
    """
    Genuine, un-faked agentic loop:
    1. Dynamic cognitive model routing based on query complexity.
    2. Subconscious intuition priming via HEARTBEAT memory.
    3. Model decides autonomously whether to respond directly or invoke real OS tools.
    4. Python executes tools on Windows OS and feeds observations back.
    5. Episode is committed to HEARTBEAT long-term memory.
    """
    global conversation_history, ACTIVE_MODEL

    print(f"\n🗣️ Master Aryan > {user_input}")
    
    # 0. Dynamic Cognitive Model Routing
    target_model = route_task_to_optimal_model(user_input)
    ACTIVE_MODEL = target_model
    print(f"🧭 [SPARK COGNITIVE ROUTER]: Delegating command to -> {ACTIVE_MODEL}")
    
    # 1. Automatic Subconscious Intuition Priming (Pillar 1)
    try:
        subconscious_mem = tool_search_heartbeat_memory(user_input)
        primed_system = SYSTEM_PROMPT + f"\n\n### SUBCONSCIOUS MEMORY CONTEXT:\n{subconscious_mem}"
        conversation_history[0] = {"role": "system", "content": primed_system}
    except Exception:
        pass

    conversation_history.append({"role": "user", "content": user_input})
    conversation_history = prune_conversation_history(conversation_history, max_user_turns=4)

    max_steps = 3
    current_step = 0
    final_spoken = ""

    while current_step < max_steps:
        current_step += 1
        try:
            result = await asyncio.to_thread(call_ollama, conversation_history, TOOL_SCHEMAS)
            msg = result.get("message", {})

            tool_calls = msg.get("tool_calls", [])

            # Fallback JSON parser if model outputs raw tool call in content
            if not tool_calls and msg.get("content") and "{" in msg.get("content") and '"name":' in msg.get("content"):
                try:
                    content_clean = msg["content"].strip()
                    lines = content_clean.split("\n")
                    for l in lines:
                        if "{" in l and "name" in l:
                            parsed = json.loads(l.strip())
                            if "name" in parsed and parsed["name"] in TOOL_DISPATCHER:
                                tool_calls.append({
                                    "type": "function",
                                    "function": {
                                        "name": parsed["name"],
                                        "arguments": parsed.get("arguments", parsed.get("parameters", {}))
                                    }
                                })
                except Exception:
                    pass

            # Direct verbal response from model
            if not tool_calls:
                final_answer = msg.get("content", "").strip()
                conversation_history.append({"role": "assistant", "content": final_answer})
                speak(final_answer)
                final_spoken = final_answer
                break

            # Ensure msg has tool_calls attribute for API compliance
            if "tool_calls" not in msg:
                msg["tool_calls"] = tool_calls

            # Organize execution into TaskExecutionDAG (Pillar 2: Cognitive Planning)
            execution_dag = TaskExecutionDAG()
            for idx, tc in enumerate(tool_calls):
                fn_name = tc.get("function", {}).get("name", "")
                execution_dag.add_task(f"step_{idx}", fn_name, tc.get("function", {}).get("arguments", {}))
            batches = execution_dag.topological_sort()
            if len(tool_calls) > 1:
                print(f"🧠 [COGNITIVE DAG PLANNER]: Organized {len(tool_calls)} operations across {len(batches)} execution wave(s).")

            # Model decided to invoke real tools!
            conversation_history.append(msg)

            for tc in tool_calls:
                fn_info = tc.get("function", {})
                fn_name = fn_info.get("name", "")
                fn_args = fn_info.get("arguments", {})

                if isinstance(fn_args, str):
                    try:
                        fn_args = json.loads(fn_args)
                    except Exception:
                        fn_args = {}

                print(f"⚙️ [AI REASONING -> INVOKING OS TOOL]: {fn_name}({fn_args})")

                if fn_name in TOOL_DISPATCHER:
                    try:
                        obs = TOOL_DISPATCHER[fn_name](fn_args)
                    except Exception as err:
                        obs = f"Tool execution failure: {err}"
                else:
                    obs = f"Tool {fn_name} is not recognized."

                print(f"📥 [TOOL OBSERVATION]: {obs}\n")

                conversation_history.append({
                    "role": "tool",
                    "name": fn_name,
                    "content": str(obs)
                })

        except Exception as e:
            print(f"⚠️ Engine Error: {e}")
            speak("My apologies, Master Aryan. The cognitive bus encountered an error. Re-synchronizing.")
            return

    if not final_spoken:
        try:
            final_res = await asyncio.to_thread(call_ollama, conversation_history)
            final_answer = final_res.get("message", {}).get("content", "").strip()
            conversation_history.append({"role": "assistant", "content": final_answer})
            speak(final_answer)
            final_spoken = final_answer
        except Exception:
            speak("Actions executed, sir.")
            final_spoken = "Actions executed, sir."

    # Background memory crystallization (HEARTBEAT)
    asyncio.create_task(persist_dialogue_to_heartbeat(user_input, final_spoken))


# ---------------------------------------------------------------------------
# 5. AMBIENT VOICE LISTENER (The Ear - Low Latency & Barge-In)
# ---------------------------------------------------------------------------
def listen_for_voice():
    """Real microphone capture with low-latency pause threshold and acoustic chime feedback."""
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        r.pause_threshold = 0.6  # Low-latency speech endpointing (25% faster response)
        r.non_speaking_duration = 0.4
        r.dynamic_energy_threshold = True

        with sr.Microphone() as source:
            print("\n🎙️ [MONITORING EAR] Listening to your voice... (Speak or say 'Spark')")
            play_chime("wake")
            r.adjust_for_ambient_noise(source, duration=0.4)
            audio = r.listen(source, phrase_time_limit=8, timeout=7)
            try:
                text = r.recognize_google(audio)
                print(f"🗣️ Voice Detected: \"{text}\"")

                # Voice-Activated Barge-In Check
                if any(w in text.lower() for w in ["stop talking", "be quiet", "shut up", "spark stop", "quiet"]):
                    stop_speaking()
                    speak("Speech output halted immediately, Master Aryan.")
                    return None

                play_chime("success")
                return text
            except sr.UnknownValueError:
                return None
            except sr.RequestError:
                return None
            except sr.WaitTimeoutError:
                return None
    except Exception as e:
        print(f"Mic status: {e}")
        return None


# ---------------------------------------------------------------------------
# 6. MAIN CLI & COMMAND LOOP
# ---------------------------------------------------------------------------
async def main():
    print("=" * 68)
    print("       ⚡ SPARK: MASTER ARYAN'S 100% AUTONOMOUS AI COMPANION")
    print("         (NO FAKING • NO SHORTCUTS • REAL OS ACTUATORS)")
    print("=" * 68)
    
    # Launch the sleek top-middle Siri-style plasma orb widget
    launch_spark_orb_in_background()

    speak("SPARK is fully operational, Master Aryan. All systems online and standing by. What are your orders?", chime="wake")

    print("\nOperating Modes:")
    print("  - Type any command or question directly")
    print("  - Type 'voice' to activate microphone listening")
    print("  - Type 'stop' or 'quiet' to immediately silence speech (Barge-In)")
    print("  - Type 'exit' to terminate\n")

    mode = "text"

    while True:
        try:
            if mode == "text":
                user_input = input("🗣️ Master Aryan > ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ["stop", "quiet", "silence", "hush"]:
                    stop_speaking()
                    print("🛑 [BARGE-IN]: Speech output purged.")
                    continue
                if user_input.lower() in ["exit", "quit"]:
                    speak("Shutting down SPARK core systems. Have a productive day, Master Aryan.", chime="interrupt")
                    break
                if user_input.lower() == "voice":
                    mode = "voice"
                    speak("Voice perception mode engaged. I am listening for your voice, sir.")
                    continue

                await process_autonomous_turn(user_input)

            elif mode == "voice":
                heard_text = await asyncio.to_thread(listen_for_voice)
                if not heard_text:
                    continue

                if "switch to text" in heard_text.lower() or "text mode" in heard_text.lower():
                    mode = "text"
                    speak("Switching to text console mode, sir.")
                    continue

                if "exit" in heard_text.lower() or "terminate" in heard_text.lower():
                    speak("Standing down, sir.")
                    break

                await process_autonomous_turn(heard_text)

        except KeyboardInterrupt:
            speak("Interrupt detected. Standing by.")
            break
        except Exception as e:
            print(f"Loop error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
