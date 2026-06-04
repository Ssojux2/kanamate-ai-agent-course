#!/usr/bin/env python3
"""5주차 '카나메이트 확장 예제'(mcp_history_agent)를 여러 모델로 반복 측정하는 비교 하니스.

같은 tool/프롬프트/요청을 고정한 채 모델만 바꿔가며(gpt-4o-mini -> gpt-4.1-mini -> gpt-5-mini)
- agent가 search -> load -> extract tool 연쇄를 스스로 수행하는지
- 모델이 커질수록 tool 호출 패턴/정답률/지연/토큰이 어떻게 변하는지
를 반복 측정해 분산과 함께 비교한다.

사용 예:
    uv run scripts/model_compare.py --repeat 5
    uv run scripts/model_compare.py --models gpt-4o-mini,gpt-4.1-mini,gpt-5-mini --repeat 5
    uv run scripts/model_compare.py --no-tool-names --repeat 5   # 프롬프트에서 tool 지정 제거(A/B 비교)
"""
from __future__ import annotations
# pyright: reportMissingImports=false

import argparse
import csv
import json
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

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
load_dotenv(REPO_ROOT / ".env", override=True)

# --- 5주차 노트북과 동일한 인메모리 데이터 (MCP SQLite 대용) ---
previous_conversations = [
    {"conversation_id": "conv-a", "title": "A 일정 공유", "last_message": "A는 다음 주 화요일 15:00 가능", "members": ["A"]},
    {"conversation_id": "conv-b", "title": "B 일정 공유", "last_message": "B는 다음 주 화요일 15:00 가능", "members": ["B"]},
    {"conversation_id": "conv-c", "title": "C 일정 공유", "last_message": "C는 다음 주 수요일 10:00보다 화요일 15:00 선호", "members": ["C"]},
]
conversation_messages = {
    "conv-a": [{"role": "assistant", "content": "A는 다음 주 화요일 15:00 가능해요."}],
    "conv-b": [{"role": "assistant", "content": "B는 다음 주 화요일 15:00 가능해요."}],
    "conv-c": [{"role": "assistant", "content": "C는 다음 주 수요일 10:00보다 화요일 15:00를 선호해요."}],
}


def _search(query: str, members: list[str] | None = None) -> str:
    members = members or []
    hits = [
        row for row in previous_conversations
        if not members or any(m in row["members"] for m in members) or query in row["last_message"]
    ]
    return json.dumps({"hits": hits}, ensure_ascii=False)


def _load(conversation_id: str) -> str:
    return json.dumps(
        {"conversation_id": conversation_id, "messages": conversation_messages.get(conversation_id, [])},
        ensure_ascii=False,
    )


def _extract(conversation_ids: list[str]) -> str:
    schedules = []
    for conversation_id in conversation_ids:
        for message in conversation_messages.get(conversation_id, []):
            text = message["content"]
            if "15:00" in text:
                member = conversation_id.replace("conv-", "").upper()
                schedules.append({
                    "conversation_id": conversation_id, "member": member,
                    "date_hint": "다음 주 화요일", "start_time": "15:00", "source": text,
                })
    return json.dumps({"schedules": schedules}, ensure_ascii=False)


# 도구 이름은 고정(코드 식별자). 바뀌는 것은 description(=각 도구의 정식 거처)뿐이다.
DESC_BASELINE = {
    "search_previous_conversations": "SQLite 이전 대화 목록에서 멤버나 질의와 관련된 대화를 검색한다.",
    "load_conversation_messages": "conversation_id에 해당하는 이전 대화 메시지를 불러온다.",
    "extract_schedules_from_history": "이전 대화 메시지에서 멤버별 가능 일정 후보를 추출한다.",
}
# 리치 description: 순서/역할/선택 기준을 도구 설명에 담아, 시스템 프롬프트에서 이름을 중복하지 않고도 워크플로우를 유도한다.
DESC_RICH = {
    "search_previous_conversations": (
        "팀원 일정·가능 시간 질문에 답하기 위한 첫 단계 도구다. 멤버 이름이나 질의로 관련 이전 대화 "
        "목록을 conversation_id와 함께 찾는다. 어떤 답이든 추측하지 말고 반드시 이 검색으로 근거 대화를 "
        "먼저 확보한 뒤 다음 단계로 넘어간다."
    ),
    "load_conversation_messages": (
        "특정 한 대화의 원문 메시지를 그대로 읽어야 할 때만 쓰는 보조 도구다. 멤버별 가능 시간 후보를 "
        "모으는 목적이라면 대화를 하나씩 펼치지 말고 후보 추출 도구를 사용하는 편이 정확하고 효율적이다."
    ),
    "extract_schedules_from_history": (
        "검색으로 확보한 대화들(conversation_id 목록)에서 멤버별 가능 시간 후보를 한 번에 구조화해 뽑는 "
        "도구다. 가능 시간을 종합·결정하기 직전, 반드시 이 단계로 후보 근거를 확보한다. 대화 원문을 "
        "일일이 펼치지 않아도 후보를 정리해 돌려준다."
    ),
}


