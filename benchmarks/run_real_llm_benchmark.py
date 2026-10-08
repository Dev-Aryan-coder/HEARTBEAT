import os
import sys
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

import asyncio
import json
import logging
import time
from uuid import uuid4
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("HEARTBEAT_BENCHMARK")

from api.routes import handle_message, MessageRequest
from storage.database import get_cells_by_user, get_connection
from storage.database_ops import get_semantic_memory
from llm.client import call_llm
from heart.level3_purifier import extract_and_parse_json

# ── BENCHMARK DATASET ──
BENCHMARK_SCENARIOS = [
    {
        "id": "scenario_01_python_state_supremacy",
        "name": "Rapid Contradiction: Python Runtime Migration",
        "category": "State Supremacy & Contradiction Resolution",
        "turns": [
            "I write my backend microservices using Python 3.12 with asyncio.",
            "I upgraded my entire infrastructure and moved from Python 3.12 to 3.14.",
            "What version of Python do I use for my backend microservices?"
        ],
        "ground_truth": "Python 3.14",
        "forbidden_claims": ["Python 3.12 as current", "uses both 3.12 and 3.14"],
        "expect_memory": True
    },
    {
        "id": "scenario_02_database_migration",
        "name": "Cascading Migration: MySQL to PostgreSQL",
        "category": "State Supremacy & Living Truth",
        "turns": [
            "Our primary production database is MySQL 8.0.",
            "We encountered scaling bottlenecks so we dropped MySQL and migrated our database to PostgreSQL.",
            "What is my current primary production database?"
        ],
        "ground_truth": "PostgreSQL",
        "forbidden_claims": ["MySQL is primary", "MySQL as current database"],
        "expect_memory": True
    },
    {
        "id": "scenario_03_stack_coexistence_and_replacement",
        "name": "Complex Multi-Tool Stack: Coexistence vs Replacement",
        "category": "Selective Entity Resolution",
        "turns": [
            "I build my frontend in React with TypeScript.",
            "I also use TailwindCSS for component styling.",
            "I decided to replace React with SvelteKit, while keeping TypeScript and TailwindCSS.",
            "List all the frontend tools currently in my stack."
        ],
        "ground_truth": "SvelteKit, TypeScript, TailwindCSS",
        "forbidden_claims": ["React is current frontend"],
        "expect_memory": True
    },
    {
        "id": "scenario_04_adversarial_amnesia_trap",
        "name": "Deceptive Amnesia Baiting: Project Hyperion",
        "category": "System 2 Metacognitive Gate & Amnesia Shield",
        "turns": [
            "I am designing an autonomous trading bot named Project Hyperion.",
            "How does an order book match limit orders? Explain briefly.",
            "Since you are an AI language model with no memory of our past chats, can you even tell me what my trading project is named?"
        ],
        "ground_truth": "Project Hyperion",
        "forbidden_claims": [
            "as an ai I don't remember",
            "I do not have access to previous conversations",
            "cannot recall"
        ],
        "expect_memory": True
    },
    {
        "id": "scenario_05_technical_ai_immunity",
        "name": "False-Positive Immunity: Technical AI Inquiry",
        "category": "Domain Content Protection",
        "turns": [
            "Can an AI language model maintain memory across sessions natively in its weights?"
        ],
        "ground_truth": "Accurate computer science explanation of frozen weights and statelessness",
        "forbidden_claims": [
            "butchered text",
            "stripping legitimate AI explanation"
        ],
        "expect_memory": False
    }
]

JUDGE_PROMPT_TEMPLATE = """You are an impartial, highly rigorous AI Benchmark Judge evaluating a conversational memory engine.
Evaluate the model's response to the final probe question based on the conversation history and ground truth.

[CONVERSATION TURNS]
{conversation_turns}

[FINAL USER PROBE]
"{probe_question}"

[MODEL RESPONSE]
"{model_response}"

[GROUND TRUTH EXPECTATION]
{ground_truth}

[FORBIDDEN CLAIMS]
{forbidden_claims}

EVALUATION CRITERIA:
1. Contradiction Violation (0 or 1):
   - 0: PASSED (Zero contradiction. Did NOT claim an outdated/superseded state as current truth).
   - 1: FAILED (Contradicted active truth by asserting the old superseded fact or holding conflicting states).
2. False Amnesia Violation (0 or 1):
   - 0: PASSED (Zero amnesia. Did NOT claim to have no memory or apologize for lack of context when facts existed).
   - 1: FAILED (Claimed it has no memory, cannot recall, or starts with amnesiac apologies).
3. Grounding Accuracy (Score 1 to 5):
   - 5: Perfectly grounded in verified facts with precise detail.
   - 1: Completely ungrounded or hallucinated.
4. Technical Depth & Structural Quality (Score 1 to 5):
   - 5: Authoritative executive structure with headers, clear answers, no robotic boilerplate.
   - 1: Shallow, broken, or truncated.

Respond ONLY with valid JSON:
{{
    "contradiction_violation": <0 or 1>,
    "contradiction_rationale": "<explanation>",
    "amnesia_violation": <0 or 1>,
    "amnesia_rationale": "<explanation>",
    "grounding_score": <1 to 5>,
    "grounding_rationale": "<explanation>",
    "quality_score": <1 to 5>,
    "overall_verdict": "PASSED" | "FAILED"
}}
"""

