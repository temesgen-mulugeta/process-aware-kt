"""
llm_analyzer.py — the offline Gemini "process analyzer".

For each *historical* interaction we make ONE Gemini call (temperature 0,
JSON-schema-constrained) that turns the student's solution into structured
features describing WHAT ALREADY HAPPENED. It never predicts the future and
never sees a target question's solution — callers only ever pass past
interactions, so leakage is structurally impossible here.

Key properties (brief Section 7):
  * temperature 0 + response_schema  -> constrained output; cache enables repeatability
  * disk cache keyed by sha256(prompt + model)  -> re-runs make zero API calls
  * malformed output -> retry once -> null-feature placeholder (logged)

Run a quick smoke test:   python -m src.llm_analyzer --smoke
Validate vs gold (7a):    python -m src.llm_analyzer --validate
Extract all history:      python -m src.llm_analyzer --extract
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from typing import Literal, Optional

from pydantic import BaseModel, ValidationError

from src import config as C

# When set, analyze() returns deterministic SYNTHETIC features instead of calling
# Gemini — lets us verify the whole downstream pipeline without a real API key.
# Mock features are clearly NOT real; never report mock-based metrics as results.
MOCK = os.environ.get("KT_MOCK_ANALYZER", "") == "1"

# Bump this when the prompt or schema changes, so the cache invalidates cleanly.
PROMPT_VERSION = "v1"

# Error-type enum exactly as the brief specifies (analyzer's own classification).
ErrorTypeLiteral = Literal[
    "wrong_operation_or_concept",
    "lack_of_concepts",
    "calculation_error",
    "incomplete_answer",
    "careless_error",
    "none",
]


class AnalyzerOutput(BaseModel):
    """The exact JSON the analyzer must return (brief Section 7)."""
    associated_concepts: list[str]      # concepts required to solve (from the 55)
    missing_concepts: list[str]         # concepts the student failed to apply ([] if correct)
    error_type: ErrorTypeLiteral
    faulty_step: str                    # the specific erroneous expression, or ""
    partial_understanding: list[str]    # short phrases: what the student did right
    process_summary: str                # 1–2 plain-English sentences


# Null placeholder used when the API/validation fails (keeps the pipeline running).
NULL_OUTPUT = AnalyzerOutput(
    associated_concepts=[],
    missing_concepts=[],
    error_type="none",
    faulty_step="",
    partial_understanding=[],
    process_summary="",
)


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------
_CONCEPT_LIST_BLOCK = "\n".join(f"- {c}" for c in C.CONCEPTS)

_SYSTEM_INSTRUCTION = (
    "You are a meticulous math-education analyst. You are given ONE student's "
    "already-completed solution to a math problem. Your job is to DESCRIBE what "
    "happened in that solution — you are not solving the problem yourself and you "
    "are NOT predicting anything about future problems.\n\n"
    "You must choose concepts ONLY from the provided fixed list of 55 concepts, "
    "using the exact strings. Never invent a concept name. If the answer is "
    "correct, missing_concepts must be empty and error_type must be \"none\"."
)


def build_prompt(rec: dict) -> str:
    """Build the analyzer user prompt for one interaction record.

    Uses question text only if available (MathEDU usually lacks it — see
    data_prep.py); otherwise the analyzer works from the solution + answer +
    correctness, which is enough to characterize the *process*.
    """
    q = rec.get("question_text")
    question_block = f"Problem statement:\n{q}\n\n" if q else (
        "Problem statement: (not available; infer the task from the student's work)\n\n"
    )
    correctness = "correct" if rec["correct"] else "incorrect"
    return (
        f"The 55 allowed concepts (choose only from these, exact strings):\n"
        f"{_CONCEPT_LIST_BLOCK}\n\n"
        f"{question_block}"
        f"Student's final answer: {rec.get('student_answer', '')!r}\n\n"
        f"Student's solution process (LaTeX):\n{rec.get('student_process', '')}\n\n"
        f"This answer was graded as: {correctness}.\n\n"
        f"Analyze the solution above and return the structured JSON. "
        f"For a correct answer, list the associated_concepts it exercises, set "
        f"missing_concepts to [], error_type to \"none\", and faulty_step to \"\". "
        f"For an incorrect answer, identify the associated_concepts the problem "
        f"requires, the missing_concepts the student failed to apply, the single "
        f"error_type that best fits, and the faulty_step (the exact erroneous "
        f"expression). Always fill partial_understanding and a short process_summary."
    )


# ---------------------------------------------------------------------------
# Disk cache
# ---------------------------------------------------------------------------
def _cache_key(prompt: str) -> str:
    h = hashlib.sha256(f"{PROMPT_VERSION}|{C.GEMINI_MODEL}|{prompt}".encode("utf-8"))
    return h.hexdigest()


def _cache_path(key: str):
    return C.LLM_FEATURES / f"{key}.json"


def _load_cache(key: str) -> Optional[dict]:
    p = _cache_path(key)
    if p.exists():
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return None


def _save_cache(key: str, payload: dict) -> None:
    with open(_cache_path(key), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)


# ---------------------------------------------------------------------------
# Gemini client (lazy, so importing this module never requires a key)
# ---------------------------------------------------------------------------
_client = None
# Simple counter so tests can assert "re-run made zero API calls".
API_CALLS = 0


def _get_client():
    global _client
    if _client is None:
        if not C.have_gemini_key():
            raise RuntimeError("GEMINI_API_KEY not set (put it in .env).")
        from google import genai
        _client = genai.Client()        # auto-reads GEMINI_API_KEY
    return _client


def _raw_gemini_call(prompt: str) -> AnalyzerOutput:
    """One temperature-0, schema-constrained Gemini call. Raises on failure."""
    global API_CALLS
    from google.genai import types

    client = _get_client()
    API_CALLS += 1
    resp = client.models.generate_content(
        model=C.GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM_INSTRUCTION,
            temperature=0,
            response_mime_type="application/json",
            response_schema=AnalyzerOutput,
        ),
    )
    # Prefer the SDK's parsed object; fall back to manual JSON parse.
    parsed = getattr(resp, "parsed", None)
    if isinstance(parsed, AnalyzerOutput):
        return parsed
    if not isinstance(resp.text, str):
        raise ValueError("Gemini returned no JSON text")
    return AnalyzerOutput.model_validate(json.loads(resp.text))


def _sanitize(out: AnalyzerOutput, rec: dict) -> AnalyzerOutput:
    """Keep only valid concept strings; enforce correct-answer invariants."""
    assoc = [c for c in out.associated_concepts if c in C.CONCEPT_TO_ID]
    miss = [c for c in out.missing_concepts if c in C.CONCEPT_TO_ID]
    error_type = out.error_type
    if rec["correct"]:
        miss = []
        error_type = "none"
    return out.model_copy(update={
        "associated_concepts": list(dict.fromkeys(assoc)),
        "missing_concepts": list(dict.fromkeys(miss)),
        "error_type": error_type,
    })


def analyze(rec: dict, use_cache: bool = True) -> AnalyzerOutput:
    """Analyze one interaction. Cached on disk; one API call on cache miss.

    Failure policy (deliberately split):
      * Malformed MODEL OUTPUT (bad JSON / schema)  -> retry once -> cache a
        NULL placeholder and continue. These are genuine per-record failures.
      * API/infrastructure errors (bad key, 4xx/5xx) -> retry once -> RAISE.
        We never cache these, so the run can be retried once the key is fixed.
    """
    if MOCK:
        return _mock_analyze(rec)

    prompt = build_prompt(rec)
    key = _cache_key(prompt)

    if use_cache:
        cached = _load_cache(key)
        if cached is not None:
            return AnalyzerOutput(**cached["output"])

    from google.genai import errors as genai_errors

    # Parsing, schema validation and sanitation belong inside the retry boundary.
    for attempt in (1, 2):
        try:
            out = _sanitize(_raw_gemini_call(prompt), rec)
            break
        except genai_errors.APIError as e:
            if attempt == 2:
                raise RuntimeError(
                    f"Gemini API error for id={rec['id']} (not cached, safe to retry): {e}"
                ) from e
            time.sleep(1.0)
        except (ValidationError, json.JSONDecodeError, ValueError) as e:
            if attempt == 1:
                continue
            sys.stderr.write(f"[analyzer] malformed output id={rec['id']}: {e}\n")
            out = NULL_OUTPUT
            _save_cache(key, {"id": rec["id"], "student_id": rec["student_id"],
                              "output": out.model_dump(), "failed": True, "error": str(e)})
            return out

    _save_cache(key, {"id": rec["id"], "student_id": rec["student_id"],
                      "output": out.model_dump()})
    return out


def _mock_analyze(rec: dict) -> AnalyzerOutput:
    """Deterministic synthetic analyzer output for offline pipeline verification.

    NOT a real analysis. It exercises every feature dimension:
      * associated_concepts = gold associated (a known property of the question,
        available at prediction time — not leakage)
      * missing_concepts    = [] (we must NOT inject gold missing here, or arm B
        would trivially equal arm C)
      * error_type          = normalized gold error type (input feature, not target)
      * process_summary     = deterministic text so the summary embedder has signal
    """
    return AnalyzerOutput(
        associated_concepts=list(rec.get("associated_concepts") or []),
        missing_concepts=[],
        error_type=rec.get("error_type", "none"),
        faulty_step=(rec.get("error_equation") or ""),
        partial_understanding=(["computed intermediate steps"] if not rec["correct"] else ["solved correctly"]),
        process_summary=(
            f"Student {'correctly solved' if rec['correct'] else 'made a ' + rec.get('error_type','none') + ' on'} "
            f"a problem involving {', '.join((rec.get('associated_concepts') or ['general arithmetic'])[:2])}."
        ),
    )


# ---------------------------------------------------------------------------
# Batch extraction over the *history* (training) interactions
# ---------------------------------------------------------------------------
def _load_table() -> list[dict]:
    with open(C.PROCESSED_TABLE, encoding="utf-8") as f:
        return json.load(f)


def extract_all(records: list[dict], workers: int = 8) -> dict[tuple[int, int], AnalyzerOutput]:
    """Analyze every given record, returning {(id, student_id): AnalyzerOutput}.

    Cache hits are resolved first (no threads); only cache misses hit the API,
    concurrently across `workers` threads. Each call writes its own cache file,
    so the disk cache stays consistent. Set workers=1 for fully sequential.
    """
    from tqdm import tqdm

    out: dict[tuple[int, int], AnalyzerOutput] = {}
    todo: list[dict] = []
    for rec in records:                                  # serve cache hits up front
        if not MOCK and use_cached(rec):
            out[(rec["id"], rec["student_id"])] = analyze(rec)
        else:
            todo.append(rec)

    if not todo:
        return out

    if workers <= 1 or MOCK:
        for rec in tqdm(todo, desc="analyzing"):
            out[(rec["id"], rec["student_id"])] = analyze(rec)
        return out

    from concurrent.futures import ThreadPoolExecutor, as_completed
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(analyze, rec): rec for rec in todo}
        for fut in tqdm(as_completed(futs), total=len(futs), desc="analyzing"):
            rec = futs[fut]
            out[(rec["id"], rec["student_id"])] = fut.result()
    return out


def use_cached(rec: dict) -> bool:
    """True if this record's analyzer output is already on disk."""
    return _cache_path(_cache_key(build_prompt(rec))).exists()


