import os
import sys
import json
import asyncio
import time
from typing import List, Dict, Any

workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(workspace_dir)

from tests.evals.evaluators import LLMJudgeEvaluator
from app.agent_graph.orchestrator import MultiAgentOrchestrator

async def run_benchmark():
    print("=================================================================")
    print("🚀 AUTOMATYCZNY BENCHMARK EVALS LLM (G-Eval / Multi-Agent DAG)")
    print("=================================================================")

    dataset_path = os.path.join(os.path.dirname(__file__), "datasets", "athlete_benchmark_100.json")
    if not os.path.exists(dataset_path):
        print(f"❌ Brak datasetu benchmarkowego: {dataset_path}")
        return

    with open(dataset_path, "r", encoding="utf-8") as f:
        profiles: List[Dict[str, Any]] = json.load(f)

    evaluator = LLMJudgeEvaluator()
    orchestrator = MultiAgentOrchestrator(max_iterations=3)
    results = []

    print(f"Załadowano {len(profiles)} profilów z datasetu benchmarkowego.\n")

    total_safety_score = 0
    total_factuality_score = 0
    schema_passed_count = 0

    for idx, profile in enumerate(profiles, start=1):
        print(f"[{idx}/{len(profiles)}] Testowanie Orkiestratora Wieloagentowego dla: {profile['id']} ({profile['name']})...", end=" ", flush=True)

        wellness_sim = [
            {"date": "2026-08-01", "hrv": profile["hrv_baseline"], "restingHR": profile["resting_hr"]},
            {"date": "2026-08-02", "hrv": profile["hrv_baseline"], "restingHR": profile["resting_hr"]},
            {"date": "2026-08-03", "hrv": profile["hrv_baseline"], "restingHR": profile["resting_hr"]},
            {"date": "2026-08-04", "hrv": profile["hrv_baseline"], "restingHR": profile["resting_hr"]},
            {"date": "2026-08-05", "hrv": profile["hrv_today"], "restingHR": profile["resting_hr"]}
        ]

        user_context = f"Zawodnik: {profile['name']}, CTL: {profile['ctl']}, ATL: {profile['atl']}, TSB: {profile['tsb']}. Cele: {', '.join(profile['goals'])}"

        # 1. PRAWDZIWE WYKONANIE GRAFU WIELOAGENTOWEGO DAG
        agent_exec_result = await orchestrator.run(
            wellness_data=wellness_sim,
            user_context=user_context,
            compliance_fact={"compliance_score": 8},
            today_planned=[]
        )

        simulated_output = {
            "decision": agent_exec_result["status"],
            "compliance_score": 8,
            "wellness_assessment": agent_exec_result["verdict"]["notes"],
            "modified_workout_description": agent_exec_result["proposal"]["dsl_text"]
        }

        # 2. Ewaluacja Sędziowska (LLM-as-a-Judge)
        eval_result = await evaluator.evaluate_decision(profile, simulated_output)


        total_safety_score += eval_result["safety_score"]
        total_factuality_score += eval_result["factuality_score"]
        if eval_result["schema_adherence"]:
            schema_passed_count += 1

        results.append({
            "profile_id": profile["id"],
            "category": profile["edge_case_category"],
            "safety_score": eval_result["safety_score"],
            "factuality_score": eval_result["factuality_score"],
            "schema_adherence": eval_result["schema_adherence"],
            "reasoning": eval_result["reasoning"],
            "judge_latency_ms": eval_result["judge_latency_ms"]
        })

        print(f"✅ Safety: {eval_result['safety_score']}/5 | Factuality: {eval_result['factuality_score']}/5")

    # Podsumowanie statystyczne
    count = len(profiles)
    mean_safety = round(total_safety_score / count, 2)
    mean_factuality = round(total_factuality_score / count, 2)
    schema_pass_rate = round((schema_passed_count / count) * 100.0, 1)

    summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_profiles_evaluated": count,
        "mean_safety_score": mean_safety,
        "mean_factuality_score": mean_factuality,
        "schema_adherence_pass_rate_pct": schema_pass_rate,
        "details": results
    }

    # Zapis raportu do pliku logs/eval_benchmark_report.json
    os.makedirs("logs", exist_ok=True)
    report_path = os.path.join("logs", "eval_benchmark_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\n=================================================================")
    print("📊 PODSUMOWANIE RAPORTU BENCHMARKOWEGO EVALS")
    print("=================================================================")
    print(f" Przetestowano profilów:        {count}")
    print(f" Średnia Ocena Bezpieczeństwa: {mean_safety} / 5.0")
    print(f" Średnia Ocena Rzetelności:    {mean_factuality} / 5.0")
    print(f" Zgodność ze Schematem (Schema): {schema_pass_rate}%")
    print(f" Raport zapisany w:            {report_path}")
    print("=================================================================\n")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
