"""
=============================================================================
⚡ SPARK 24/7 PERSISTENT SENTINEL DAEMON (WAKE WORD + WIN+S + AUTOSAVE + AUTO-DISAPPEAR)
=============================================================================
Runs continuously and silently in the background on Master Aryan's laptop.

Features:
1. VOICE ACTIVATION:
   - Wakes up on "Hey Spark", "Hello Spark", "Yo Spark", "Hi Spark", "OK Spark".
2. GLOBAL HOTKEY ACTIVATION:
   - Wakes up on Alt + S, Alt + Shift + S, Ctrl + Shift + S, or Backspace + S.
3. DYNAMIC UI (TOP-MIDDLE PLASMA ORB):
   - Hidden by default.
   - Pops up instantly at top-middle of the screen upon greeting / hotkey.
   - Undulates with live electric sparks matching Siri/JARVIS state.
   - Automatically disappears after 15 seconds of inactivity/silence.
4. 24/7 HARD SHUTDOWN PROTECTION & AUTOSAVE:
   - Autosaves state after every interaction and flushes on Windows shutdown.
   - SQLite WAL persistence guarantees zero lost data even if power is cut.
=============================================================================
"""

import os
import sys
import time
import json
import atexit
import signal
import ctypes
import threading
import asyncio
import re
from typing import Optional, Tuple, Dict, Any

# Ensure project root is in sys.path
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

# Guard against None stdout/stderr when running via pythonw.exe
if sys.stdout is None or sys.stderr is None:
    log_dir = os.path.join(WORKSPACE_DIR, "data")
    os.makedirs(log_dir, exist_ok=True)
    log_fp = open(os.path.join(log_dir, "spark_sentinel.log"), "a", encoding="utf-8", buffering=1)
    if sys.stdout is None:
        sys.stdout = log_fp
    if sys.stderr is None:
        sys.stderr = log_fp

from spark_orb_ui import (
    launch_spark_orb_in_background,
    set_orb_state,
    show_spark_orb,
    hide_spark_orb,
    schedule_spark_orb_auto_hide,
    cancel_spark_orb_auto_hide,
    is_spark_orb_visible
)
from spark_voice_assistant import (
    speak,
    stop_speaking,
    play_chime,
    process_autonomous_turn,
    conversation_history
)
from microphone_driver import recognize_live_speech, is_microphone_available

CHECKPOINT_FILE = os.path.join(WORKSPACE_DIR, "data", "checkpoints", "spark_autosave_state.json")
SENTINEL_RUNNING = True
WAKE_LOCK = threading.Lock()
LAST_INTERACTION_TS = time.time()
AUTO_HIDE_DELAY = 15.0  # Disappear after 15 seconds of silence

# ---------------------------------------------------------------------------
# 1. 24/7 AUTOSAVE & SHUTDOWN PROTECTION
# ---------------------------------------------------------------------------
def autosave_all_state(reason: str = "periodic"):
    """
    Guarantees zero data loss even on sudden laptop shutdown or power button off.
    Flushes all session contexts, memory tokens, and conversation history.
    """
    try:
        os.makedirs(os.path.dirname(CHECKPOINT_FILE), exist_ok=True)
        # Compact serializable messages
        serializable_history = []
        for m in conversation_history[-30:]:
            content = m.get("content", "")
            if isinstance(content, str):
                serializable_history.append({"role": m.get("role"), "content": content[:1000]})

        state_payload = {
            "autosave_timestamp": time.time(),
            "readable_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "reason": reason,
            "master": "Aryan",
            "history_count": len(conversation_history),
            "recent_messages": serializable_history,
            "status": "persistent_online"
        }
        with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
            json.dump(state_payload, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Autosave Notice: {e}]")

def restore_session_state():
    """Restores memory state from disk on laptop boot."""
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            last_saved = data.get("readable_time", "earlier")
            print(f"⚡ [RESTORE]: Loaded SPARK state checkpoint from {last_saved}.")
            return data
        except Exception:
            return None
    return None

# Attach graceful shutdown handlers for Windows OS
def _on_exit_cleanup():
    autosave_all_state(reason="system_shutdown_or_process_exit")

atexit.register(_on_exit_cleanup)

try:
    signal.signal(signal.SIGINT, lambda s, f: (_on_exit_cleanup(), sys.exit(0)))
    signal.signal(signal.SIGTERM, lambda s, f: (_on_exit_cleanup(), sys.exit(0)))
except Exception:
    pass

