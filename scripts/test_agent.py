import httpx
import asyncio
import sqlite3
import json
import time
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_BASE = "http://127.0.0.1:8000"
TEST_USER_ID = "TEST_AGENT_USER"
TEST_SESSION = "agent_test_session"

# Colors for terminal output
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

results = []  # stores all test results

def log(emoji, label, status, detail=""):
    color = GREEN if status == "PASS" else RED if status == "FAIL" else YELLOW
    print(f"{color}{emoji} [{status}] {label}{RESET}")
    if detail:
        print(f"       {CYAN}{detail}{RESET}")
    results.append({"label": label, "status": status, "detail": detail})

# ── TEST 1: SERVER HEALTH CHECK ───────────────────────────────────────────────

async def test_server_health():
    print(f"\n{BOLD}{BLUE}━━━ TEST 1: Server Health ━━━{RESET}")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{API_BASE}/api/ping")
            if r.status_code == 200 and r.json().get("status") == "ok":
                log("✅", "Server running on port 8000", "PASS", 
                    f"Response: {r.json()}")
                return True
            else:
                log("❌", "Server health check failed", "FAIL",
                    f"Status: {r.status_code}")
                print(f"{RED}FATAL: Server not running. Start with: python main.py{RESET}")
                sys.exit(1)
    except Exception as e:
        log("❌", "Cannot connect to server", "FAIL", str(e))
        print(f"{RED}FATAL: Run 'python main.py' first then retry{RESET}")
        sys.exit(1)

# ── TEST MESSAGES ─────────────────────────────────────────────────────────────

TEST_MESSAGES = [
    {
        "id": "msg_fact",
        "content": "I am a BSc IT student from Mumbai and I love Python programming",
        "expected_intent": "permanent_fact",
        "expected_l1_pass": True,
        "expected_ambiguous": False,
        "description": "Should create permanent fact cell with high importance"
    },
    {
        "id": "msg_smalltalk", 
        "content": "Hello",
        "expected_intent": "small_talk",
        "expected_l1_pass": False,
        "expected_ambiguous": False,
        "description": "Should be rejected at L1 Sieve as small talk"
    },
    {
        "id": "msg_ambiguous",
        "content": "I really love Apple products and use them daily",
        "expected_intent": "permanent_fact",
        "expected_l1_pass": True,
        "expected_ambiguous": True,
        "description": "Should trigger ambiguity detection for Apple"
    },
    {
        "id": "msg_filler",
        "content": "Um so yeah basically I think Python is good",
        "expected_intent": "permanent_fact", 
        "expected_l1_pass": True,
        "expected_ambiguous": False,
        "description": "Should pass L1 after filler removal, fact extracted"
    },
    {
        "id": "msg_multiintent",
        "content": "Build me a website and also suggest marketing strategies",
        "expected_intent": "command",
        "expected_l1_pass": True,
        "expected_ambiguous": False,
        "description": "Should be split into 2 separate cells by intent splitter"
    },
    {
        "id": "msg_memory_test",
        "content": "My name is Aryan and I am building the HEARTBEAT AI memory system",
        "expected_intent": "permanent_fact",
        "expected_l1_pass": True,
        "expected_ambiguous": False,
        "description": "Core identity fact — should get importance score 8-10"
    }
]

# ── TEST FUNCTIONS ────────────────────────────────────────────────────────────

async def send_test_message(msg_data: dict, chat_id: str) -> dict:
    async with httpx.AsyncClient(timeout=60) as client:
        payload = {
            "user_id": TEST_USER_ID,
            "chat_id": chat_id,
            "session_id": TEST_SESSION,
            "content": msg_data["content"],
            "content_type": "text"
        }
        start_time = time.time()
        r = await client.post(f"{API_BASE}/api/message", json=payload)
        elapsed = round((time.time() - start_time) * 1000)
        
        return {
            "status_code": r.status_code,
            "response": r.json() if r.status_code == 200 else {},
            "elapsed_ms": elapsed,
            "msg_data": msg_data
        }

