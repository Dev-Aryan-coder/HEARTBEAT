# ⚡ Project SPARK: The Blueprint to a Real JARVIS
*An Engineering Implementation Plan for Master Aryan*

---

## 🌟 What Does a "Real JARVIS" Actually Look Like?

In the movies, Tony Stark doesn't click buttons or write code. He simply speaks to JARVIS in plain English:
> *"JARVIS, create a new simulation, pull up the schematics, and notify me when the render is complete."*

To make **SPARK** do this in the real world on your Windows laptop, SPARK must have **4 Pillars**:
1. **The Ears & Voice**: Hear you accurately, speak naturally, and stop talking instantly if you interrupt.
2. **The Memory Core (HEARTBEAT)**: Remember conversations from yesterday, your preferences, and past files.
3. **The Multi-Step Brain (Metacognition)**: Break big instructions into small steps, and fix its own mistakes if something fails.
4. **The Infinite Hands (Dynamic Execution)**: Never say *"I don't know how to do that"*. If a tool doesn't exist, SPARK writes and runs a Python script on the fly to get it done.

```mermaid
graph TD
    User([🗣️ Master Aryan]) -->|Speaks Command| Ears[🎤 Voice & Intent Listener]
    Ears --> Brain[🧠 SPARK Brain: Qwen / Nemotron]
    
    Brain <--> Memory[(🧬 HEARTBEAT Memory: Recalls Context & Preferences)]
    
    Brain --> Decision{Can Native Tools Do It?}
    
    Decision -->|Yes: Instant Speed| FastRoute[⚡ Route 1: Fast Reflexes\nVolume, Screenshot, Battery, Processes]
    Decision -->|No: Infinite Scalability| DynamicRoute[🛠️ Route 2: Dynamic Code Generator\nWrites Python on the fly for Word, Excel, Apps, Web]
    
    DynamicRoute --> Exec[⚙️ Safe Local Subprocess Runner]
    Exec --> Feedback[📋 Execution Feedback & Self-Correction]
    Feedback -->|If error occurs| Brain
    
    FastRoute --> Voice[🔊 SAPI5 / Neural Voice Speaker]
    Exec --> Voice
    Voice --> User
```

---

## 🏗️ Phase 1: The Infinite Hands (Dynamic Code Execution)
**Goal:** Give SPARK the power to perform **any** laptop task without hardcoding.

### 1.1 The Two Routes
* **Route 1 (Fast Reflexes)**:
  * For common actions like changing the volume, muting, getting battery status, taking a screenshot, or listing processes.
  * Runs in **under 50 milliseconds** because it uses pre-written Python functions.
* **Route 2 (Dynamic Automation Fallback)**:
  * For unique requests (e.g., *"Open Word and write a letter"*, *"Extract all ZIP files in Downloads"*, *"Make an Excel sheet for my daily budget"*).
  * SPARK writes a fresh, standalone Python script, saves it to `spark_dynamic_execution.py`, runs it via Windows subprocess, reads the output, and deletes the temporary script.

### 1.2 Self-Installing Abilities (Zero-Crash Fallback)
If SPARK needs a special library that is not installed on your laptop (for example, `python-docx` for Word or `openpyxl` for Excel), the script SPARK writes will automatically install it first:
```python
try:
    import docx
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-docx"])
    import docx
```
This guarantees SPARK **never crashes** just because a library was missing.

### 1.3 Safety Guardrails (The Jarvis Shield)
To ensure SPARK is safe and never harms your system:
* Blacklist dangerous commands (e.g., deleting system files like `C:\Windows\System32` or formatting drives).
* Run every script with a strict **45-second timeout** so it never hangs or freezes your computer.

### 1.4 🧠 Skill Crystallization (Self-Expanding Skills Library)
*Master Aryan's Key Insight: Never re-invent the wheel twice.*
* **First Time**: You ask for a new task (e.g. *"Write a report in Word"*). SPARK dynamically writes and executes the script.
* **Crystallization**: Once the script runs successfully, SPARK saves the function into a dedicated `skills/` library (e.g., `skills/word_toolkit.py`).
* **Second Time & Beyond**: Next time you say *"Write in Word"*, SPARK does **not** need to generate code from scratch! It immediately imports its tested skill, passes your new text as arguments, and finishes in **milliseconds**.
* **Result**: SPARK literally **learns new tools over time**. The more you use it, the smarter, faster, and more capable it becomes!


---

## 🧬 Phase 2: The Living Memory Core (HEARTBEAT)
**Goal:** Make sure SPARK never forgets what you told him yesterday, last week, or 10 minutes ago.

