
# -*- coding: utf-8 -*-
"""
Run GPT in batch from a JSONL prompts file with concurrency, retry, checkpoint, and resume.
- Input JSONL (one object per line) must include the following keys (from your file):
    - product_name: str
    - persona_key: int or str
    - system_prompt: str
    - user_prompt: str

The script will construct messages = [
  {"role":"system","content":system_prompt},
  {"role":"user","content":user_prompt}
]
and call OpenAI Chat Completions with JSON mode enabled to enforce valid JSON outputs.

Usage (Windows PowerShell):
  $env:OPENAI_API_KEY="sk-..."
  python run_gpt_jsonl_batch.py --input "/mnt/data/advanced_prompts_for_llm.jsonl" --out "results_adv.jsonl" --model "gpt-4o-mini" --concurrency 6

Usage (macOS/Linux):
  export OPENAI_API_KEY="sk-..."
  python run_gpt_jsonl_batch.py --input /mnt/data/advanced_prompts_for_llm.jsonl --out results_adv.jsonl --model gpt-4o-mini --concurrency 6
"""
import os
import json
import csv
import time
import random
import signal
import argparse
import asyncio
from pathlib import Path
from typing import Dict, Any, List

try:
    # OpenAI SDK v1.x
    from openai import AsyncOpenAI
except Exception:
    AsyncOpenAI = None

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DEFAULT_MAX_OUTPUT_TOKENS = int(os.getenv("OPENAI_MAX_OUTPUT_TOKENS", "512"))

def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except Exception as e:
                raise ValueError(f"Invalid JSON on line {ln}: {e}")
            # Basic validation
            for k in ("product_name", "persona_key", "system_prompt", "user_prompt"):
                if k not in obj:
                    raise ValueError(f"Missing key '{k}' on line {ln}")
            rows.append(obj)
    return rows

def to_jsonl_line(obj: Dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False) + "\n"

def load_done_ids(jsonl_path: Path) -> set:
    done = set()
    if jsonl_path.exists():
        with jsonl_path.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    key = obj.get("id")
                    if key:
                        done.add(str(key))
                except Exception:
                    continue
    return done

def build_id(o: Dict[str, Any]) -> str:
    # Combine product and persona for uniqueness
    return f"{o.get('product_name','').strip()}|{o.get('persona_key')}"

class GracefulKiller:
    def __init__(self):
        self.kill_now = False
        signal.signal(signal.SIGINT, self.exit_gracefully)
        try:
            signal.signal(signal.SIGTERM, self.exit_gracefully)
        except Exception:
            pass
    def exit_gracefully(self, *args):
        self.kill_now = True

