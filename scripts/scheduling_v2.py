#!/usr/bin/env python3
"""5주차 개선 예제: '말한 가용성' × '기존 일정(딕셔너리)' 교차 참조.

기존 mock(`if "15:00" in text`)을 걷어내고, 두 개의 서로 다른 근거 소스를 둔다.
  소스1 conversation_messages : 멤버가 "언제 된다고 말했나"(가용성)
  소스2 member_schedules(dict): 멤버가 "이미 무엇에 잡혀있나"(충돌)
함정: 대화상 모두 화 15:00 가능이라 말하지만, A는 화 15:00에 기존 일정이 있다.
  → 정답은 충돌 없는 목 14:00.
  → load_member_schedules(충돌 확인)를 생략하면 잘못된 화 15:00을 답하게 된다.

사용:
    uv run scripts/scheduling_v2.py --models "gpt-4o-mini:5,gpt-4.1-mini:5,gpt-5-mini:1"
"""
from __future__ import annotations
# pyright: reportMissingImports=false

import argparse
import json
import re
import statistics
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env", override=True)

# --- 소스1: 멤버가 말한 가용성(대화) ---
# 주의: last_message(요약)에는 '구체 시간'을 흘리지 않는다. 실제 시간은 conversation_messages(원문)에만 있다.
#       → 가용성을 알려면 반드시 extract_candidate_slots로 원문을 파싱해야 한다(도구를 구조적으로 필수화).
previous_conversations = [
    {"conversation_id": "conv-a", "title": "A 일정 공유", "last_message": "A가 다음 주 가능한 회의 시간을 공유함", "members": ["A"]},
    {"conversation_id": "conv-b", "title": "B 일정 공유", "last_message": "B가 다음 주 가능한 회의 시간을 공유함", "members": ["B"]},
    {"conversation_id": "conv-c", "title": "C 일정 공유", "last_message": "C가 다음 주 가능한 회의 시간을 공유함", "members": ["C"]},
]
conversation_messages = {
    "conv-a": [{"role": "assistant", "content": "A는 다음 주 화요일 15:00 가능하고, 목요일 14:00도 괜찮아요."}],
    "conv-b": [{"role": "assistant", "content": "B는 다음 주 화요일 15:00과 목요일 14:00 둘 다 가능해요."}],
    "conv-c": [{"role": "assistant", "content": "C는 다음 주 화요일 15:00 좋고, 목요일 14:00도 가능해요."}],
}
# --- 소스2: 이미 잡혀있는 일정(딕셔너리) — 충돌 확인용. A가 화 15:00에 선약이 있다(함정) ---
member_schedules = {
    "A": [{"day": "화요일", "start_time": "15:00", "title": "기존 팀 회의"}],
    "B": [],
    "C": [],
}

DAY_TIME = re.compile(r"([월화수목금토일]요일)\s*([0-2]?\d:[0-5]\d)")


def _search(query: str, members: list[str] | None = None) -> str:
    members = members or []
    hits = [r for r in previous_conversations
            if not members or any(m in r["members"] for m in members) or query in r["last_message"]]
    return json.dumps({"hits": hits}, ensure_ascii=False)


def _extract_candidates(conversation_ids: list[str]) -> str:
    """대화에서 각 멤버가 '가능하다고 말한' (요일, 시간) 후보를 파싱한다."""
    candidates = []
    for cid in conversation_ids:
        member = cid.replace("conv-", "").upper()
        for msg in conversation_messages.get(cid, []):
            for day, t in DAY_TIME.findall(msg["content"]):
                candidates.append({"member": member, "day": day, "start_time": t, "source": msg["content"]})
    return json.dumps({"candidates": candidates}, ensure_ascii=False)


def _load_schedules(members: list[str]) -> str:
    """멤버들이 이미 잡아둔 기존 일정을 가져온다(충돌 확인용)."""
    return json.dumps({"existing": {m: member_schedules.get(m, []) for m in members}}, ensure_ascii=False)


def build_tools():
    return [
        tool("search_previous_conversations",
             description="팀원 일정 질문의 첫 단계. 멤버 이름이나 질의로 관련 이전 대화를 conversation_id와 함께 찾는다.")(_search),
        tool("extract_candidate_slots",
             description="찾은 대화들(conversation_id 목록)에서 각 멤버가 가능하다고 말한 (요일, 시간) 후보를 뽑는다.")(_extract_candidates),
        tool("load_member_schedules",
             description=("멤버들이 이미 잡아둔 기존 일정을 가져온다. 후보 시간을 최종 확정하기 전, 그 시간에 "
                          "충돌하는 기존 일정이 없는지 반드시 이 도구로 확인한다."))(_load_schedules),
    ]


# 경로는 강제하지 않고(도구/순서 자유), 확인해야 할 '근거 속성'만 요구한다.
SYSTEM_PROMPT = (
    "너는 카나메이트 일정 조율 agent다. 팀원들의 회의 시간을 정할 때 추측하지 말고, "
    "(1) 각 팀원이 가능하다고 말한 시간과 (2) 각 팀원이 이미 잡아둔 기존 일정을 모두 근거로 확인한 뒤, "
    "모두가 가능하면서 누구의 기존 일정과도 겹치지 않는 시간을 하나 골라 이유와 함께 답한다. "
    "어떤 도구를 어떤 순서로 쓸지는 스스로 판단한다."
)
REQUEST = "팀원 A/B/C와 다음 주 회의 시간을 잡아줘. 모두 되고 기존 일정과 안 겹치는 시간으로."


