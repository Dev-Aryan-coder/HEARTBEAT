# 💓 HEARTBEAT

> **Biological AI Memory — Your thoughts, remembered forever.**

HEARTBEAT is a premium, localized AI memory system engineered to function like a living biological brain. It doesn't just respond to your prompts; it metabolizes your conversations into permanent, searchable "Memory Cells" that circulate in real-time. HEARTBEAT provides an everlasting context window, granting you an AI companion that grows, learns, and perfectly remembers every detail about you.

---

## 🧬 **The Core Idea**

Traditional AI chatbots suffer from global amnesia the moment a session ends. HEARTBEAT permanently solves this by actively extracting concepts, facts, and sentiments from every interaction, routing them through a multi-stage **Intelligence Pipeline**.

1. **The L1 Sieve:** Rapidly categorizes incoming thoughts and filters out noise.
2. **The Ambiguity Detector:** Clarifies missing context before committing anything to memory.
3. **The Cell Generator:** Synthesizes raw data into immutable `Memory Cells` (Vector Embeddings + Metadata).
4. **The Nervous System:** Streams live telemetry back to the dashboard, letting you physically watch your AI brain form memories in real-time.

---

## ⚡ **Key Features**

*   **Real-time Cellular Dashboard:** A professional, three-column UI reminiscent of Claude or ChatGPT, but heavily upgraded. Watch your `Active Cells` pulsate and circulate in the telemetry panel as the AI thinks.
*   **3-Level Answer Depth Synthesis:** Tailor your AI's recall on-the-fly. Choose between **Summary** (Quick overview), **Detail** (Comprehensive synthesis), or **Original** (Exact retrieval) under every AI response.
*   **Persistent Neural Storage:** Unbounded long-term memory powered by Local Vector Databases (ChromaDB) and Relational Storage (SQLite).
*   **Clarification Loops:** If HEARTBEAT detects an ambiguous pronoun or statement, it triggers a specialized UI banner to ask for clarification, ensuring high-fidelity memories.
*   **Local-First Design & OCR:** Secure privacy limits by processing state and images locally using `pytesseract`, while firing rapid logical deductions via Groq's high-speed API.

---

## 🏗️ **The Technology Stack**

HEARTBEAT is meticulously engineered for high-performance scale and raw speed.

### **Backend (The Core Brain)**
*   **Language:** Python 3.10+
*   **API Framework:** FastAPI (Serving as the high-speed *Artery*)
*   **Real-time Telemetry:** WebSockets (Serving as the *Nervous System*)
*   **LLM Inference Engine:** Groq API (Primary routing for ultra-low latency), OpenRouter (Fallback API)
*   **Vector Embeddings:** `sentence-transformers` (Local generation)

### **Storage (The Hippocampus)**
*   **Semantic Memory:** ChromaDB (Vector database for similarity searches and RAG mechanics)
*   **Relational Backbone:** SQLite (Pydantic v2 schemas for tracking cell scores, topics, and session history)

### **Processing & Integrations (Sensory Organs)**
*   **Image Processing:** `Pillow` and `pytesseract` (Local OCR pipeline)
*   **NLP Utilities:** `nltk` for chunking and lexical analysis

### **Frontend (The Neural Dashboard)**
*   **Structure:** Vanilla HTML5 
*   **Styling:** Custom CSS3 with CSS Variables, Flexbox/Grid, and Premium Micro-animations
*   **Logic:** Vanilla ES6+ JavaScript, `localStorage` state persistence, native fetch APIs, and raw `WebSocket` listeners.

### **Testing & CI/CD**
*   **Framework:** `pytest` with `unittest.mock`

---

## 🚀 **Getting Started**

### 1. **Prerequisites**
*   Python 3.10+
*   Tesseract-OCR installed on your system
*   A Groq API key (and optionally an OpenRouter key)

### 2. **Installation**
Clone the repository and install the biological dependencies:
```bash
pip install fastapi uvicorn pydantic python-dotenv chromadb sentence-transformers pillow pytesseract nltk groq httpx pytest redis
```

### 3. **Environment Setup**
Create a `.env` file in the root directory:
```env
# .env
HEARTBEAT_BRAIN_KEY=your_groq_api_key_here
HEARTBEAT_OPENROUTER_KEY=fallback_key_here
```

### 4. **Ignite the System**
*   **Start the Artery (Backend):**
    ```powershell
    $env:PYTHONPATH="."; python main.py
    ```
    *The server runs locally on `http://127.0.0.1:8000`*

*   **Launch the Dashboard:**
    Double-click `ui/index.html` or run it via Microsoft Edge/Chrome. Enjoy a seamless, living UI capable of managing unbounded conversations.

---

> **“The real magic of intelligence is not in the generation of text, but in the permanent formation of memories.”** 
