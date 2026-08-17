"""Config-driven benchmark runner.

Reads a YAML (or JSON) benchmark manifest and executes each entry in order,
capturing stdout to ``reports/benchmarks/<name>.log`` and writing a summary
manifest to ``reports/benchmarks/manifest.json``.

Usage:
    python scripts/benchmark.py benchmarks.yaml
    python scripts/benchmark.py benchmarks.json

Manifest format (YAML):
    defaults:
      base_url: http://localhost:8890
      reports_dir: reports
    benchmarks:
      - name: baseline
        script: scripts/01_baseline_trials.py
        env: { REPORTS_DIR: reports/ci-baseline }   # optional overrides
        args: []                                    # optional CLI args

Only stdlib + PyYAML (optional, falls back to JSON) are used.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).parent.parent


def _load_manifest(path: str) -> dict:
    p = Path(path)
    if not p.is_absolute():
        p = REPO / p
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() in (".yaml", ".yml"):
        try:
            import yaml  # type: ignore  # pylint: disable=import-outside-toplevel

            return yaml.safe_load(text)
        except ImportError:
            sys.exit("PyYAML is required for .yaml manifests (pip install pyyaml); use JSON otherwise.")
    return json.loads(text)


def _run_one(entry: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    name = entry["name"]
    script = REPO / entry["script"]
    env = dict(os.environ)
    env.setdefault("HINDSIGHT_BASE_URL", defaults.get("base_url", "http://localhost:8890"))
    env.setdefault("REPORTS_DIR", defaults.get("reports_dir", "reports"))
    for k, v in (entry.get("env") or {}).items():
        env[k] = str(v)

    outdir = REPO / "reports" / "benchmarks"
    outdir.mkdir(parents=True, exist_ok=True)
    log = outdir / f"{name}.log"
    args = [sys.executable, str(script)] + [str(a) for a in (entry.get("args") or [])]

    started = datetime.now(timezone.utc)
    with open(log, "w", encoding="utf-8") as fh:
        proc = subprocess.run(args, cwd=REPO, env=env, stdout=fh, stderr=subprocess.STDOUT, check=False)
    elapsed = (datetime.now(timezone.utc) - started).total_seconds()

    return {
        "name": name,
        "script": entry["script"],
        "exit_code": proc.returncode,
        "elapsed_s": round(elapsed, 2),
        "log": str(log.relative_to(REPO)),
        "ok": proc.returncode == 0,
    }


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: python scripts/benchmark.py <manifest.yaml|.json>")
    manifest = _load_manifest(sys.argv[1])
    defaults = manifest.get("defaults", {})
    results = []

    for entry in manifest.get("benchmarks", []):
        print(f"[benchmark] {entry['name']} ...", flush=True)
        res = _run_one(entry, defaults)
        results.append(res)
        status = "ok" if res["ok"] else f"FAILED (exit {res['exit_code']})"
        print(f"            {status} in {res['elapsed_s']}s -> {res['log']}", flush=True)

    outdir = REPO / "reports" / "benchmarks"
    outdir.mkdir(parents=True, exist_ok=True)
    manifest_out = outdir / "manifest.json"
    manifest_out.write_text(json.dumps({"timestamp": datetime.now(timezone.utc).isoformat(), "results": results}, indent=2))

    failed = [r for r in results if not r["ok"]]
    print(f"\n{len(results) - len(failed)}/{len(results)} benchmarks ok. Manifest: {manifest_out}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
