import urllib.request
import json
from datetime import datetime

def get_current_time():
    return datetime.now().strftime("%A, %B %d, %Y at %I:%M:%S %p")

def get_system_vitals():
    import psutil
    cpu = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory()
    battery = psutil.sensors_battery()
    bat_str = f"{battery.percent}% ({'Plugged in' if battery.power_plugged else 'On Battery'})" if battery else "Desktop/AC"
    return f"CPU: {cpu}%, RAM Used: {ram.used // (1024**2)}MB / {ram.total // (1024**2)}MB ({ram.percent}%), Battery: {bat_str}"

tools_def = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Returns the exact real-time current date, time, and day of the week on Master Aryan's system.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_vitals",
            "description": "Returns actual hardware vitals including CPU usage, RAM utilization, and battery status.",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]

def run_test():
    messages = [
        {"role": "system", "content": "You are JARVIS, Master Aryan's personal AI majordomo and autonomous assistant. You have live tools to inspect and control the computer. When asked for real-world or hardware information, invoke the necessary tool. Be concise, respectful, and dignified."},
        {"role": "user", "content": "Jarvis, what is the exact time and how are my laptop vitals looking right now?"}
    ]

    req_data = {
        "model": "qwen2.5:3b",
        "messages": messages,
        "tools": tools_def,
        "stream": False
    }

    req = urllib.request.Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps(req_data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        res = json.loads(resp.read().decode("utf-8"))

    msg = res["message"]
    print("\n--- MODEL STEP 1 (THOUGHT / TOOL CALLS) ---")
    print(json.dumps(msg, indent=2))

    if msg.get("tool_calls"):
        messages.append(msg)
        for tc in msg["tool_calls"]:
            fn_name = tc["function"]["name"]
            if fn_name == "get_current_time":
                obs = get_current_time()
            elif fn_name == "get_system_vitals":
                obs = get_system_vitals()
            else:
                obs = f"Unknown tool: {fn_name}"

            print(f"\n[EXECUTING REAL OS TOOL] {fn_name} -> {obs}")
            messages.append({
                "role": "tool",
                "content": obs
            })

        req_data["messages"] = messages
        req2 = urllib.request.Request(
            "http://127.0.0.1:11434/api/chat",
            data=json.dumps(req_data).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req2, timeout=30) as resp2:
            res2 = json.loads(resp2.read().decode("utf-8"))

        print("\n--- MODEL STEP 2 (FINAL SYNTHESIZED RESPONSE) ---")
        final_text = res2["message"]["content"]
        print(final_text)

if __name__ == "__main__":
    run_test()