async def test_l1_sieve(content: str, expected_pass: bool):
    async with httpx.AsyncClient(timeout=30) as client:
        payload = {
            "user_id": TEST_USER_ID,
            "chat_id": "pipeline_test",
            "session_id": "test",
            "content": content
        }
        r = await client.post(
            f"{API_BASE}/api/test/pipeline", json=payload
        )
        if r.status_code != 200:
            return False, f"Pipeline endpoint returned {r.status_code}"
        
        data = r.json()
        l1 = data.get("l1", {})
        passed = l1.get("passed", False)
        cleaned = l1.get("cleaned") or ""
        removed = l1.get("removed") or ""
        
        if passed == expected_pass:
            detail = f"Cleaned: '{cleaned[:60]}...' | Removed: '{removed[:40]}'"
            return True, detail
        else:
            detail = f"Expected pass={expected_pass} but got pass={passed}"
            return False, detail

async def test_l2_valve(content: str, expected_intent: str, 
                         expected_ambiguous: bool):
    async with httpx.AsyncClient(timeout=30) as client:
        payload = {
            "user_id": TEST_USER_ID,
            "chat_id": "pipeline_test", 
            "session_id": "test",
            "content": content
        }
        r = await client.post(
            f"{API_BASE}/api/test/pipeline", json=payload
        )
        data = r.json()
        l2 = data.get("l2")
        
        if l2 is None:
            # L2 was skipped (L1 rejected)
            return True, "L2 correctly skipped (L1 rejected message)"
        
        actual_intent = l2.get("intent_type", "unknown")
        actual_ambiguous = l2.get("is_ambiguous", False)
        splits = l2.get("splits", [])
        
        issues = []
        if actual_intent != expected_intent:
            issues.append(
                f"Intent: expected '{expected_intent}' got '{actual_intent}'"
            )
        if actual_ambiguous != expected_ambiguous:
            issues.append(
                f"Ambiguous: expected {expected_ambiguous} "
                f"got {actual_ambiguous}"
            )
        
        detail = (
            f"Intent: {actual_intent} | "
            f"Ambiguous: {actual_ambiguous} | "
            f"Splits: {len(splits)}"
        )
        if l2.get("clarification_question"):
            detail += f" | Question: {l2['clarification_question'][:60]}"
        
        return len(issues) == 0, detail if not issues else " | ".join(issues)

async def test_l3_purifier(content: str):
    async with httpx.AsyncClient(timeout=60) as client:
        payload = {
            "user_id": TEST_USER_ID,
            "chat_id": "pipeline_test",
            "session_id": "test", 
            "content": content
        }
        r = await client.post(
            f"{API_BASE}/api/test/pipeline", json=payload
        )
        data = r.json()
        l3 = data.get("l3")
        
        if l3 is None:
            return True, "L3 correctly skipped"
        
        checks = []
        issues = []
        
        # Check importance score exists and is valid
        score = l3.get("importance_score")
        if score is not None and 1 <= score <= 10:
            checks.append(f"Score: {score}/10 ✓")
        else:
            issues.append(f"Invalid importance score: {score}")
        
        # Check keywords extracted
        keywords = l3.get("keywords", [])
        if len(keywords) >= 1:
            checks.append(f"Keywords: {keywords[:3]} ✓")
        else:
            issues.append("No keywords extracted")
        
        # Check topic_id assigned
        topic = l3.get("topic_id")
        if topic:
            checks.append(f"Topic: {topic} ✓")
        else:
            issues.append("No topic_id assigned")
        
        # Check summary written
        summary = l3.get("summary", "")
        if len(summary) > 10:
            checks.append(f"Summary: '{summary[:50]}...' ✓")
        else:
            issues.append("Summary too short or missing")
        
        # Check user_content cleaned
        user_content = l3.get("user_content", "")
        if len(user_content) > 5:
            checks.append(f"Cleaned: '{user_content[:50]}...' ✓")
        else:
            issues.append("user_content empty")
        
        detail = " | ".join(checks) if not issues else " | ".join(issues)
        return len(issues) == 0, detail

def test_cell_in_sqlite(cell_id: str = None) -> tuple:
    # Get database path same way as database.py
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "data", "heartbeat.db")
    
    if not os.path.exists(db_path):
        return False, f"Database not found at {db_path}"
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    try:
        if cell_id:
            # Check specific cell
            row = conn.execute(
                "SELECT * FROM blood_cells WHERE cell_id = ?", 
                (cell_id,)
            ).fetchone()
            if row:
                cell = dict(row)
                detail = (
                    f"Status: {cell['status']} | "
                    f"Topic: {cell['topic_id']} | "
                    f"Score: {cell['importance_score']} | "
                    f"Summary: {str(cell['summary'])[:50]}"
                )
                return True, detail
            else:
                return False, f"Cell {cell_id} not found in SQLite"
        else:
            # Check test user has cells
            count = conn.execute(
                "SELECT COUNT(*) FROM blood_cells WHERE user_id = ?",
                (TEST_USER_ID,)
            ).fetchone()[0]
            active = conn.execute(
                "SELECT COUNT(*) FROM blood_cells "
                "WHERE user_id = ? AND status = 'active'",
                (TEST_USER_ID,)
            ).fetchone()[0]
            return count > 0, (
                f"Total cells: {count} | Active: {active}"
            )
    finally:
        conn.close()

