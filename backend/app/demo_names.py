from __future__ import annotations

import random

_GIVEN_NAMES = [
    "Amelia",
    "Rafael",
    "Maya",
    "Theo",
    "Nina",
    "Luca",
    "Aisha",
    "Felix",
    "Sofia",
    "Ethan",
    "Leila",
    "Oscar",
    "Priya",
    "Mateo",
    "Zara",
    "Jonah",
    "Ines",
    "Kai",
    "Elena",
    "Arjun",
]
_FAMILY_NAMES = [
    "Bennett",
    "Costa",
    "Shah",
    "Moreau",
    "Kim",
    "Novak",
    "Singh",
    "Fischer",
    "Alvarez",
    "Tanaka",
    "Dubois",
    "Reed",
    "Petrov",
    "Okafor",
    "Lindholm",
    "Santos",
    "Kaur",
    "Weber",
    "Nakamura",
    "Clarke",
]


def generate_demo_names(rng: random.Random, car_count: int) -> list[str]:
    return [
        f"{given} {family}"
        for given, family in zip(
            rng.sample(_GIVEN_NAMES, car_count),
            rng.sample(_FAMILY_NAMES, car_count),
            strict=False,
        )
    ]
