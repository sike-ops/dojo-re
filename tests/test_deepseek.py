from dojo_re.deepseek import _extract_json, _normalize_model
from dojo_re.models import GeneratedChallenge, Language


def test_extract_json_from_plain_json() -> None:
    payload = _extract_json('{"language":"c","title":"Checksum","description":"A small checksum task.","source":"#include <stdio.h>\\nint main(){return 0;}","public_tests":[{"name":"sample","stdin":"1\\n","stdout":"","public":true}],"hidden_tests":[{"name":"hidden","stdin":"2\\n","stdout":"","public":false}]}')

    challenge = GeneratedChallenge.model_validate(payload)

    assert challenge.language == Language.C
    assert challenge.public_tests[0].public is True
    assert challenge.hidden_tests[0].public is False


def test_extract_json_from_markdown_wrapped_response() -> None:
    payload = _extract_json('```json\n{"ok": true}\n```')

    assert payload == {"ok": True}


def test_deepseek_v41_flash_alias_uses_api_model_id() -> None:
    assert _normalize_model("DeepSeek-V4.1-Flash") == "deepseek-flash"