def build_model(name: str, max_tokens: int = 1200) -> ChatOpenAI:
    kwargs: dict[str, Any] = {"model": name, "timeout": 90}
    if name.startswith("gpt-5"):
        kwargs["max_completion_tokens"] = max(max_tokens, 4000)
    else:
        kwargs["temperature"] = 0
        kwargs["max_completion_tokens"] = max_tokens
    return ChatOpenAI(**kwargs)


def trace_of(result: dict[str, Any]) -> list[str]:
    calls = []
    for m in result.get("messages", []):
        for c in getattr(m, "tool_calls", []) or []:
            calls.append(c.get("name"))
    return calls


def run_once(model_name: str, tools: list) -> dict[str, Any]:
    rec: dict[str, Any] = {"model": model_name, "ok": False, "error": None}
    try:
        agent = create_agent(model=build_model(model_name), tools=tools, system_prompt=SYSTEM_PROMPT)
        t0 = time.perf_counter()
        result = agent.invoke({"messages": [{"role": "user", "content": REQUEST}]})
        rec["latency_s"] = round(time.perf_counter() - t0, 2)
        calls = trace_of(result)
        final = (result["messages"][-1].content or "").strip()
        rec["ok"] = True
        rec["tool_seq"] = calls
        rec["extract_called"] = "extract_candidate_slots" in calls  # 가용성 원문 파싱(요약에 시간 없으니 필수)
        rec["schedules_checked"] = "load_member_schedules" in calls  # 충돌 확인했나(핵심 grounding)
        rec["full_chain"] = ("search_previous_conversations" in calls) and rec["extract_called"] and rec["schedules_checked"]
        rec["picked_thursday"] = ("목요일" in final) and ("14:00" in final)  # 정답: 충돌 피해 목 14:00
        rec["picked_tuesday_15"] = ("화요일" in final) and ("15:00" in final) and ("목요일" not in final)  # 함정에 빠짐
        rec["correct"] = rec["picked_thursday"] and not rec["picked_tuesday_15"]
        rec["final_text"] = final
    except Exception as e:  # noqa: BLE001
        rec["error"] = f"{type(e).__name__}: {e}"[:300]
    return rec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="gpt-4o-mini:5,gpt-4.1-mini:5,gpt-5-mini:1")
    ap.add_argument("--repeat", type=int, default=5)
    args = ap.parse_args()

    specs = []
    for tok in args.models.split(","):
        tok = tok.strip()
        if not tok:
            continue
        name, _, rep = tok.partition(":")
        specs.append((name.strip(), int(rep) if rep else args.repeat))

    tools = build_tools()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print("\n개선 예제: 말한 가용성 × 기존 일정(dict) 충돌 확인")
    print(f"함정: 대화상 모두 화 15:00 가능이지만 A는 화 15:00 선약 → 정답은 목 14:00")
    print(f"요청: {REQUEST}\n")

    all_runs, summaries = [], []
    for name, rep in specs:
        print(f"── {name} (×{rep}) ──")
        runs = []
        for i in range(rep):
            r = run_once(name, tools)
            runs.append(r)
            all_runs.append(r)
            if r["ok"]:
                verdict = "✓목14:00" if r["correct"] else ("✗화15:00함정" if r["picked_tuesday_15"] else "✗기타")
                chk = "DB확인O" if r["schedules_checked"] else "DB확인X"
                print(f"  run{i+1}: {verdict} [{chk}] seq=[{' → '.join(r['tool_seq'])}] {r['latency_s']}s")
            else:
                print(f"  run{i+1}: ERROR {r['error']}")
        ok = [r for r in runs if r["ok"]]

        def rate(pred):
            return f"{sum(1 for r in ok if pred(r))}/{len(ok)}" if ok else "-"
        summaries.append({
            "model": name,
            "correct(목14:00)": rate(lambda r: r["correct"]),
            "extract_called": rate(lambda r: r["extract_called"]),
            "schedules_checked": rate(lambda r: r["schedules_checked"]),
            "full_chain": rate(lambda r: r["full_chain"]),
            "fell_for_trap(화15:00)": rate(lambda r: r["picked_tuesday_15"]),
            "avg_latency_s": round(statistics.mean([r["latency_s"] for r in ok]), 1) if ok else None,
            "modal_seq": Counter(" → ".join(r["tool_seq"]) for r in ok).most_common(1)[0][0] if ok else "-",
        })

    print("\n===================== 충돌 인지 비교 =====================")
    cols = ["model", "correct(목14:00)", "extract_called", "schedules_checked", "full_chain", "fell_for_trap(화15:00)", "avg_latency_s"]
    w = {c: max(len(c), *(len(str(s[c])) for s in summaries)) for c in cols}
    print(" | ".join(c.ljust(w[c]) for c in cols))
    print("-+-".join("-" * w[c] for c in cols))
    for s in summaries:
        print(" | ".join(str(s[c]).ljust(w[c]) for c in cols))
    print()
    for s in summaries:
        print(f"  · {s['model']:14s} {s['modal_seq']}")

    out = REPO_ROOT / "tmp" / f"scheduling_v2_{stamp}.json"
    out.write_text(json.dumps({"runs": all_runs, "summary": summaries}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n저장: {out}")


if __name__ == "__main__":
    main()