# ---------------------------------------------------------------------------
# 7a — validate the analyzer against gold teacher annotations before trusting it
# ---------------------------------------------------------------------------
def validate_against_gold(n: int = 20) -> str:
    """Compare analyzer error_type / faulty_step to gold on ~n incorrect records."""
    table = _load_table()
    # incorrect records that have a gold error_type and an error_equation to compare faulty_step
    gold = [r for r in table
            if not r["correct"] and r["raw_error_type"] and r["error_equation"]]
    gold = gold[:n]

    rows, et_hits = [], 0
    for r in gold:
        out = analyze(r)
        gold_et = C.normalize_error_type(r["raw_error_type"])
        et_match = (out.error_type == gold_et)
        et_hits += et_match
        # crude faulty_step overlap: does the predicted step share tokens with gold equation?
        fs_overlap = _token_overlap(out.faulty_step, r["error_equation"])
        rows.append((r["id"], gold_et, out.error_type, et_match, fs_overlap,
                     r["error_equation"], out.faulty_step))

    agree = et_hits / len(gold) if gold else 0.0
    L = ["# Analyzer validation (7a) — vs gold teacher annotations\n",
         f"Model: `{C.GEMINI_MODEL}` | compared {len(gold)} incorrect records.\n",
         f"**error_type agreement: {et_hits}/{len(gold)} = {agree:.0%}**\n",
         "| id | gold error_type | pred error_type | match | faulty_step token-overlap |",
         "|---|---|---|:--:|---:|"]
    for (rid, g, p, m, ov, _eq, _fs) in rows:
        L.append(f"| {rid} | {g} | {p} | {'✓' if m else '✗'} | {ov:.2f} |")
    L.append("\n### Examples (gold error_equation vs predicted faulty_step)\n")
    for (rid, _g, _p, _m, _ov, eq, fs) in rows[:8]:
        L.append(f"- **{rid}** gold=`{eq}`  pred=`{fs}`")
    L.append(f"\n**Verdict:** {'reasonable — proceed to full extraction.' if agree >= 0.4 else 'low agreement — inspect prompt before trusting.'}")
    return "\n".join(L)


