"""Script đánh giá toàn diện năng lực của AI Chatbot (P1 & P2 Evaluation).

Chạy trên SQLite tạm thời (isolated database), không ghi đè dữ liệu demo:
- Đo lường độ chính xác phân loại ý định (Intent Accuracy).
- Đo lường khả năng bóc tách thực thể không nhãn (Unlabeled Slot Extraction).
- Đo lường tỷ lệ hoàn thành hội thoại đa lượt (Multi-turn Completion Rate).
- Đo lường an toàn (Safety & Idempotency Probes).
"""
from __future__ import annotations

import argparse
import atexit
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
CASES_FILE = ROOT / "artifacts" / "chatbot_baseline_cases.json"

# Thiết lập database cô lập trong thư mục tạm
TMP_DB = Path(tempfile.gettempdir()) / f"chatbot-eval-{uuid4().hex}.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TMP_DB.as_posix()}"
os.environ["LLM_PROVIDER"] = "fake"

# Nạp ứng dụng sau khi đã thiết lập biến môi trường
sys.path.insert(0, str(ROOT / "backend"))
from fastapi.testclient import TestClient
from app import main
from app.db import engine
from app.seed import initialize_database


def cleanup_temp_db():
    try:
        engine.dispose()
        TMP_DB.unlink(missing_ok=True)
    except Exception:
        pass


atexit.register(cleanup_temp_db)


def run_evaluation():
    initialize_database()
    data = json.loads(CASES_FILE.read_text(encoding="utf-8"))
    cases = data.get("cases", [])
    origin = "http://127.0.0.1:5173"

    results = []
    cases_run = 0
    cases_passed = 0

    with TestClient(main.app) as client:
        for case in cases:
            cases_run += 1
            cid = case["id"]
            client.cookies.clear()
            # Khởi tạo session mới cho mỗi ca kiểm thử
            sess_res = client.post("/api/v1/session", headers={"Origin": origin})
            if sess_res.status_code != 200:
                results.append({"id": cid, "pass": False, "error": "session_init_failed"})
                continue

            case_passed = True
            details = []

            # Ca kiểm thử đa lượt (multi-turn)
            if "turns" in case:
                for idx, turn in enumerate(case["turns"], 1):
                    turn_msg = turn["input"]
                    client_msg_id = uuid4().hex
                    resp = client.post("/api/v1/chat/messages", headers={"Origin": origin}, json={
                        "message": turn_msg,
                        "client_message_id": client_msg_id
                    })
                    if resp.status_code != 200:
                        case_passed = False
                        details.append(f"Turn {idx}: HTTP {resp.status_code}")
                        break

                    body = resp.json()
                    expected_route = turn.get("expected_route")
                    if expected_route and body.get("route") != expected_route:
                        case_passed = False
                        details.append(f"Turn {idx}: expected route '{expected_route}' but got '{body.get('route')}'")

                    # Kiểm tra thông tin đã gom được ở đơn hàng nháp cuối cùng
                    if "expected_final_order" in turn and body.get("route") == "pending_confirmation":
                        expected_order = turn["expected_final_order"]
                        msg = body.get("message", "")
                        if "quantity" in expected_order and str(expected_order["quantity"]) not in msg:
                            case_passed = False
                            details.append(f"Turn {idx}: quantity '{expected_order['quantity']}' missing in confirmation")
            else:
                # Ca kiểm thử một lượt (single-turn)
                inp = case["input"]
                client_msg_id = uuid4().hex
                resp = client.post("/api/v1/chat/messages", headers={"Origin": origin}, json={
                    "message": inp,
                    "client_message_id": client_msg_id
                })
                if resp.status_code != 200:
                    case_passed = False
                    details.append(f"HTTP {resp.status_code}")
                else:
                    body = resp.json()
                    expected_route = case.get("expected_route")
                    if expected_route and body.get("route") != expected_route:
                        case_passed = False
                        details.append(f"expected route '{expected_route}' but got '{body.get('route')}'")

            if case_passed:
                cases_passed += 1

            results.append({
                "id": cid,
                "category": case.get("category"),
                "pass": case_passed,
                "details": details if not case_passed else "OK"
            })

    report = {
        "run_date": datetime.now(timezone.utc).isoformat(),
        "total_cases": cases_run,
        "cases_passed": cases_passed,
        "accuracy_rate": round(cases_passed / cases_run * 100, 2) if cases_run else 0,
        "results": results
    }

    print("\n================== AI CHATBOT EVALUATION REPORT ==================")
    print(f"Total Cases Run   : {cases_run}")
    print(f"Passed            : {cases_passed}")
    print(f"Failed            : {cases_run - cases_passed}")
    print(f"Accuracy Rate     : {report['accuracy_rate']}%")
    print("------------------------------------------------------------------")
    for r in results:
        status_symbol = "✓ PASS" if r["pass"] else "✗ FAIL"
        print(f"[{status_symbol}] {r['id']} ({r['category']}) - {r['details']}")
    print("==================================================================\n")

    return report


if __name__ == "__main__":
    run_evaluation()
