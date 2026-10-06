import asyncio
import sys
import os
import shutil
from dotenv import load_dotenv

# Add root to path
sys.path.append(os.getcwd())
load_dotenv()

from cells.cell_model import CellFactory, PurifiedData
from storage.database import get_connection, init_database
from storage.chroma_client import get_chroma_manager
from storage.link_vault import get_link_vault
from storage.database_ops import persist_purified_cell, get_semantic_memory

async def test_phase5():
    print("--- Phase 5 Verification: Storage Layer (Bones) ---")
    
    # 0. Initialize Tables
    init_database()
    
    # 1. Clear previous test data (optional but cleaner)
    # shutil.rmtree("./chroma_store", ignore_errors=True)
    
    # 2. Mock a Purified Blood Cell
    sample_cell = CellFactory.from_text(
        user_id="user_storage_test",
        chat_id="chat_test",
        message_id="msg_test",
        session_id="sess_test",
        content="I love using Groq for AI speed."
    )
    # Simulate L3 Purification
    sample_cell.summary = "User expressed strong preference for Groq AI inference speed."
    sample_cell.purified_data = PurifiedData(
        entities=["Groq", "AI"],
        facts=["User prefers Groq for speed"],
        metadata={"urls": ["https://groq.com"], "topic_id": "ai_tools"}
    )
    sample_cell.analysis_status = "purified"
    
    # 3. Test Persistence
    print("\nTesting Unified Persistence (SQLite + ChromaDB + Link Vault)...")
    try:
        await persist_purified_cell(sample_cell)
        print("✅ Unified Persist OK")
    except Exception as e:
        print(f"❌ Persist Failed: {e}")
        return

    # 4. Test ChromaDB Semantic Search
    print("\nTesting ChromaDB Semantic Search...")
    chroma = get_chroma_manager()
    results = chroma.search_related("Which AI provider is fast?", n_results=1, user_id="user_storage_test")
    if results and "Groq" in results[0]["metadata"]["summary"]:
        print(f"✅ Semantic Search OK (Found: {results[0]['metadata']['summary']})")
    else:
        print("❌ Semantic Search Failed to match context.")

    # 5. Test Link Vault
    print("\nTesting Link Vault Persistence...")
    vault = get_link_vault()
    links = vault.get_user_links("user_storage_test")
    if links and "groq.com" in links[0].url:
        print(f"✅ Link Vault OK (Found: {links[0].url})")
    else:
        print("❌ Link Vault Failed to find URL.")

    print("\n--- Phase 5 Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(test_phase5())