def _token_overlap(a: str, b: str) -> float:
    """Jaccard overlap of non-trivial tokens (rough faulty_step similarity)."""
    ta = {t for t in _tok(a) if len(t) > 1}
    tb = {t for t in _tok(b) if len(t) > 1}
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _tok(s: str) -> list[str]:
    import re
    return re.findall(r"[A-Za-z0-9]+", (s or "").lower())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true", help="analyze 3 records and print JSON")
    ap.add_argument("--validate", action="store_true", help="write results/analyzer_validation.md")
    ap.add_argument("--extract", action="store_true", help="extract features for all history records")
    ap.add_argument("--workers", type=int, default=8, help="concurrent API workers for --extract")
    args = ap.parse_args()

    table = _load_table()

    if args.smoke:
        for r in [r for r in table if not r["correct"]][:2] + [r for r in table if r["correct"]][:1]:
            out = analyze(r)
            print(f"\n--- id={r['id']} correct={r['correct']} ---")
            print(json.dumps(out.model_dump(), ensure_ascii=False, indent=2))
        print(f"\nAPI calls this run: {API_CALLS}")

    if args.validate:
        report = validate_against_gold(20)
        (C.RESULTS / "analyzer_validation.md").write_text(report, encoding="utf-8")
        print(f"wrote {C.RESULTS / 'analyzer_validation.md'} (API calls: {API_CALLS})")

    if args.extract:
        # Analyze EVERY interaction: each one is used as a *past* input feature when
        # predicting its successor (incl. test interactions serving as history for
        # later test targets). The no-leakage rule — never feed analyzer(i+1) when
        # predicting i+1 — is enforced in dataset.py, not by limiting extraction.
        extract_all(table, workers=args.workers)
        print(f"extracted {len(table)} records (API calls this run: {API_CALLS})")

    if not (args.smoke or args.validate or args.extract):
        ap.print_help()


if __name__ == "__main__":
    main()
