from __future__ import annotations

import json
import os
import random
import re
from typing import Any

from openai import OpenAI, OpenAIError
from pydantic import ValidationError

from dojo_re.models import (
    ChallengeTest,
    Difficulty,
    GenerateChallengeRequest,
    GeneratedChallenge,
    Language,
)


class GenerationError(RuntimeError):
    pass


LANGUAGE_LABELS = {
    Language.C: "C",
    Language.CPP: "C++",
    Language.RUST: "Rust",
    Language.ZIG: "Zig",
    Language.GO: "Go",
}


class DeepSeekChallengeGenerator:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not key:
            raise GenerationError("Set DEEPSEEK_API_KEY before generating challenges.")
        self.client = OpenAI(api_key=key, base_url="https://api.deepseek.com", timeout=45)
        self.model = _normalize_model(model or os.environ.get("DEEPSEEK_MODEL", "deepseek-flash"))

    def generate(self, request: GenerateChallengeRequest) -> GeneratedChallenge:
        language = self._pick_language(request.language)
        prompt = self._prompt(language, request.difficulty, request.theme)
        last_error = ""
        for _ in range(3):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.8,
                    max_tokens=8000,
                    stream=False,
                    reasoning_effort="none",
                    extra_body={"thinking": {"type": "disabled"}},
                )
                content = response.choices[0].message.content or ""
                payload = _extract_json(content)
                challenge = GeneratedChallenge.model_validate(payload)
                if challenge.language != language:
                    challenge = challenge.model_copy(update={"language": language})
                return challenge
            except OpenAIError as exc:
                raise GenerationError(f"DeepSeek API request failed: {exc}") from exc
            except (json.JSONDecodeError, ValidationError, TypeError, ValueError, IndexError) as exc:
                last_error = str(exc)
        raise GenerationError(f"DeepSeek did not return a valid challenge: {last_error}")

    def _pick_language(self, language: Language | str) -> Language:
        if language == "any":
            return random.choice(list(Language))
        return Language(language)

    def _prompt(
        self,
        language: Language,
        difficulty: Difficulty,
        theme: str | None,
    ) -> str:
        theme_line = f"The user requested this theme: {theme}." if theme else ""
        return f"""
Generate one reverse-engineering practice challenge in {LANGUAGE_LABELS[language]}.
Difficulty: {difficulty.value}.
{theme_line}

The program must:
- be a single complete source file
- read only from stdin
- write only deterministic stdout
- terminate quickly
- avoid files, networking, randomness, clock/time, threads, sleeps, undefined behavior, platform-specific syscalls, and huge allocations
- be small enough to reverse engineer from objdump assembly
- implement mixed utility logic such as checksum, parser, encoder, validator, numeric transform, or small state machine

Return strict JSON only with this shape:
{{
  "language": "{language.value}",
  "title": "short title",
  "description": "what the binary appears to do, without revealing the exact source",
  "source": "complete source code",
  "public_tests": [
    {{"name": "sample 1", "stdin": "input text", "stdout": "", "public": true}}
  ],
  "hidden_tests": [
    {{"name": "hidden 1", "stdin": "input text", "stdout": "", "public": false}}
  ]
}}

Provide 2 public tests and 4 hidden tests. Leave stdout as an empty string; the harness will compute it.
"""


SYSTEM_PROMPT = """
You generate safe, deterministic, single-file programming challenges for reverse engineering practice.
Return JSON only. Do not use Markdown fences.
The generated source must compile on Linux x86_64 with ordinary stable compilers.
"""


def _extract_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("{"):
        return json.loads(stripped)
    match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON object found")
    return json.loads(match.group(0))


def _normalize_model(model: str) -> str:
    normalized = model.strip().lower().replace("_", "-")
    aliases = {
        "deepseek-v4.1-flash": "deepseek-flash",
        "deepseek-v4-flash": "deepseek-flash",
        "v4.1-flash": "deepseek-flash",
        "v4-flash": "deepseek-flash",
    }
    return aliases.get(normalized, model.strip())


def with_actual_outputs(
    challenge: GeneratedChallenge,
    public_results: list[ChallengeTest],
    hidden_results: list[ChallengeTest],
) -> GeneratedChallenge:
    return challenge.model_copy(
        update={
            "public_tests": public_results,
            "hidden_tests": hidden_results,
        },
    )
