"""Evaluation script for RAG retrieval, permissions, grounded citations, and routing.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.rag import RAGIndex, generate_grounded_answer, normalize_text, DEFAULT_BUNDLE_PATH
from src.router import route_message


def run_evaluation(bundle_path=DEFAULT_BUNDLE_PATH, cases_path=ROOT / "artifacts" / "evaluation_cases.jsonl", split=None):
    cases = [json.loads(line) for line in Path(cases_path).read_text(encoding="utf-8").splitlines() if line.strip()]
    if split:
        cases = [c for c in cases if c.get("split") == split]

    index = RAGIndex.load(bundle_path)
    retrieval_hits_at_3 = 0
    retrieval_recalls_at_5: list[float] = []
    reciprocal_ranks: list[float] = []
    retrieval_eligible_count = 0

    safe_abstention_correct = 0
    safe_abstention_total = 0

    access_denied_correct = 0
    access_denied_total = 0

    mixed_correct = 0
    mixed_total = 0

    citation_resolved_count = 0
    citation_total_count = 0

    answer_fact_count = 0
    answer_fact_match_count = 0
    retrieved_fact_match_count = 0
    cited_fact_match_count = 0
    mixed_query_split_count = 0
    mixed_query_split_match_count = 0
    mixed_action_intent_count = 0
    mixed_action_intent_match_count = 0
    route_match_count = 0
    status_match_count = 0
    total_evaluated_cases = len(cases)

    case_results = []

    for case in cases:
        cid = case["id"]
        query = case["query"]
        role = case["role"]
        expected_chunks = set(case.get("expected_chunk_ids", []))
        expected_status = case.get("expected_status")
        expected_route = case.get("expected_route")

        # 1. Routing
        decision = route_message(query)
        actual_route = decision.primary_route
        route_match = actual_route == expected_route
        route_match_count += int(route_match)
        split_expected = case.get("expected_order_query_contains")
        category_is_mixed = case.get("category") == "mixed"
        split_match = bool(
            decision.knowledge_query and decision.order_query
            and (not split_expected or normalize_text(split_expected) in normalize_text(decision.order_query))
        ) if category_is_mixed else None
        if category_is_mixed:
            mixed_query_split_count += 1
            mixed_query_split_match_count += int(split_match)
        expected_action_intent = case.get("expected_action_intent")
        action_intent_match = decision.intent == expected_action_intent if expected_action_intent else None
        if expected_action_intent:
            mixed_action_intent_count += 1
            mixed_action_intent_match_count += int(action_intent_match)

        # 2. Retrieval & Generation
        k_query = decision.knowledge_query or query
        retrieved = index.retrieve(k_query, user_role=role, top_k=5)
        retrieved_chunk_ids = [c.chunk_id for c, _ in retrieved]

        # Calculate retrieval metrics if query has expected chunks
        if expected_chunks:
            retrieval_eligible_count += 1
            # Hit@3
            top3 = set(retrieved_chunk_ids[:3])
            hit = 1 if (expected_chunks & top3) else 0
            retrieval_hits_at_3 += hit

            # Recall@5
            top5 = set(retrieved_chunk_ids[:5])
            recall = len(expected_chunks & top5) / len(expected_chunks)
            retrieval_recalls_at_5.append(recall)

            # MRR
            rr = 0.0
            for rank, r_id in enumerate(retrieved_chunk_ids, 1):
                if r_id in expected_chunks:
                    rr = 1.0 / rank
                    break
            reciprocal_ranks.append(rr)

        answer_obj = generate_grounded_answer(k_query, retrieved, user_role=role)
        actual_status = answer_obj["status"]
        status_match = actual_status == expected_status
        status_match_count += int(status_match)

        # 3. Citation resolution check
        for cit in answer_obj.get("citations", []):
            citation_total_count += 1
            cited_chunk = next((chunk for chunk in index.chunks if chunk.chunk_id == cit.get("chunk_id")), None)
            if cited_chunk and all(cit.get(key) == getattr(cited_chunk, attr) for key, attr in {
                "doc_id": "doc_id", "source": "source", "version": "version", "section": "section"
            }.items()) and cited_chunk.access_level in {
                "customer": {"public"}, "staff": {"public", "staff"}, "admin": {"public", "staff", "admin"}
            }.get(role, {"public"}):
                citation_resolved_count += 1

        # 4. Check category specific goals
        category = case["category"]
        if category == "no_evidence":
            safe_abstention_total += 1
            if actual_status == "insufficient_evidence":
                safe_abstention_correct += 1

        if category == "access_denied":
            access_denied_total += 1
            if actual_status == "access_denied":
                access_denied_correct += 1

        if category == "mixed":
            mixed_total += 1
            if actual_route == "mixed" and answer_obj.get("citations"):
                mixed_correct += 1

        # 5. Claim support check (basic check if key facts in answer)
        facts = case.get("expected_facts", []) if expected_status == "answered" else []
        ans_text = answer_obj.get("answer", "")
        ans_norm = normalize_text(ans_text)
        retrieved_norm = normalize_text("\n".join(f"{chunk.source}\n{chunk.text}" for chunk, _ in retrieved))
        cited_ids = {citation.get("chunk_id") for citation in answer_obj.get("citations", [])}
        cited_norm = normalize_text("\n".join(
            f"{chunk.source}\n{chunk.text}" for chunk in index.chunks if chunk.chunk_id in cited_ids
        ))
        fact_answer_matches = [normalize_text(fact) in ans_norm for fact in facts]
        fact_retrieved_matches = [normalize_text(fact) in retrieved_norm for fact in facts]
        fact_cited_matches = [
            normalize_text(fact) in ans_norm and normalize_text(fact) in cited_norm for fact in facts
        ]
        answer_fact_count += len(facts)
        answer_fact_match_count += sum(fact_answer_matches)
        retrieved_fact_match_count += sum(fact_retrieved_matches)
        cited_fact_match_count += sum(fact_cited_matches)

        case_results.append({
            "id": cid,
            "category": category,
            "route_match": route_match,
            "status_match": status_match,
            "mixed_query_split_match": split_match,
            "mixed_action_intent_match": action_intent_match,
            "actual_route": actual_route,
            "actual_status": actual_status,
            "citations": [c["chunk_id"] for c in answer_obj.get("citations", [])],
            "answer_preview": ans_text[:120] + "..." if len(ans_text) > 120 else ans_text,
            "expected_answer_facts": facts,
            "answer_fact_matches": fact_answer_matches,
            "retrieved_evidence_matches": fact_retrieved_matches,
            "cited_evidence_matches": fact_cited_matches,
        })

    # Summary metrics
    hit_at_3_rate = (retrieval_hits_at_3 / retrieval_eligible_count) if retrieval_eligible_count else 1.0
    mean_recall_at_5 = (sum(retrieval_recalls_at_5) / len(retrieval_recalls_at_5)) if retrieval_recalls_at_5 else 1.0
    mrr = (sum(reciprocal_ranks) / len(reciprocal_ranks)) if reciprocal_ranks else 1.0
    citation_resolve_rate = (citation_resolved_count / citation_total_count) if citation_total_count else 1.0
    abstention_rate = (safe_abstention_correct / safe_abstention_total) if safe_abstention_total else 1.0
    access_denied_rate = (access_denied_correct / access_denied_total) if access_denied_total else 1.0
    mixed_accuracy = (mixed_correct / mixed_total) if mixed_total else 1.0
    answer_fact_match_rate = answer_fact_match_count / answer_fact_count if answer_fact_count else 1.0
    retrieved_evidence_coverage = retrieved_fact_match_count / answer_fact_count if answer_fact_count else 1.0
    citation_fact_support_rate = cited_fact_match_count / answer_fact_count if answer_fact_count else 1.0

    report = {
        "split": split or "all",
        "total_cases": total_evaluated_cases,
        "retrieval_cases_count": retrieval_eligible_count,
        "metrics": {
            "Hit@3": round(hit_at_3_rate * 100, 2),
            "Recall@5": round(mean_recall_at_5 * 100, 2),
            "MRR": round(mrr, 4),
            "Citation_Resolve_Rate": round(citation_resolve_rate * 100, 2),
            "Expected_Answer_Fact_Match_Rate": round(answer_fact_match_rate * 100, 2),
            "Retrieved_Evidence_Lexical_Coverage": round(retrieved_evidence_coverage * 100, 2),
            "Citation_Evidence_Lexical_Support": round(citation_fact_support_rate * 100, 2),
            "Safe_Abstention_Rate": round(abstention_rate * 100, 2),
            "Access_Denied_Rate": round(access_denied_rate * 100, 2),
            "Mixed_Route_Accuracy": round(mixed_accuracy * 100, 2),
            "Mixed_Query_Split_Accuracy": round(mixed_query_split_match_count / mixed_query_split_count * 100, 2) if mixed_query_split_count else 100.0,
            "Mixed_Action_Intent_Accuracy": round(mixed_action_intent_match_count / mixed_action_intent_count * 100, 2) if mixed_action_intent_count else 100.0,
            "Route_Accuracy": round(route_match_count / total_evaluated_cases * 100, 2) if total_evaluated_cases else 100.0,
            "Status_Accuracy": round(status_match_count / total_evaluated_cases * 100, 2) if total_evaluated_cases else 100.0,
        },
        "case_results": case_results,
    }
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["dev", "test", "holdout", "all"], default="all")
    parser.add_argument("--cases", type=Path, default=ROOT / "artifacts" / "evaluation_cases.jsonl")
    args = parser.parse_args()

    split_arg = None if args.split == "all" else args.split
    result = run_evaluation(cases_path=args.cases, split=split_arg)
    print(f"\n=================== RAG EVALUATION REPORT ({args.split.upper()}) ===================")
    print(f"Total Cases: {result['total_cases']}")
    for k, v in result["metrics"].items():
        print(f" - {k}: {v}{'%' if any(term in k for term in ('Rate', 'Accuracy', 'Hit', 'Recall', 'Coverage', 'Support')) else ''}")
    print("==================================================================\n")