def test_cell_in_chromadb(cell_id: str = None) -> tuple:
    try:
        import chromadb
        base_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
        chroma_path = os.path.join(base_dir, "data", "chroma_store")
        
        if not os.path.exists(chroma_path):
            return False, "ChromaDB store not found at data/chroma_store"
        
        client = chromadb.PersistentClient(path=chroma_path)
        
        try:
            collection = client.get_collection("heartbeat_cells")
        except:
            return False, "heartbeat_cells collection does not exist yet"
        
        count = collection.count()
        
        if cell_id:
            # Try to get specific cell
            try:
                result = collection.get(ids=[cell_id])
                if result["ids"]:
                    meta = result["metadatas"][0] if result["metadatas"] else {}
                    return True, (
                        f"Found in ChromaDB | "
                        f"Topic: {meta.get('topic_id','?')} | "
                        f"Summary: {str(meta.get('summary','?'))[:40]}"
                    )
                else:
                    return False, f"Cell {cell_id} not in ChromaDB"
            except:
                return False, f"Could not query cell {cell_id}"
        else:
            return count > 0, f"Total vectors in ChromaDB: {count}"
            
    except ImportError:
        return False, "chromadb not installed"
    except Exception as e:
        return False, str(e)

async def test_message_saved(chat_id: str, 
                              expected_count: int) -> tuple:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{API_BASE}/api/history/{chat_id}")
        if r.status_code != 200:
            return False, f"History endpoint returned {r.status_code}"
        
        msgs = r.json().get("messages", [])
        user_msgs = [m for m in msgs if m["role"] == "user"]
        ai_msgs   = [m for m in msgs if m["role"] == "assistant"]
        
        if len(msgs) >= expected_count:
            return True, (
                f"Messages saved: {len(msgs)} total | "
                f"User: {len(user_msgs)} | AI: {len(ai_msgs)}"
            )
        else:
            return False, (
                f"Expected >= {expected_count} messages, "
                f"found {len(msgs)}"
            )

async def test_memory_cross_session() -> tuple:
    # Step 1: Send a fact in Chat A
    chat_a = f"CHAT_A_{int(time.time())}"
    async with httpx.AsyncClient(timeout=60) as client:
        await client.post(f"{API_BASE}/api/message", json={
            "user_id": TEST_USER_ID,
            "chat_id": chat_a,
            "session_id": TEST_SESSION,
            "content": "My favourite programming language is definitely Rust",
            "content_type": "text"
        })
        
        # Wait for cell to be created and purified
        await asyncio.sleep(3)
        
        # Step 2: Ask about it in Chat B (different chat)
        chat_b = f"CHAT_B_{int(time.time())}"
        r = await client.post(f"{API_BASE}/api/message", json={
            "user_id": TEST_USER_ID,
            "chat_id": chat_b,
            "session_id": TEST_SESSION,
            "content": "What is my favourite programming language?",
            "content_type": "text"
        })
        
        if r.status_code != 200:
            return False, f"Chat B message failed: {r.status_code}"
        
        ai_response = r.json().get("ai_response", "").lower()
        
        # Check if AI remembered Rust from Chat A
        if "rust" in ai_response:
            return True, (
                f"AI correctly recalled 'Rust' across sessions. "
                f"Response: '{ai_response[:80]}...'"
            )
        else:
            return False, (
                f"AI did NOT recall Rust from previous chat. "
                f"Response: '{ai_response[:80]}...'"
            )

async def test_stats_endpoint() -> tuple:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{API_BASE}/api/stats/{TEST_USER_ID}")
        if r.status_code != 200:
            return False, f"Stats endpoint returned {r.status_code}"
        
        data = r.json()
        required_fields = [
            "total_cells", "active_cells", "total_messages",
            "total_chats", "avg_importance", "topic_distribution"
        ]
        missing = [f for f in required_fields if f not in data]
        
        if not missing:
            return True, (
                f"Total cells: {data['total_cells']} | "
                f"Active: {data['active_cells']} | "
                f"Messages: {data['total_messages']} | "
                f"Avg importance: {data['avg_importance']}"
            )
        else:
            return False, f"Missing fields: {missing}"

