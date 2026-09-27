from __future__ import annotations

from dataclasses import dataclass

from dojo_re.models import Language


@dataclass(frozen=True, slots=True)
class LanguageSpec:
    filename: str
    compile_command: str
    monaco_language: str


LANGUAGES: dict[Language, LanguageSpec] = {
    Language.C: LanguageSpec("source.c", "gcc -O2 -g0 source.c -o program", "c"),
    Language.CPP: LanguageSpec("source.cpp", "g++ -O2 -g0 source.cpp -o program", "cpp"),
    Language.RUST: LanguageSpec("source.rs", "rustc -O source.rs -o program", "rust"),
    Language.ZIG: LanguageSpec(
        "source.zig",
        "zig build-exe -O ReleaseFast source.zig -femit-bin=program",
        "zig",
    ),
    Language.GO: LanguageSpec(
        "source.go",
        'go build -ldflags="-s -w" -o program source.go',
        "go",
    ),
}


def language_spec(language: Language) -> LanguageSpec:
    return LANGUAGES[language]
