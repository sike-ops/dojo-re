from dojo_re.models import ChallengeTest, GeneratedChallenge, Language
from dojo_re.store import ChallengeStore


def test_store_hides_source_from_summary() -> None:
    store = ChallengeStore()
    challenge = GeneratedChallenge(
        language=Language.C,
        title="Tiny Hash",
        description="Reads input and prints a tiny hash.",
        source="#include <stdio.h>\nint main(void){return 0;}",
        public_tests=[ChallengeTest(name="sample", stdin="abc\n", stdout="42\n", public=True)],
        hidden_tests=[ChallengeTest(name="hidden", stdin="xyz\n", stdout="7\n", public=False)],
    )

    stored = store.add(challenge, "asm")
    summary = stored.summary().model_dump()

    assert summary["id"]
    assert summary["assembly"] == "asm"
    assert "source" not in summary
    assert "hidden_tests" not in summary