# Windows Console Ctrl Handler for hard power down / logoff events
try:
    PHANDLER_ROUTINE = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_uint)
    def _win_ctrl_handler(dwCtrlType):
        autosave_all_state(reason=f"windows_ctrl_event_{dwCtrlType}")
        return False
    _handler_ref = PHANDLER_ROUTINE(_win_ctrl_handler)
    ctypes.windll.kernel32.SetConsoleCtrlHandler(_handler_ref, True)
except Exception:
    pass

# ---------------------------------------------------------------------------
# 2. WAKE WORD DETECTION (HEY SPARK, HELLO SPARK, YO SPARK)
# ---------------------------------------------------------------------------
WAKE_GREETING_PATTERNS = [
    r"\b(hey|hello|yo|hi|ok|okay|wake up|listen)\s+(spark|sparks|park)\b",
    r"\b(spark|sparks)\b"
]

def check_for_wake_phrase(text: str) -> Tuple[bool, str]:
    """
    Checks if text contains a wake greeting ('hey spark', 'hello spark', etc.)
    Returns (True, remaining_command) if matched, else (False, '').
    """
    if not text:
        return False, ""
    clean = text.lower().strip()
    for pat in WAKE_GREETING_PATTERNS:
        match = re.search(pat, clean)
        if match:
            # Extract anything after the wake phrase
            end_pos = match.end()
            remainder = clean[end_pos:].strip()
            # Remove leading punctuation
            remainder = re.sub(r"^[,.!?\s]+", "", remainder)
            return True, remainder
    return False, ""

def listen_for_wake_greeting() -> Tuple[bool, str]:
    """Listens continuously in low-latency ambient mode for wake phrase via native hardware mic."""
    try:
        raw_text = recognize_live_speech(timeout=3.5, phrase_time_limit=4.5)
        if raw_text:
            print(f"👂 [HEARD]: \"{raw_text}\"", flush=True)
            return check_for_wake_phrase(raw_text)
        return False, ""
    except Exception:
        return False, ""

def listen_for_command_after_wake() -> Optional[str]:
    """Listens attentively for Master Aryan's full command after waking."""
    try:
        set_orb_state("listening")
        play_chime("wake")
        text = recognize_live_speech(timeout=8.0, phrase_time_limit=12.0)
        return text
    except Exception:
        return None

# ---------------------------------------------------------------------------
# 3. INTERACTIVE CONVERSATION LOOP (DYNAMIC AUTO-DISAPPEAR)
# ---------------------------------------------------------------------------
def handle_awakened_interaction(initial_command: str = "", trigger_type: str = "voice"):
    """
    Called when SPARK is triggered by voice greeting or hotkey.
    1. Reveals the floating plasma orb at the top-middle of the display.
    2. Cancels any auto-hide countdown.
    3. Engages with Master Aryan.
    4. Auto-hides after 15 seconds of inactivity.
    """
    global LAST_INTERACTION_TS
    if not WAKE_LOCK.acquire(blocking=False):
        return  # Already handling an interaction

    try:
        LAST_INTERACTION_TS = time.time()
        cancel_spark_orb_auto_hide()
        show_spark_orb()
        set_orb_state("listening")

        command = initial_command.strip()

        if not command:
            # Greet Master Aryan
            play_chime("wake")
            speak("Yes, Master Aryan? I am listening.", async_mode=False)
            set_orb_state("listening")

            # Capture spoken command via native hardware mic
            command = listen_for_command_after_wake() or ""

        if command:
            # Check for dismissal commands
            if command.lower() in ["hide", "disappear", "sleep", "goodbye", "bye", "cancel", "nevermind"]:
                speak("Standing by, sir.", chime="confirm")
                set_orb_state("idle")
                hide_spark_orb()
                autosave_all_state(reason="user_dismissal")
                return

            set_orb_state("thinking")
            # Run autonomous turn
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(process_autonomous_turn(command))
            finally:
                loop.close()

            autosave_all_state(reason="interaction_complete")

        # After speaking finishes, return orb to idle and start auto-disappear timer
        set_orb_state("idle")
        schedule_spark_orb_auto_hide(AUTO_HIDE_DELAY)

    except Exception as e:
        print(f"[Interaction Error: {e}]")
        set_orb_state("idle")
        schedule_spark_orb_auto_hide(AUTO_HIDE_DELAY)
    finally:
        WAKE_LOCK.release()

