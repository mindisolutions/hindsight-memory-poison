"""
Attack 2: Secret/PII exfiltration vs Memory Defense's redact/block rules.

This is the one documented control (regex-based, 45 predefined patterns,
opt-in per bank). Runs every payload variant against both CONTROL_BANK
(defense off) and DEFENDED_BANK (defense on, redact mode) and checks whether
recall() still returns the raw secret.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent / "payloads"))
from client import CONTROL_BANK, DEFENDED_BANK, append_result, get_client  # noqa: E402
from secret_variants import VARIANTS  # noqa: E402


def probe_bank(client, bank_id: str, variant_name: str, content: str) -> dict:
    client.retain(bank_id=bank_id, content=content, context=f"exfil_probe:{variant_name}")
    recalled = client.recall(bank_id=bank_id, query=content[:60])
    recalled_text = str(recalled)

    # crude check: does the raw fragment (first 20 chars after any label)
    # still show up verbatim in what comes back?
    leaked = any(
        marker in recalled_text
        for marker in ("sk-proj-FAKEKEY", "AKIAFAKEEXAMPLE", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9")
    )
    return {"recalled": recalled_text, "leaked": leaked}


def main() -> None:
    client = get_client()

    for variant_name, content in VARIANTS.items():
        for bank_id, defended in ((CONTROL_BANK, False), (DEFENDED_BANK, True)):
            outcome = probe_bank(client, bank_id, variant_name, content)
            status = "LEAKED" if outcome["leaked"] else "blocked/redacted"
            print(f"[{bank_id:>20}] {variant_name:<24} -> {status}")

            append_result(
                {
                    "attack": "02_secret_exfiltration",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "bank": bank_id,
                    "memory_defense_enabled": defended,
                    "variant": variant_name,
                    "leaked": outcome["leaked"],
                    "recalled_excerpt": outcome["recalled"][:300],
                }
            )

    print(
        "\nInteresting result = leaked=True on DEFENDED_BANK for any variant "
        "(defense should have caught it) -- especially the obfuscated ones "
        "(base64, zero-width chars, split-across-lines, described-not-shown), "
        "since regex detectors typically only match the literal pattern."
    )


if __name__ == "__main__":
    main()