async def call_openai_json(
    client,
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_output_tokens: int,
    temperature: float,
    top_p: float,
    timeout_s: int,
    use_json_mode: bool = True,
) -> Dict[str, Any]:
    """
    Calls Chat Completions with optional JSON mode.
    Returns dict with keys: content, model, id_resp, usage (if available).
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    kwargs = dict(
        model=model,
        messages=messages,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_output_tokens,
        timeout=timeout_s,
    )
    if use_json_mode:
        # JSON mode (response_format) is supported by Chat Completions on modern models like gpt-4o, gpt-4o-mini.
        # If the server/model does not support it, we'll retry without.
        kwargs["response_format"] = {"type": "json_object"}

    resp = await client.chat.completions.create(**kwargs)
    choice = resp.choices[0]
    content = getattr(choice, "message", None).content if hasattr(choice, "message") else getattr(choice, "text", None)
    usage = getattr(resp, "usage", None)
    usage_dict = usage.model_dump() if hasattr(usage, "model_dump") else (usage.__dict__ if usage else None)
    return {
        "content": content,
        "model": resp.model,
        "id_resp": resp.id,
        "usage": usage_dict,
    }

async def worker(job: Dict[str, Any], sem: asyncio.Semaphore, client, args, out_fh):
    backoff = 1.0
    attempt = 0
    use_json_mode = True
    while True:
        if args.killer.kill_now:
            return
        try:
            async with sem:
                result = await call_openai_json(
                    client=client,
                    model=args.model,
                    system_prompt=job["system_prompt"],
                    user_prompt=job["user_prompt"],
                    max_output_tokens=args.max_output_tokens,
                    temperature=args.temperature,
                    top_p=args.top_p,
                    timeout_s=args.timeout,
                    use_json_mode=use_json_mode,
                )
            text = result["content"] or ""
            parsed = None
            parse_error = None
            # Try to parse JSON (models in JSON mode should return valid JSON)
            try:
                parsed = json.loads(text)
            except Exception as e:
                parse_error = str(e)

            record = {
                "id": job["id"],
                "product_name": job["product_name"],
                "persona_key": job["persona_key"],
                "model": result.get("model"),
                "response_id": result.get("id_resp"),
                "usage": result.get("usage"),
                "output_raw": text,
                "output_json": parsed,
                "parse_error": parse_error,
                "ts": time.time(),
                "attempts": attempt + 1,
            }
            out_fh.write(to_jsonl_line(record))
            out_fh.flush()
            return
        except Exception as e:
            attempt += 1
            # If response_format not supported, try once without JSON mode
            msg = str(e)
            if "response_format" in msg or "json_object" in msg:
                use_json_mode = False
            if attempt > args.retries:
                record = {
                    "id": job["id"],
                    "product_name": job["product_name"],
                    "persona_key": job["persona_key"],
                    "error": msg,
                    "ts": time.time(),
                    "attempts": attempt,
                }
                out_fh.write(to_jsonl_line(record))
                out_fh.flush()
                return
            # Backoff + jitter
            await asyncio.sleep(backoff + random.uniform(0, 0.5))
            backoff = min(backoff * 2.0, args.max_backoff)

async def main_async(args):
    if AsyncOpenAI is None:
        raise RuntimeError("OpenAI SDK not found. Install with: pip install openai>=1.0.0")
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Please set OPENAI_API_KEY environment variable.")

    rows = read_jsonl(args.input)
    # attach synthetic id
    for o in rows:
        o["id"] = build_id(o)

    done_ids = load_done_ids(args.out)
    pending = [r for r in rows if str(r["id"]) not in done_ids]
    total = len(rows)

    print(f"Total={total} | AlreadyDone={len(done_ids)} | Pending={len(pending)} | Concurrency={args.concurrency} | Model={args.model}")
    if not pending:
        print("Nothing to do.")
        return

    client = AsyncOpenAI()
    sem = asyncio.Semaphore(args.concurrency)

    killer = GracefulKiller()
    args.killer = killer

    # Ensure output dir exists
    args.out.parent.mkdir(parents=True, exist_ok=True)

    started = time.time()
    with args.out.open("a", encoding="utf-8") as out_fh:
        tasks = [asyncio.create_task(worker(job, sem, client, args, out_fh)) for job in pending]

        # simple progress ticker
        while True:
            await asyncio.sleep(2.0)
            done_n = sum(1 for t in tasks if t.done())
            rate = done_n / max(1e-9, (time.time() - started))
            print(f"[progress] {done_n}/{len(tasks)} | ~{rate:.2f} it/s")
            if done_n == len(tasks) or killer.kill_now:
                break

        await asyncio.gather(*tasks, return_exceptions=True)

def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Batch runner for GPT from JSONL")
    p.add_argument("--input", type=Path, required=True, help="Input JSONL (keys: product_name, persona_key, system_prompt, user_prompt)")
    p.add_argument("--out", type=Path, default=Path("results_adv.jsonl"), help="Output JSONL")
    p.add_argument("--model", type=str, default=DEFAULT_MODEL)
    p.add_argument("--max-output-tokens", type=int, default=DEFAULT_MAX_OUTPUT_TOKENS)
    p.add_argument("--temperature", type=float, default=0.2)
    p.add_argument("--top-p", type=float, default=1.0)
    p.add_argument("--timeout", type=int, default=120)
    p.add_argument("--concurrency", type=int, default=6)
    p.add_argument("--retries", type=int, default=5)
    p.add_argument("--max-backoff", type=float, default=30.0)
    return p.parse_args(argv)

if __name__ == "__main__":
    args = parse_args()
    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        print("Interrupted.")
