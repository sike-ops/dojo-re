from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Language(StrEnum):
    C = "c"
    CPP = "cpp"
    RUST = "rust"
    ZIG = "zig"
    GO = "go"


class Difficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ChallengeTest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    stdin: str = Field(max_length=4096)
    stdout: str = Field(max_length=4096)
    public: bool = True


class GeneratedChallenge(BaseModel):
    language: Language
    title: str = Field(min_length=3, max_length=100)
    description: str = Field(min_length=10, max_length=800)
    source: str = Field(min_length=20, max_length=20000)
    public_tests: list[ChallengeTest] = Field(min_length=1, max_length=5)
    hidden_tests: list[ChallengeTest] = Field(min_length=1, max_length=10)

    @field_validator("public_tests", "hidden_tests")
    @classmethod
    def tests_match_visibility(cls, tests: list[ChallengeTest], info):
        public = info.field_name == "public_tests"
        return [test.model_copy(update={"public": public}) for test in tests]


class ChallengeSummary(BaseModel):
    id: str
    language: Language
    title: str
    description: str
    assembly: str
    public_tests: list[ChallengeTest]
    created_at: float


class GenerateChallengeRequest(BaseModel):
    language: Language | Literal["any"] = "any"
    difficulty: Difficulty = Difficulty.MEDIUM
    theme: str | None = Field(default=None, max_length=120)


class SubmitRequest(BaseModel):
    source: str = Field(min_length=1, max_length=30000)


class RunResult(BaseModel):
    name: str
    stdin: str
    expected_stdout: str
    actual_stdout: str
    passed: bool
    stderr: str = ""
    exit_code: int | None = None
    timed_out: bool = False


class SubmissionResult(BaseModel):
    challenge_id: str
    passed: bool
    compile_stdout: str = ""
    compile_stderr: str = ""
    tests: list[RunResult]


class CompileResult(BaseModel):
    ok: bool
    stdout: str = ""
    stderr: str = ""
    assembly: str = ""
    binary_path: str = "program"