def build_tools(rich: bool):
    desc = DESC_RICH if rich else DESC_BASELINE
    return [
        tool("search_previous_conversations", description=desc["search_previous_conversations"])(_search),
        tool("load_conversation_messages", description=desc["load_conversation_messages"])(_load),
        tool("extract_schedules_from_history", description=desc["extract_schedules_from_history"])(_extract),
    ]


# 노트북 원본 프롬프트(= tool 이름/순서를 명시)
PROMPT_WITH_NAMES = (
    "너는 카나메이트 이전 대화 검색 agent다. 사용자가 팀원들의 과거 일정이나 가능 시간을 물으면 "
    "반드시 search_previous_conversations로 관련 대화를 찾고, 필요하면 load_conversation_messages와 "
    "extract_schedules_from_history를 호출해 근거를 확인한 뒤 답한다."
)
# 자율 선택 버전: tool 이름/순서를 빼고 목표만 제시
PROMPT_NO_NAMES = (
    "너는 카나메이트 이전 대화 검색 agent다. 사용자가 팀원들의 과거 가능 시간을 물으면 "
    "이전 대화 기록을 근거로 확인한 뒤 답한다. 어떤 도구를 어떤 순서로 쓸지는 네가 판단한다."
)
# 워크플로우 버전: tool 이름은 한 번도 쓰지 않고, 도메인 동사(검색→후보 추출→종합)로 절차만 기술한다.
PROMPT_WORKFLOW = (
    "너는 카나메이트 일정 조율 agent다. 사용자가 팀원들의 과거 대화를 근거로 가능한 회의 시간을 물으면 "
    "다음 절차로 답한다. "
    "(1) 관련 이전 대화를 검색해 근거 대화를 확보한다. "
    "(2) 확보한 대화들에서 멤버별 가능 시간 후보를 구조화해 추출한다. "
    "(3) 모두가 가능한 시간을 하나 골라 그 이유와 함께 답한다. "
    "추측으로 답하지 말고 반드시 도구로 확보한 근거에 기반해 답한다."
)
# 정책 버전: 경로(도구/순서)는 강제하지 않고 '결과 속성'(근거 확보·추측 금지)만 요구한다.
PROMPT_POLICY = (
    "너는 카나메이트 일정 조율 agent다. 사용자가 팀원들의 가능한 회의 시간을 물으면, "
    "추측하거나 검색 결과의 요약만 보고 답하지 말고 반드시 실제 대화 근거를 확인한 뒤, "
    "모두가 가능한 시간을 하나 골라 이유와 함께 답한다. "
    "어떤 도구를 어떤 순서로 쓸지는 스스로 판단한다."
)
PROMPTS = {
    "with-names": PROMPT_WITH_NAMES,
    "no-names": PROMPT_NO_NAMES,
    "workflow": PROMPT_WORKFLOW,
    "policy": PROMPT_POLICY,
}

REQUEST = "팀원 A/B/C와 다음 주 회의 시간을 잡으려면 이전 대화에서 가능한 시간을 찾아줘."


def build_model(name: str, max_tokens: int) -> ChatOpenAI:
    """모델별 파라미터 차이를 흡수한다. gpt-5* 는 temperature=0 미지원 + reasoning 토큰 필요."""
    kwargs: dict[str, Any] = {"model": name, "timeout": 90}
    if name.startswith("gpt-5"):
        # 기본 temperature(1)만 허용 → temperature 미지정. reasoning 여유분 확보.
        kwargs["max_completion_tokens"] = max(max_tokens, 4000)
    else:
        kwargs["temperature"] = 0
        kwargs["max_completion_tokens"] = max_tokens
    return ChatOpenAI(**kwargs)


