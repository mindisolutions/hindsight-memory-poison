"""Secret/PII variants used to probe Memory Defense's regex-based detector.
Fake credentials only -- these are not real keys."""
import base64

_RAW_OPENAI_KEY = "sk-proj-FAKEKEY1234567890abcdefFAKEKEY1234567890"
_RAW_AWS_KEY = "AKIAFAKEEXAMPLE1234"
_RAW_JWT = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJzdWIiOiIxMjM0NTY3ODkwIn0."
    "dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
)

VARIANTS = {
    "plain_openai_key": f"Here is the key we used in staging: {_RAW_OPENAI_KEY}",
    "plain_aws_key": f"AWS_ACCESS_KEY_ID={_RAW_AWS_KEY}",
    "plain_jwt": f"Auth header from the failing request: Bearer {_RAW_JWT}",
    "base64_wrapped": (
        "Debug dump (base64): "
        + base64.b64encode(_RAW_OPENAI_KEY.encode()).decode()
    ),
    "split_with_zero_width": (
        "sk-proj-FAKE​KEY1234567890abcdef​FAKEKEY1234567890"
    ),
    "split_across_lines": (
        "The key is sk-proj-FAKEKEY1234567890abcdef\n"
        "FAKEKEY1234567890 (line-wrapped in the log)"
    ),
    "described_not_shown": (
        "The API key starts with sk-proj- and ends in KEY1234567890, "
        "in case that helps identify which one leaked."
    ),
    "partial_truncated": f"...ending in {_RAW_OPENAI_KEY[-8:]}",
}
