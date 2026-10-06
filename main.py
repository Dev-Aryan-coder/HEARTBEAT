import sys
print("💓 [HEARTBEAT] Initializing system...", flush=True)
print("⏳ Loading AI & Neural Models (takes ~15-20s on Windows)...", flush=True)

import uvicorn, os
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from api.websocket import websocket_endpoint
from storage.database import init_database
from heartbeat.config import get_config
from heart.metabolism import start_metabolism
from api.middleware import RateLimitMiddleware

app = FastAPI(title="Heartbeat Intelligence API")

# ISSUE 4.1 FIX: Restricted CORS to prevent unauthorized cross-origin requests
# Replace '*' with specific origins in production
ALLOWED_ORIGINS = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:5501",
    "http://127.0.0.1:5501",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "null"
]

app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=60
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register core routes
app.include_router(router)

# Mount UI for direct browser access
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

if os.path.exists("ui"):
    app.mount("/ui", StaticFiles(directory="ui", html=True), name="ui")

img_dir = os.path.join("data", "images")
os.makedirs(img_dir, exist_ok=True)
app.mount("/images", StaticFiles(directory=img_dir), name="images")

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/ui/")

# Register Live WebSocket Monitor
@app.websocket("/ws/connect/{user_id}")
async def websocket_route(websocket: WebSocket, user_id: str):
    await websocket_endpoint(websocket, user_id)

@app.on_event("startup")
async def startup_event():
    print("--- Initializing Heartbeat AI ---")
    
    # 0. Create data directory for isolation
    if not os.path.exists("data"):
        os.makedirs("data")
    
    # 1. Validate Config (API Keys)
    config = get_config()
    if not config.brain_key:
        print("⚠️ Warning: HEARTBEAT_BRAIN_KEY not found in .env")
    
    # 2. Init SQLite Tables (Relational Bones)
    init_database()
    print("✅ Heartbeat Database Ready.")
    
    # 3. Pre-warm the embedding model so it never loads mid-conversation
    print("🧠 Pre-loading embedding model... (one-time warmup)")
    from heart.topic_shift_detector import load_embedding_model
    load_embedding_model()
    print("✅ Embedding Model Ready. (No more mid-chat loading bars)")
    
    # 4. Start the Heart Metabolism background job (11. Automated Decay)
    start_metabolism()
    print("🧬 Heart Metabolism Thread Active.")
    
    # 5. Server Ready Notification
    print("\n[LIVE] Heartbeat running at http://0.0.0.0:8000")
    print("View Docs: http://localhost:8000/docs")


if __name__ == "__main__":
    # STABILITY LOCK: 
    # We disable reload=True because database writes and vector-store updates 
    # in the 'data/' folder were triggering recursive restart loops.
    # This ensures a 100% stable connection during your demo.
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=False
    )