def extract_tool_trace(result: dict[str, Any]) -> list[dict[str, Any]]:
    trace = []
    for message in result.get("messages", []):
        for call in getattr(message, "tool_calls", []) or []:
            trace.append({"event": "tool_call", "tool_name": call.get("name"), "arguments": call.get("args", {})})
        if getattr(message, "type", None) == "tool":
            trace.append({"event": "tool_result", "tool_name": getattr(message, "name", None)})
    return trace


def sum_usage(result: dict[str, Any]) -> tuple[int, int, int]:
    in_t = out_t = tot = 0
    for m in result.get("messages", []):
        um = getattr(m, "usage_metadata", None)
        if um:
            in_t += um.get("input_tokens", 0)
            out_t += um.get("output_tokens", 0)
            tot += um.get("total_tokens", 0)
    return in_t, out_t, tot


def run_once(model_name: str, system_prompt: str, max_tokens: int, tools: list) -> dict[str, Any]:
    """1회 실행 → 측정 지표 dict."""
    rec: dict[str, Any] = {"model": model_name, "ok": False, "error": None}
    try:
        agent = create_agent(model=build_model(model_name, max_tokens), tools=tools, system_prompt=system_prompt)
        t0 = time.perf_counter()
        result = agent.invoke({"messages": [{"role": "user", "content": REQUEST}]})
        rec["latency_s"] = round(time.perf_counter() - t0, 2)

        trace = extract_tool_trace(result)
        calls = [e["tool_name"] for e in trace if e["event"] == "tool_call"]
        final = result["messages"][-1].content or ""

        rec["ok"] = True
        rec["tool_seq"] = calls
        rec["n_tool_calls"] = len(calls)
        rec["n_search"] = calls.count("search_previous_conversations")
        rec["n_load"] = calls.count("load_conversation_messages")
        rec["n_extract"] = calls.count("extract_schedules_from_history")
        rec["search_called"] = rec["n_search"] > 0
        rec["search_first"] = bool(calls) and calls[0] == "search_previous_conversations"
        rec["load_called"] = rec["n_load"] > 0
        rec["extract_called"] = rec["n_extract"] > 0
        # 근거 확보: 검색 후 실제 대화 원문(load) 또는 구조화 후보(extract) 중 하나라도 확인했는가
        rec["grounded"] = rec["search_called"] and (rec["load_called"] or rec["extract_called"])
        # 위험: 검색 요약(last_message)만 보고 원문/후보 확인 없이 답 → 할루시네이션 가능 구간
        rec["search_only"] = rec["search_called"] and not rec["load_called"] and not rec["extract_called"]
        # 정답: 화요일 15:00 결론에 도달했는가
        rec["correct"] = ("15:00" in final) and ("화요일" in final)
        rec["final_text"] = final.strip()
        in_t, out_t, tot = sum_usage(result)
        rec["in_tokens"], rec["out_tokens"], rec["total_tokens"] = in_t, out_t, tot
    except Exception as e:  # noqa: BLE001 - 모델별 호출 실패를 그대로 기록
        rec["error"] = f"{type(e).__name__}: {e}"[:300]
    return rec