### 2.1 The 3-Tier Storage Hierarchy
1. **Tier 1 (Instant Working Memory - RAM)**:
   * Uses the `LRUMemoryCache` and `PrefixTrie` we built to find recent notes, active file names, and conversation context in **0.1 milliseconds**.
2. **Tier 2 (Long-Term Episodic Memory - SQLite)**:
   * Every conversation, tool execution, and user preference is permanently logged in `storage/heartbeat_memory.db`.
3. **Tier 3 (Subconscious Vector Association - ChromaDB)**:
   * Uses semantic embeddings (`all-MiniLM-L6-v2`) so if you say:
     > *"Spark, where did we put that draft about the college project?"*
     Even if you don't say the exact filename, SPARK understands the meaning and finds it.

### 2.2 Synaptic Priming (Learning Your Habits)
When you ask SPARK to do something repeatedly (e.g., opening a specific folder every morning or playing your favorite music), the biological Hebbian synapses strengthen. SPARK will start anticipating what you need before you even ask.

---

## 🧩 Phase 3: The Multi-Step Brain (Task DAG & Self-Healing)
**Goal:** Handle complex, multi-stage requests and fix its own errors.

### 3.1 Breaking Big Tasks into Steps (Task Execution DAG)
If you give a big command:
> *"SPARK, take a screenshot of my screen, save it to my desktop, and summarize the active window in a text file."*

SPARK doesn't try to guess everything at once. It creates an internal **Directed Acyclic Graph (DAG)**:
* **Step 1**: Call `take_screenshot` → Save to desktop.
* **Step 2**: Read active window title via Win32.
* **Step 3**: Call `write_workspace_file` with the summary.
* **Step 4**: Announce completion to Master Aryan.

### 3.2 Self-Healing Loop (Autonomous Debugging)
If SPARK generates a script that fails (for example, a typo in a file path or a blocked window):
1. SPARK captures the error message (`stderr`).
2. SPARK feeds the error back into its own brain: *"That failed because the file path had spaces. Let me fix the quotes and try again."*
3. It fixes the script and reruns it automatically **without asking you to fix the code**.

---

## 🎙️ Phase 4: Voice & Speech Presence
**Goal:** Fast, smooth vocal interaction worthy of JARVIS.

1. **Low-Latency Speech Recognition**:
   * Uses microphone threshold tuning so SPARK doesn't miss words or cut you off mid-sentence.
2. **Native Speech Engine (SAPI5 / Neural TTS)**:
   * Zero cloud lag. Speaks locally through your laptop speakers instantly.
3. **Barge-In (Interruption Detection)**:
   * If SPARK is speaking a long sentence and you say *"Stop"* or start giving a new order, SPARK cuts off speech immediately and listens to you.

---

## 📅 Step-by-Step Implementation Roadmap

| Step | Action | Files Touched | Expected Outcome |
| :--- | :--- | :--- | :--- |
| **1** | **Implement Dynamic Code Actuator** | `spark_voice_assistant.py` | Add `tool_execute_dynamic_automation` with subprocess bridge & cleanup. |
| **2** | **Update Tool Schemas & Dispatcher** | `spark_voice_assistant.py` | Expose the fallback tool to Qwen / Ollama and map it into `TOOL_DISPATCHER`. |
| **3** | **Cognitive Priority Prompt Re-alignment** | `spark_voice_assistant.py` | Teach SPARK to use Route 1 (Native) first and Route 2 (Dynamic Code) as universal fallback. |
| **4** | **Self-Correction & Feedback Loop** | `spark_voice_assistant.py` | If dynamic code fails, allow SPARK one retry attempt with the error log. |
| **5** | **Live Global Test Verification** | Live System Test | Test 1 native task (Volume) + 1 dynamic arbitrary task (Word doc creation on Desktop). |

---

## 🎯 Verification Criteria: How We Know It Works 100%
1. **Scenario A (Native Route)**: *"SPARK, set system volume to 35%"* → Executes directly in < 50ms without generating any script.
2. **Scenario B (Dynamic Arbitrary Route)**: *"SPARK, create a Word file named 'Jarvis_Report.docx' on my Desktop and write 'Autonomous system operational' inside."* → SPARK generates code on the fly, auto-installs `docx` if needed, creates the file, opens it on screen, and announces success.
3. **Scenario C (Memory Recall)**: *"SPARK, what did we just create?"* → Pulls the memory from HEARTBEAT and answers accurately.