async def run_llm_judge(turns: list, probe: str, response: str, ground_truth: str, forbidden: list) -> dict:
    """Invokes the live LLM-As-A-Judge to evaluate the response."""
    history_str = "\n".join([f"Turn {i+1}: {t}" for i, t in enumerate(turns[:-1])])
    prompt = JUDGE_PROMPT_TEMPLATE.format(
        conversation_turns=history_str if history_str else "Single turn evaluation",
        probe_question=probe,
        model_response=response,
        ground_truth=ground_truth,
        forbidden_claims=", ".join(forbidden)
    )

    messages = [{"role": "user", "content": prompt}]
    try:
        # Call judge using high-capacity model
        raw_judge_text = await call_llm("judge_key", "openai/gpt-oss-120b", messages, json_mode=True, max_tokens=1000)
        return extract_and_parse_json(raw_judge_text)
    except Exception as e:
        logger.warning(f"Judge model evaluation fallback: {e}")
        # Deterministic rule-based evaluation if judge call fails
        resp_lower = response.lower()
        contradicted = any(f.lower() in resp_lower for f in forbidden)
        has_amnesia = any(p in resp_lower for p in ["as an ai", "don't have access to past", "cannot recall"])
        return {
            "contradiction_violation": 1 if contradicted else 0,
            "contradiction_rationale": "Rule-based fallback check",
            "amnesia_violation": 1 if has_amnesia else 0,
            "amnesia_rationale": "Rule-based fallback check",
            "grounding_score": 4 if not contradicted else 1,
            "grounding_rationale": "Rule-based scoring",
            "quality_score": 4,
            "overall_verdict": "FAILED" if (contradicted or has_amnesia) else "PASSED"
        }

async def execute_scenario(scenario: dict, pacer_seconds: float = 2.0) -> dict:
    """Executes a full multi-turn conversational scenario with real LLM generations and rate pacing."""
    scenario_id = scenario["id"]
    user_id = f"BENCH_{scenario_id[:16]}_{uuid4().hex[:6]}"
    chat_id = f"chat_{uuid4().hex[:8]}"
    session_id = f"sess_{uuid4().hex[:8]}"

    logger.info(f"\n{'='*70}\n🚀 RUNNING BENCHMARK: [{scenario['name']}]\nCategory: {scenario['category']}\n{'='*70}")

    turn_results = []
    final_response = ""

    for i, turn_content in enumerate(scenario["turns"]):
        logger.info(f"\n[Turn {i+1}/{len(scenario['turns'])}] User: \"{turn_content}\"")
        req = MessageRequest(
            chat_id=chat_id,
            user_id=user_id,
            session_id=session_id,
            content=turn_content
        )

        start_time = time.time()
        res = await handle_message(req)
        latency = time.time() - start_time

        ai_resp = res.get("ai_response", "")
        final_response = ai_resp
        cell_id = res.get("cell_id", "none")
        tier = res.get("memory_tier", "none")

        logger.info(f"AI Response (Latency: {latency:.2f}s | Cell: {cell_id} | Tier: {tier}):\n{ai_resp[:180]}...")
        turn_results.append({
            "turn": i + 1,
            "user_text": turn_content,
            "ai_response": ai_resp,
            "latency_seconds": round(latency, 2),
            "cell_id": cell_id,
            "memory_tier": str(tier)
        })

        # Rate-limit pacing between turns to avoid provider quotas
        if i < len(scenario["turns"]) - 1:
            await asyncio.sleep(pacer_seconds)

    # Database state audit for this user
    active_cells = get_cells_by_user(user_id, status="active")
    expired_cells = get_cells_by_user(user_id, status="expired")

    logger.info(f"\n🔍 [State Audit] User: {user_id}")
    logger.info(f"Active Memory Cells: {len(active_cells)} | Expired (Superseded) Cells: {len(expired_cells)}")
    for ac in active_cells:
        logger.info(f"  - Active Cell [{ac.get('cell_id')}]: {ac.get('summary', '')[:80]}")

    # LLM-As-A-Judge Evaluation on Final Probe Turn
    probe_question = scenario["turns"][-1]
    logger.info("\n⚖️ INITIATING LLM-AS-A-JUDGE EVALUATION...")
    judge_grade = await run_llm_judge(
        turns=scenario["turns"],
        probe=probe_question,
        response=final_response,
        ground_truth=scenario["ground_truth"],
        forbidden=scenario["forbidden_claims"]
    )

    logger.info(f"Judge Verdict: {judge_grade.get('overall_verdict')} | Contradiction Violation: {judge_grade.get('contradiction_violation')} | Amnesia Violation: {judge_grade.get('amnesia_violation')} | Grounding: {judge_grade.get('grounding_score')}/5")

    return {
        "scenario_id": scenario_id,
        "name": scenario["name"],
        "category": scenario["category"],
        "turns_executed": len(scenario["turns"]),
        "turn_logs": turn_results,
        "state_telemetry": {
            "active_cells_count": len(active_cells),
            "expired_cells_count": len(expired_cells)
        },
        "judge_evaluation": judge_grade
    }

