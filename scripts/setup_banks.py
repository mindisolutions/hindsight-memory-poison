"""Creates the two banks used across the lab: one control (no Memory Defense)
and one defended (Memory Defense on, redact mode) so attack 2 has something
to compare against."""
from client import CONTROL_BANK, DEFENDED_BANK, ensure_bank, set_memory_defense


def main() -> None:
    ensure_bank(CONTROL_BANK)
    set_memory_defense(CONTROL_BANK, enabled=False)
    print(f"[ok] {CONTROL_BANK} ready (memory_defense disabled)")

    ensure_bank(DEFENDED_BANK)
    set_memory_defense(
        DEFENDED_BANK,
        enabled=True,
        rules=[{"on": "sensitive_data", "action": "redact"}],
    )
    print(f"[ok] {DEFENDED_BANK} ready (memory_defense enabled, redact mode)")


if __name__ == "__main__":
    main()