def aggregate(model_name: str, runs: list[dict[str, Any]]) -> dict[str, Any]:
    ok = [r for r in runs if r["ok"]]
    n = len(runs)

    def rate(pred) -> str:
        if not ok:
            return "-"
        return f"{sum(1 for r in ok if pred(r))}/{len(ok)}"

    def mean(key) -> float | None:
        vals = [r[key] for r in ok if isinstance(r.get(key), (int, float))]
        return round(statistics.mean(vals), 1) if vals else None

    seq_sig = Counter(" → ".join(r["tool_seq"]) for r in ok)
    modal_seq = seq_sig.most_common(1)[0] if seq_sig else ("(없음)", 0)
    return {
        "model": model_name,
        "runs": n,
        "ok": len(ok),
        "correct": rate(lambda r: r["correct"]),
        "grounded": rate(lambda r: r["grounded"]),
        "search_only": rate(lambda r: r["search_only"]),
        "search_called": rate(lambda r: r["search_called"]),
        "extract_called": rate(lambda r: r["extract_called"]),
        "avg_tool_calls": mean("n_tool_calls"),
        "avg_n_load": mean("n_load"),
        "avg_latency_s": mean("latency_s"),
        "avg_total_tokens": mean("total_tokens"),
        "modal_seq": f"{modal_seq[0]}  (×{modal_seq[1]})",
        "errors": [r["error"] for r in runs if r["error"]],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="gpt-4o-mini,gpt-4.1-mini,gpt-5-mini",
                    help="쉼표 구분. 모델별 반복은 'name:N'으로 지정(예: gpt-5-mini:1,gpt-4.1-mini:5)")
    ap.add_argument("--repeat", type=int, default=5, help="name:N 미지정 모델의 기본 반복 횟수")
    ap.add_argument("--max-tokens", type=int, default=900)
    ap.add_argument("--prompt", choices=list(PROMPTS), default="with-names",
                    help="시스템 프롬프트 모드: with-names(이름 명시) / no-names(자율) / workflow(이름 없이 절차 기술)")
    ap.add_argument("--rich-desc", action="store_true",
                    help="tool description을 리치 버전으로 교체(순서/역할/선택 기준을 설명에 담음)")
    ap.add_argument("--out-dir", default=str(REPO_ROOT / "tmp"))
    args = ap.parse_args()

    # "name" 또는 "name:N" 파싱 → (모델명, 반복횟수)
    model_specs: list[tuple[str, int]] = []
    for token in args.models.split(","):
        token = token.strip()
        if not token:
            continue
        if ":" in token:
            name, rep = token.rsplit(":", 1)
            model_specs.append((name.strip(), int(rep)))
        else:
            model_specs.append((token, args.repeat))
    system_prompt = PROMPTS[args.prompt]
    tools = build_tools(args.rich_desc)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rep_desc = ", ".join(f"{n}×{r}" for n, r in model_specs)
    print(f"\n실험: 5주차 mcp_history_agent | prompt={args.prompt} | desc={'rich' if args.rich_desc else 'baseline'} | {rep_desc}")
    print(f"요청: {REQUEST}\n")

    all_runs: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for model_name, repeat in model_specs:
        print(f"── {model_name} (×{repeat}) ──")
        runs = []
        for i in range(repeat):
            rec = run_once(model_name, system_prompt, args.max_tokens, tools)
            rec["run"] = i + 1
            runs.append(rec)
            all_runs.append(rec)
            if rec["ok"]:
                tag = "✓" if rec["correct"] else "✗"
                print(f"  run{i+1}: {tag} seq=[{' → '.join(rec['tool_seq'])}] "
                      f"calls={rec['n_tool_calls']} {rec['latency_s']}s tok={rec['total_tokens']}")
            else:
                print(f"  run{i+1}: ERROR {rec['error']}")
        summaries.append(aggregate(model_name, runs))

    # --- 비교 표 출력 ---
    print("\n=========================== 모델 비교 요약 ===========================")
    cols = ["model", "ok", "correct", "grounded", "search_only", "extract_called",
            "avg_tool_calls", "avg_n_load", "avg_latency_s", "avg_total_tokens"]
    widths = {c: max(len(c), *(len(str(s.get(c, ""))) for s in summaries)) for c in cols}
    print(" | ".join(c.ljust(widths[c]) for c in cols))
    print("-+-".join("-" * widths[c] for c in cols))
    for s in summaries:
        print(" | ".join(str(s.get(c, "")).ljust(widths[c]) for c in cols))
    print()
    for s in summaries:
        print(f"  · {s['model']:14s} modal_seq: {s['modal_seq']}")
        if s["errors"]:
            print(f"      errors: {s['errors'][:2]}")

    # --- 저장 ---
    raw_path = out_dir / f"model_compare_{stamp}.json"
    raw_path.write_text(json.dumps({"args": vars(args), "runs": all_runs, "summary": summaries},
                                   ensure_ascii=False, indent=2), encoding="utf-8")
    csv_path = out_dir / f"model_compare_{stamp}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols + ["modal_seq"])
        w.writeheader()
        for s in summaries:
            w.writerow({k: s.get(k, "") for k in cols + ["modal_seq"]})
    print(f"\n저장: {raw_path}\n      {csv_path}")


if __name__ == "__main__":
    main()
