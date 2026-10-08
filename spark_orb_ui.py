"""
=============================================================================
⚡ SPARK FLOATING ORB UI (SIRI-STYLE DYNAMIC PLASMA SPARK)
=============================================================================
A frameless, transparent, always-on-top desktop orb floating at the top-middle
of Master Aryan's screen, featuring live fractal lightning & electric plasma
sparks that undulate and pulse in real-time like Siri / Tony Stark's JARVIS.

States:
- 'idle': Calm breathing purple plasma tendrils.
- 'listening': Energetic cyan & electric blue lightning pulses.
- 'thinking': High-frequency rotating electrical vortex.
- 'speaking': Vibrant multi-branching electric storm responding to vocal cadence.
=============================================================================
"""

import os
import sys
import math
import time
import random
import threading
import tkinter as tk
from typing import List, Tuple

class SparkOrbWidget:
    def __init__(self, size: int = 160, start_hidden: bool = False):
        self.size = size
        self.radius = (size - 20) // 2
        self.center_x = size // 2
        self.center_y = size // 2
        self.state = "idle"  # idle, listening, thinking, speaking
        self.running = True
        self.is_visible = not start_hidden
        self._auto_hide_after_id = None
        self.angle_offset = 0.0
        self.pulse_phase = 0.0

        # Create frameless, transparent top-level window
        self.root = tk.Tk()
        self.root.title("SPARK Neural Orb")
        self.root.overrideredirect(True)      # Frameless
        self.root.wm_attributes("-topmost", True)  # Always on top

        # Windows Transparent Color Key
        self.transparent_key = "#010101"
        self.root.wm_attributes("-transparentcolor", self.transparent_key)
        self.root.config(bg=self.transparent_key)

        if start_hidden:
            self.root.withdraw()

        # Position at the top-middle of primary display
        screen_w = self.root.winfo_screenwidth()
        x_pos = (screen_w - size) // 2
        y_pos = 12  # Sleek top margin
        self.root.geometry(f"{size}x{size}+{x_pos}+{y_pos}")

        # Canvas for hardware-accelerated drawing
        self.canvas = tk.Canvas(
            self.root,
            width=size,
            height=size,
            bg=self.transparent_key,
            highlightthickness=0,
            bd=0
        )
        self.canvas.pack(fill="both", expand=True)

        # Enable smooth dragging with mouse
        self._drag_data = {"x": 0, "y": 0}
        self.canvas.bind("<ButtonPress-1>", self._start_drag)
        self.canvas.bind("<B1-Motion>", self._do_drag)
        self.canvas.bind("<Double-Button-1>", self._cycle_state)
        self.canvas.bind("<Button-3>", self._show_menu)

        # Lightning bolt memory
        self.lightning_tendrils: List[List[Tuple[float, float]]] = []

        # Start render animation loop (~30-40 FPS)
        self._animate()

    def _start_drag(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _do_drag(self, event):
        deltax = event.x - self._drag_data["x"]
        deltay = event.y - self._drag_data["y"]
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def _cycle_state(self, event=None):
        states = ["idle", "listening", "thinking", "speaking"]
        idx = (states.index(self.state) + 1) % len(states)
        self.set_state(states[idx])

    def _show_menu(self, event):
        menu = tk.Menu(self.root, tearoff=0, bg="#1a1c23", fg="#ffffff", activebackground="#7c3aed")
        menu.add_command(label="⚡ State: Idle", command=lambda: self.set_state("idle"))
        menu.add_command(label="🎙️ State: Listening", command=lambda: self.set_state("listening"))
        menu.add_command(label="🧠 State: Thinking", command=lambda: self.set_state("thinking"))
        menu.add_command(label="🔊 State: Speaking", command=lambda: self.set_state("speaking"))
        menu.add_separator()
        menu.add_command(label="Center at Top", command=self.reset_to_top)
        menu.add_command(label="Close Orb", command=self.close)
        menu.post(event.x_root, event.y_root)

    def reset_to_top(self):
        screen_w = self.root.winfo_screenwidth()
        x_pos = (screen_w - self.size) // 2
        self.root.geometry(f"{self.size}x{self.size}+{x_pos}+12")

    def show_orb(self):
        """Thread-safe reveal of the plasma orb window at top-center."""
        def _show():
            self.reset_to_top()
            self.root.deiconify()
            self.root.wm_attributes("-topmost", True)
            self.is_visible = True
        self.root.after(0, _show)

    def hide_orb(self):
        """Thread-safe concealment of the plasma orb window."""
        def _hide():
            self.root.withdraw()
            self.is_visible = False
        self.root.after(0, _hide)

    def toggle_orb(self):
        """Thread-safe visibility toggle."""
        if self.is_visible:
            self.hide_orb()
        else:
            self.show_orb()

    def schedule_auto_hide(self, seconds: float = 15.0):
        """Schedules the orb to automatically disappear after `seconds` of inactivity."""
        def _do_schedule():
            self.cancel_auto_hide()
            ms = int(seconds * 1000)
            def _auto_hide():
                self.hide_orb()
                self._auto_hide_after_id = None
            self._auto_hide_after_id = self.root.after(ms, _auto_hide)
        self.root.after(0, _do_schedule)

    def cancel_auto_hide(self):
        """Cancels any pending auto-hide timer."""
        if self._auto_hide_after_id:
            try:
                self.root.after_cancel(self._auto_hide_after_id)
            except Exception:
                pass
            self._auto_hide_after_id = None

    def set_state(self, new_state: str):
        if new_state in ("idle", "listening", "thinking", "speaking"):
            self.state = new_state

    def _generate_lightning_branch(self, start_x: float, start_y: float, target_angle: float, length: float, jitter: float) -> List[Tuple[float, float]]:
        """Generates fractal electrical lightning points branching outwards from the core."""
        steps = random.randint(6, 12)
        points = [(start_x, start_y)]
        curr_x, curr_y = start_x, start_y
        step_len = length / steps

        for _ in range(steps):
            angle = target_angle + random.uniform(-jitter, jitter)
            curr_x += math.cos(angle) * step_len
            curr_y += math.sin(angle) * step_len
            points.append((curr_x, curr_y))
        return points

    def _draw_glowing_circle(self, cx: float, cy: float, r: float, color: str, width: int = 1):
        self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=color, width=width)

    def _animate(self):
        self.canvas.delete("all")
        cx, cy = self.center_x, self.center_y
        base_r = self.radius

        # Pulse breathing modulation
        self.pulse_phase += 0.08
        pulse = math.sin(self.pulse_phase)
        current_r = base_r + pulse * (4 if self.state != "speaking" else 8)

        # Color schemes based on cognitive state
        if self.state == "idle":
            # Purple / Violet plasma (matches user's reference lightning)
            halo_color = "#3b0764"       # Deep dark violet
            outer_ring = "#7e22ce"       # Electric purple
            spark_primary = "#a855f7"    # Bright violet
            spark_bright = "#e9d5ff"     # Lavender glow
            core_color = "#ffffff"       # White-hot nucleus
            num_branches = random.randint(4, 7)
            length_factor = 0.85
            jitter = 0.55
        elif self.state == "listening":
            # Cyan & Electric Blue (attentive listening)
            halo_color = "#083344"
            outer_ring = "#06b6d4"
            spark_primary = "#22d3ee"
            spark_bright = "#a5f3fc"
            core_color = "#ffffff"
            num_branches = random.randint(7, 12)
            length_factor = 0.95
            jitter = 0.4
        elif self.state == "thinking":
            # Rotating Magenta & Blue vortex
            halo_color = "#4c0519"
            outer_ring = "#e11d48"
            spark_primary = "#fb7185"
            spark_bright = "#fbcfe8"
            core_color = "#ffffff"
            num_branches = random.randint(8, 14)
            length_factor = 0.9
            jitter = 0.65
        else: # speaking
            # Supercharged Electric Arc Storm
            halo_color = "#2e1065"
            outer_ring = "#9333ea"
            spark_primary = "#c084fc"
            spark_bright = "#f3e8ff"
            core_color = "#ffffff"
            num_branches = random.randint(12, 18)
            length_factor = 1.05
            jitter = 0.7

        # 1. Outer Dark Diffusion Sphere (Subtle containment orb)
        self.canvas.create_oval(
            cx - current_r, cy - current_r, cx + current_r, cy + current_r,
            fill="#0f0728", outline=halo_color, width=2
        )

        # 2. Outer Glowing Rings
        self._draw_glowing_circle(cx, cy, current_r, outer_ring, width=2)
        self._draw_glowing_circle(cx, cy, current_r * 0.92, spark_primary, width=1)

        # 3. Dynamic Fractal Lightning Sparks (branching out from central nucleus)
        self.angle_offset += (0.05 if self.state != "thinking" else 0.15)
        for i in range(num_branches):
            base_angle = (i * (2 * math.pi / num_branches)) + self.angle_offset + random.uniform(-0.15, 0.15)
            branch_len = current_r * length_factor * random.uniform(0.7, 1.0)
            
            # Sub-core starting offset
            core_offset = random.uniform(2, 8)
            sx = cx + math.cos(base_angle) * core_offset
            sy = cy + math.sin(base_angle) * core_offset

            pts = self._generate_lightning_branch(sx, sy, base_angle, branch_len, jitter)
            
            # Draw outer glow stroke
            flat_pts = [coord for pt in pts for coord in pt]
            if len(flat_pts) >= 4:
                self.canvas.create_line(flat_pts, fill=spark_primary, width=2, smooth=False)
                self.canvas.create_line(flat_pts, fill=spark_bright, width=1, smooth=False)

                # Occasional fork branching
                if random.random() > 0.4 and len(pts) > 4:
                    fork_start = pts[len(pts) // 2]
                    fork_pts = self._generate_lightning_branch(fork_start[0], fork_start[1], base_angle + random.choice([-0.8, 0.8]), branch_len * 0.45, 0.5)
                    flat_fork = [c for p in fork_pts for c in p]
                    if len(flat_fork) >= 4:
                        self.canvas.create_line(flat_fork, fill=spark_bright, width=1)

        # 4. Central Glowing Arc Reactor Nucleus (Pulsing bright white-violet core)
        core_r = random.uniform(7, 11) + (pulse * 2 if self.state == "speaking" else 0)
        # Inner aura
        self.canvas.create_oval(cx - core_r * 1.6, cy - core_r * 1.6, cx + core_r * 1.6, cy + core_r * 1.6, fill=spark_primary, outline="")
        self.canvas.create_oval(cx - core_r * 1.2, cy - core_r * 1.2, cx + core_r * 1.2, cy + core_r * 1.2, fill=spark_bright, outline="")
        # White hot spark center
        self.canvas.create_oval(cx - core_r, cy - core_r, cx + core_r, cy + core_r, fill=core_color, outline="")

        if self.running:
            # 30 ms interval = ~33 FPS fluid electric animation
            self.root.after(30, self._animate)

    def close(self):
        self.running = False
        try:
            self.root.destroy()
        except Exception:
            pass

    def run(self):
        self.root.mainloop()

_GLOBAL_ORB_INSTANCE = None

def launch_spark_orb_in_background(start_hidden: bool = False):
    """Launches the SPARK floating orb in a dedicated thread so it never blocks the voice assistant."""
    global _GLOBAL_ORB_INSTANCE
    if _GLOBAL_ORB_INSTANCE is not None:
        if not start_hidden:
            _GLOBAL_ORB_INSTANCE.show_orb()
        return _GLOBAL_ORB_INSTANCE

    def _runner():
        global _GLOBAL_ORB_INSTANCE
        orb = SparkOrbWidget(size=160, start_hidden=start_hidden)
        _GLOBAL_ORB_INSTANCE = orb
        orb.run()

    t = threading.Thread(target=_runner, daemon=True)
    t.start()
    time.sleep(0.5)
    return _GLOBAL_ORB_INSTANCE

def set_orb_state(state: str):
    """Sets the visual animated state: 'idle', 'listening', 'thinking', 'speaking'."""
    global _GLOBAL_ORB_INSTANCE
    if _GLOBAL_ORB_INSTANCE:
        _GLOBAL_ORB_INSTANCE.set_state(state)

def show_spark_orb():
    """Reveals the top-center floating plasma orb."""
    global _GLOBAL_ORB_INSTANCE
    if _GLOBAL_ORB_INSTANCE:
        _GLOBAL_ORB_INSTANCE.show_orb()

def hide_spark_orb():
    """Conceals the floating plasma orb."""
    global _GLOBAL_ORB_INSTANCE
    if _GLOBAL_ORB_INSTANCE:
        _GLOBAL_ORB_INSTANCE.hide_orb()

def is_spark_orb_visible() -> bool:
    """Returns True if the orb is currently visible on screen."""
    global _GLOBAL_ORB_INSTANCE
    return _GLOBAL_ORB_INSTANCE.is_visible if _GLOBAL_ORB_INSTANCE else False

def schedule_spark_orb_auto_hide(seconds: float = 15.0):
    """Schedules the orb to automatically disappear after `seconds` of silence."""
    global _GLOBAL_ORB_INSTANCE
    if _GLOBAL_ORB_INSTANCE:
        _GLOBAL_ORB_INSTANCE.schedule_auto_hide(seconds)

def cancel_spark_orb_auto_hide():
    """Cancels auto-hide timer if user speaks or interacts."""
    global _GLOBAL_ORB_INSTANCE
    if _GLOBAL_ORB_INSTANCE:
        _GLOBAL_ORB_INSTANCE.cancel_auto_hide()

if __name__ == "__main__":
    print("⚡ Launching SPARK Siri-style Plasma Orb at top-middle of screen...")
    print("Controls:")
    print(" - Drag anywhere on screen with Left Mouse Button")
    print(" - Double-click to cycle states (Idle -> Listening -> Thinking -> Speaking)")
    print(" - Right-click for menu")
    orb = SparkOrbWidget(size=160)
    orb.run()