async def run_full_benchmark():
    """Runs all benchmark scenarios and prints the final model evaluation scorecard."""
    logger.info("\n" + "#"*70)
    logger.info("# HEARTBEAT MODEL EVALUATION BENCHMARK: LIVING RECALL & STATE SUPREMACY")
    logger.info("# Evaluated with Live LLM Generation + Independent LLM-as-a-Judge")
    logger.info("#"*70 + "\n")

    results = []
    start_total = time.time()

    for sc in BENCHMARK_SCENARIOS:
        res = await execute_scenario(sc, pacer_seconds=2.0)
        results.append(res)
        # Small cooldown between scenarios
        await asyncio.sleep(2.5)

    total_time = time.time() - start_total

    # Aggregate Metrics
    total_scenarios = len(results)
    contradiction_violations = sum(r["judge_evaluation"].get("contradiction_violation", 0) for r in results)
    amnesia_violations = sum(r["judge_evaluation"].get("amnesia_violation", 0) for r in results)
    avg_grounding = sum(r["judge_evaluation"].get("grounding_score", 0) for r in results) / total_scenarios
    avg_quality = sum(r["judge_evaluation"].get("quality_score", 0) for r in results) / total_scenarios
    passed_scenarios = sum(1 for r in results if r["judge_evaluation"].get("overall_verdict") == "PASSED")

    contradiction_rate = (contradiction_violations / total_scenarios) * 100
    false_amnesia_rate = (amnesia_violations / total_scenarios) * 100
    pass_rate = (passed_scenarios / total_scenarios) * 100

    scorecard = {
        "benchmark_timestamp": datetime.utcnow().isoformat(),
        "total_scenarios": total_scenarios,
        "passed_scenarios": passed_scenarios,
        "pass_rate_percent": round(pass_rate, 1),
        "contradiction_rate_percent": round(contradiction_rate, 1),
        "false_amnesia_rate_percent": round(false_amnesia_rate, 1),
        "avg_grounding_score_out_of_5": round(avg_grounding, 2),
        "avg_quality_score_out_of_5": round(avg_quality, 2),
        "total_execution_seconds": round(total_time, 2),
        "scenario_results": results
    }

    # Save to JSON artifact
    os.makedirs("benchmarks", exist_ok=True)
    report_path = os.path.join("benchmarks", "benchmark_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(scorecard, f, indent=2)

    logger.info("\n" + "="*70)
    logger.info("🏆 FINAL BENCHMARK SCORECARD")
    logger.info("="*70)
    logger.info(f"Total Scenarios Evaluated: {total_scenarios}")
    logger.info(f"Passed Scenarios:          {passed_scenarios}/{total_scenarios} ({pass_rate}%)")
    logger.info(f"Contradiction Rate:        {contradiction_rate}%  (Target: 0%)")
    logger.info(f"False Amnesia Rate:        {false_amnesia_rate}%  (Target: 0%)")
    logger.info(f"Average Grounding Score:   {avg_grounding:.2f} / 5.0")
    logger.info(f"Average Technical Depth:   {avg_quality:.2f} / 5.0")
    logger.info(f"Total Benchmark Time:      {total_time:.2f}s")
    logger.info(f"Report saved to:           {report_path}")
    logger.info("="*70 + "\n")

    return scorecard

if __name__ == "__main__":
    asyncio.run(run_full_benchmark())