async def test_answer_levels(chat_id: str, 
                              cell_id: str) -> tuple:
    if not cell_id:
        return False, "No cell_id to test answers with"
    
    async with httpx.AsyncClient(timeout=30) as client:
        results_local = []
        
        for level in [1, 2, 3]:
            r = await client.post(f"{API_BASE}/api/answer", json={
                "user_id": TEST_USER_ID,
                "cell_id": cell_id,
                "message": f"Tell me more",
                "depth_level": level
            })
            
            if r.status_code == 200:
                data = r.json()
                response = data.get("response") or data.get(
                    "answer") or data.get("message", "")
                if response:
                    results_local.append(
                        f"L{level}: '{str(response)[:40]}...' ✓"
                    )
                else:
                    results_local.append(f"L{level}: Empty response ✗")
            else:
                results_local.append(
                    f"L{level}: HTTP {r.status_code} ✗"
                )
        
        all_passed = all("✓" in r for r in results_local)
        return all_passed, " | ".join(results_local)

# ── MAIN TEST RUNNER ──────────────────────────────────────────────────────────

async def main():
    print(f"\n{BOLD}{CYAN}")
    print("╔══════════════════════════════════════════════════════╗")
    print("║     HEARTBEAT END-TO-END PIPELINE TEST AGENT        ║")
    print("║     Testing full biological memory pipeline          ║")
    print(f"╚══════════════════════════════════════════════════════╝{RESET}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Test User: {TEST_USER_ID}\n")
    
    # Create unique chat ID for this test run
    TEST_CHAT_ID = f"TEST_{int(time.time())}"
    last_cell_id = None
    
    # ── TEST 1: Server Health ──
    await test_server_health()
    
    # ── TEST 2-8: Pipeline tests for each message ──
    print(f"\n{BOLD}{BLUE}━━━ TEST 2-8: Pipeline Verification Per Message ━━━{RESET}")
    
    for msg in TEST_MESSAGES:
        print(f"\n{BOLD}Message: '{msg['content'][:55]}...'{RESET}")
        print(f"{CYAN}Expected: {msg['description']}{RESET}")
        
        # 2. Send message (simulates chat UI)
        result = await send_test_message(msg, TEST_CHAT_ID)
        sc = result["status_code"]
        elapsed = result["elapsed_ms"]
        resp = result["response"]
        
        if sc == 200:
            log("📤", f"Message sent via API ({elapsed}ms)", "PASS",
                f"AI Response: '{str(resp.get('ai_response',''))[:60]}...'")
            cell_id = resp.get("cell_id")
            if cell_id:
                last_cell_id = cell_id
        else:
            log("📤", f"Message send failed", "FAIL", 
                f"HTTP {sc}: {resp}")
            continue
        
        # 3. Test L1 Sieve
        l1_ok, l1_detail = await test_l1_sieve(
            msg["content"], msg["expected_l1_pass"]
        )
        log("🔬", "L1 Sieve — noise removal", 
            "PASS" if l1_ok else "FAIL", l1_detail)
        
        # 4. Test L2 Valve (only if L1 passes)
        if msg["expected_l1_pass"]:
            l2_ok, l2_detail = await test_l2_valve(
                msg["content"],
                msg["expected_intent"],
                msg["expected_ambiguous"]
            )
            log("⚡", "L2 Valve — classification", 
                "PASS" if l2_ok else "WARN", l2_detail)
            
            # 5. Test L3 Purifier
            l3_ok, l3_detail = await test_l3_purifier(msg["content"])
            log("💎", "L3 Purifier — extraction", 
                "PASS" if l3_ok else "FAIL", l3_detail)
        
        # Small delay between messages
        await asyncio.sleep(1)
    
    # ── TEST 6: SQLite Storage ──
    print(f"\n{BOLD}{BLUE}━━━ TEST 6: Database Storage ━━━{RESET}")
    sql_ok, sql_detail = test_cell_in_sqlite()
    log("💾", "Cells saved to SQLite", 
        "PASS" if sql_ok else "FAIL", sql_detail)
    
    if last_cell_id:
        sql_cell_ok, sql_cell_detail = test_cell_in_sqlite(last_cell_id)
        log("💾", f"Specific cell in SQLite ({last_cell_id[:8]}...)",
            "PASS" if sql_cell_ok else "FAIL", sql_cell_detail)
    
    # ── TEST 7: ChromaDB Storage ──
    print(f"\n{BOLD}{BLUE}━━━ TEST 7: ChromaDB Vector Storage ━━━{RESET}")
    chroma_ok, chroma_detail = test_cell_in_chromadb()
    log("🔵", "Vectors saved to ChromaDB",
        "PASS" if chroma_ok else "FAIL", chroma_detail)
    
    if last_cell_id:
        chroma_cell_ok, chroma_cell_detail = test_cell_in_chromadb(
            last_cell_id
        )
        log("🔵", f"Specific cell in ChromaDB ({last_cell_id[:8]}...)",
            "PASS" if chroma_cell_ok else "WARN", chroma_cell_detail)
    
    # ── TEST 8: Message Display Layer ──
    print(f"\n{BOLD}{BLUE}━━━ TEST 8: Message Display Layer ━━━{RESET}")
    msg_ok, msg_detail = await test_message_saved(
        TEST_CHAT_ID, len(TEST_MESSAGES) * 2
    )
    log("📝", "Messages saved to SQLite display layer",
        "PASS" if msg_ok else "FAIL", msg_detail)
    
    # ── TEST 9: Cross-Session Memory ──
    print(f"\n{BOLD}{BLUE}━━━ TEST 9: Cross-Session Memory ━━━{RESET}")
    print(f"{CYAN}Sending fact in Chat A, asking about it in Chat B...{RESET}")
    mem_ok, mem_detail = await test_memory_cross_session()
    log("🧠", "AI recalls memory across different chats",
        "PASS" if mem_ok else "FAIL", mem_detail)
    
    # ── TEST 10: Stats Endpoint ──
    print(f"\n{BOLD}{BLUE}━━━ TEST 10: Stats Endpoint ━━━{RESET}")
    stats_ok, stats_detail = await test_stats_endpoint()
    log("📊", "Stats endpoint returns correct data",
        "PASS" if stats_ok else "FAIL", stats_detail)
    
    # ── TEST 11: 3-Level Answer System ──
    print(f"\n{BOLD}{BLUE}━━━ TEST 11: 3-Level Answer System ━━━{RESET}")
    ans_ok, ans_detail = await test_answer_levels(
        TEST_CHAT_ID, last_cell_id
    )
    log("🎯", "3-level answers (Quick/Detail/Original)",
        "PASS" if ans_ok else "WARN", ans_detail)
    
    # ══════════════════════════════════════════════════
    # FINAL REPORT
    # ══════════════════════════════════════════════════
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    warned = sum(1 for r in results if r["status"] == "WARN")
    total  = len(results)
    
    print(f"\n{BOLD}{CYAN}")
    print("╔══════════════════════════════════════════════════════╗")
    print("║                  FINAL TEST REPORT                  ║")
    print("╠══════════════════════════════════════════════════════╣")
    print(f"║  {GREEN}PASSED: {passed:3d}{CYAN}  |  "
          f"{RED}FAILED: {failed:3d}{CYAN}  |  "
          f"{YELLOW}WARNED: {warned:3d}{CYAN}  |  TOTAL: {total:3d}  ║")
    score = round((passed / total) * 100) if total > 0 else 0
    print(f"║  Score: {score}% — "
          f"{'ALL SYSTEMS GO' if score >= 80 else 'NEEDS FIXES'}        "
          f"                  ║")
    print(f"╚══════════════════════════════════════════════════════╝{RESET}")
    
    if failed > 0:
        print(f"\n{RED}{BOLD}Failed Tests:{RESET}")
        for r in results:
            if r["status"] == "FAIL":
                print(f"  {RED}✗ {r['label']}{RESET}")
                if r["detail"]:
                    print(f"    {r['detail']}")
    
    if warned > 0:
        print(f"\n{YELLOW}{BOLD}Warnings (investigate):{RESET}")
        for r in results:
            if r["status"] == "WARN":
                print(f"  {YELLOW}⚠ {r['label']}{RESET}")
    
    # Save results to file
    report_path = "scripts/test_agent_report.json"
    with open(report_path, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "score": score,
            "passed": passed,
            "failed": failed,
            "warned": warned,
            "results": results
        }, f, indent=2)
    print(f"\n{CYAN}Full report saved to: {report_path}{RESET}")

if __name__ == "__main__":
    asyncio.run(main())