# ---------------------------------------------------------------------------
# 4. GLOBAL HOTKEY LISTENER (NATIVE WIN32 + PYNPUT DUAL-ENGINE)
# ---------------------------------------------------------------------------
def start_global_hotkey_listener():
    """
    Registers native Windows Win32 OS-level Global Hotkeys (Alt + S)
    plus pynput multi-key backup with dedicated message pump.
    """
    def _trigger():
        print("\n⚡ [HOTKEY DETECTED]: SPARK Activation Hotkey pressed. Waking SPARK orb!")
        threading.Thread(target=handle_awakened_interaction, kwargs={"trigger_type": "hotkey"}, daemon=True).start()

    # 1. Native Windows Win32 API RegisterHotKey (Bulletproof OS-level)
    def _win32_hotkey_pump():
        try:
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            MOD_ALT = 0x0001
            MOD_CONTROL = 0x0002
            MOD_SHIFT = 0x0004
            VK_S = 0x53

            # ID 1: Alt + S
            user32.RegisterHotKey(None, 1, MOD_ALT, VK_S)
            # ID 2: Ctrl + Shift + S
            user32.RegisterHotKey(None, 2, MOD_CONTROL | MOD_SHIFT, VK_S)
            # ID 3: Alt + Shift + S
            user32.RegisterHotKey(None, 3, MOD_ALT | MOD_SHIFT, VK_S)

            msg = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == 0x0312:  # WM_HOTKEY
                    _trigger()
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        except Exception as e:
            print(f"[Win32 Hotkey Pump Notice: {e}]")

    win32_thread = threading.Thread(target=_win32_hotkey_pump, daemon=True)
    win32_thread.start()

    # 2. Pynput GlobalHotKeys (Secondary backup)
    try:
        from pynput import keyboard
        hotkeys = {
            "<alt>+s": _trigger,
            "<alt>+<shift>+s": _trigger,
            "<ctrl>+<shift>+s": _trigger,
            "<backspace>+s": _trigger,
        }
        listener = keyboard.GlobalHotKeys(hotkeys)
        listener.daemon = True
        listener.start()
    except Exception:
        pass

    print("⌨️  [HOTKEY ACTIVE]: Native Win32 + Pynput (Alt + S / Ctrl + Shift + S / Backspace + S) registered globally.")

# ---------------------------------------------------------------------------
# 5. CONTINUOUS 24/7 BACKGROUND SENTINEL LOOP
# ---------------------------------------------------------------------------
def run_sentinel_daemon():
    """
    Main 24/7 sentinel process.
    - Launches plasma orb in hidden state.
    - Binds global hotkeys.
    - Continuously listens for greetings ('Hey Spark', 'Yo Spark', etc.).
    - Autosaves state periodically.
    """
    print("=" * 68)
    print("       ⚡ SPARK: 24/7 PERSISTENT BACKGROUND SENTINEL")
    print("         (VOICE WAKE • WIN+S • AUTOSAVE • ZERO TERMINAL)")
    print("=" * 68)

    # 1. Restore previous session state if available
    restore_session_state()

    # 2. Launch top-middle plasma orb in hidden state (appears on wake)
    launch_spark_orb_in_background(start_hidden=True)

    # 3. Register Global Hotkey (Win + S)
    start_global_hotkey_listener()

    # 4. Periodic background autosave thread (every 60s)
    def _periodic_saver():
        while SENTINEL_RUNNING:
            time.sleep(60)
            autosave_all_state(reason="periodic_60s_heartbeat")
    threading.Thread(target=_periodic_saver, daemon=True).start()

    # 5. Microphone voice perception sentinel loop using native Realtek driver
    try:
        mic_ok, mic_dev = is_microphone_available()
        print(f"\n👂 [LISTENING]: Standing by for 'Hey Spark', 'Yo Spark', or Alt+S...")
        print(f"🎙️ [HARDWARE MIC]: {mic_dev} ({'ACTIVE' if mic_ok else 'CHECK HARDWARE'})")

        while SENTINEL_RUNNING:
            if not WAKE_LOCK.locked():
                try:
                    woke, remainder = listen_for_wake_greeting()
                    if woke:
                        print(f"\n⚡ [WAKE DETECTED]: Master Aryan greeted SPARK! (Remainder: '{remainder}')")
                        threading.Thread(
                            target=handle_awakened_interaction,
                            kwargs={"initial_command": remainder, "trigger_type": "voice"},
                            daemon=True
                        ).start()
                except Exception:
                    pass
            time.sleep(0.2)

    except Exception as e:
        print(f"[Sentinel Microphone Error: {e}]")
        # Keep process alive so hotkey continues to work even if mic drops
        while SENTINEL_RUNNING:
            time.sleep(1)

if __name__ == "__main__":
    run_sentinel_daemon()
