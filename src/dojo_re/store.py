from __future__ import annotations

import secrets
import time
from dataclasses import dataclass

from dojo_re.models import ChallengeSummary, ChallengeTest, GeneratedChallenge


@dataclass(slots=True)
class StoredChallenge:
    id: str
    generated: GeneratedChallenge
    assembly: str
    created_at: float

    @property
    def all_tests(self) -> list[ChallengeTest]:
        return [*self.generated.public_tests, *self.generated.hidden_tests]

    def summary(self) -> ChallengeSummary:
        return ChallengeSummary(
            id=self.id,
            language=self.generated.language,
            title=self.generated.title,
            description=self.generated.description,
            assembly=self.assembly,
            public_tests=self.generated.public_tests,
            created_at=self.created_at,
        )


class ChallengeStore:
    def __init__(self) -> None:
        self._items: dict[str, StoredChallenge] = {}

    def add(self, generated: GeneratedChallenge, assembly: str) -> StoredChallenge:
        challenge_id = secrets.token_urlsafe(12)
        item = StoredChallenge(
            id=challenge_id,
            generated=generated,
            assembly=assembly,
            created_at=time.time(),
        )
        self._items[challenge_id] = item
        return item

    def get(self, challenge_id: str) -> StoredChallenge | None:
        return self._items.get(challenge_id)
