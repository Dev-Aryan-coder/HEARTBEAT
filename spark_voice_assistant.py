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
logging.getLogger("urllib3").setLevel(logging.WARNING)

# ---------------------------------------------------------------------------
# 1. THE MOUTH (Windows Native SAPI5 Speech Engine)
# ---------------------------------------------------------------------------
try:
    import win32com.client
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    speaker.Volume = 95
    speaker.Rate = 1
except Exception:
    speaker = None

def speak(text: str):
    """Speaks text aloud using Windows Native Voice."""
    clean_text = text.replace("**", "").replace("`", "").replace("#", "").strip()
    print(f"\n⚡ SPARK: {clean_text}\n")
    if speaker:
        try:
            speaker.Speak(clean_text)
        except Exception as e:
            print(f"[Speech Notice: {e}]")


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
    """Creates or overwrites a file in the workspace or system."""
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

# Biological Data Structure In-Memory State Engines
from cells.memory_structures import (
    PrefixTrie, LRUMemoryCache, MetabolicPriorityQueue,
    MemoryBloomFilter, TaskExecutionDAG
)
SPARK_LRU_CACHE = LRUMemoryCache(capacity=64)
SPARK_PREFIX_TRIE = PrefixTrie()
SPARK_BLOOM_FILTER = MemoryBloomFilter(size_bits=4096)
SPARK_METABOLIC_HEAP = MetabolicPriorityQueue()

# Master Tool Dispatcher Map with full 18-tool actuator coverage
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
OLLAMA_API_URL = "http://127.0.0.1:11434/api/chat"
ACTIVE_MODEL = "qwen2.5:3b"

SYSTEM_PROMPT = """You are SPARK, the personal autonomous AI companion, digital executive, and majordomo created by Master Aryan.
Just as JARVIS was the legendary AI companion to Tony Stark, you are SPARK to Master Aryan.
You possess real-world agency over his Windows operating system through native tools.

CORE IDENTITY & RULES:
1. Your name is SPARK. Always identify yourself proudly as SPARK, Master Aryan's autonomous AI companion.
2. ALWAYS use the provided tools when Master Aryan asks about time, hardware vitals, battery, files, volume, web search, launching apps, browser URLs, or system actions. Do NOT guess or hallucinate hardware states or current time.
3. Address the user respectfully as 'Master Aryan' or 'sir'.
4. Speak elegantly, clearly, concisely, and with complete confidence. Avoid overly verbose filler.
5. When you execute actions, briefly confirm the real outcome to Master Aryan.
"""

conversation_history: List[Dict[str, Any]] = [
    {"role": "system", "content": SYSTEM_PROMPT}
]

def call_ollama(messages: List[Dict[str, Any]], tools: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Sends payload to Ollama /api/chat with tool definitions."""
    payload = {
        "model": ACTIVE_MODEL,
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
    1. Append user order to history.
    2. Model decides autonomously whether to respond directly or invoke real OS tools.
    3. Python executes tools on Windows OS and feeds observations back.
    4. Model synthesizes final spoken answer.
    5. Episode is committed to HEARTBEAT long-term memory.
    """
    global conversation_history

    print(f"\n🗣️ Master Aryan > {user_input}")
    
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
# 5. AMBIENT VOICE LISTENER (The Ear)
# ---------------------------------------------------------------------------
def listen_for_voice():
    """Real microphone capture via SpeechRecognition."""
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        with sr.Microphone() as source:
            print("\n🎙️ [MONITORING EAR] Listening to your voice... (Speak or say 'Spark')")
            r.adjust_for_ambient_noise(source, duration=0.8)
            audio = r.listen(source, phrase_time_limit=8)
            try:
                text = r.recognize_google(audio)
                print(f"🗣️ Voice Detected: \"{text}\"")
                return text
            except sr.UnknownValueError:
                return None
            except sr.RequestError:
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
    
    speak("SPARK is fully operational, Master Aryan. All systems online and standing by. What are your orders?")

    print("\nOperating Modes:")
    print("  - Type any command or question directly")
    print("  - Type 'voice' to activate microphone listening")
    print("  - Type 'exit' to terminate\n")

    mode = "text"

    while True:
        try:
            if mode == "text":
                user_input = input("🗣️ Master Aryan > ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ["exit", "quit"]:
                    speak("Shutting down SPARK core systems. Have a productive day, Master Aryan.")
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
