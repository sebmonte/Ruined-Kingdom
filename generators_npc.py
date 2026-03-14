from dataclasses import dataclass, field
import random
from models import NPC
import json
import random
from content_loader import NAMES


def generate_name(race: str) -> tuple[str, str]:
    first = random.choice(NAMES["first_names"][race])
    last = random.choice(NAMES["surnames"][race])
    title = random.choice(NAMES["titles"])
    return first, last


def generate_stat() -> int:
    return round((random.randint(1, 10) + random.randint(1, 10)) / 2)


def get_personality_traits(charm: int, warmth: int, morality: int) -> list[str]:
    stats = {
        "charm": charm,
        "warmth": warmth,
        "morality": morality
    }

    traits = []

    for stat, value in stats.items():
        if value >= 8:
            traits.append(random.choice(NAMES["personalities"][stat]["high"]))
        elif value <= 3:
            traits.append(random.choice(NAMES["personalities"][stat]["low"]))

    return traits

def get_title(traits: list[str], unpredictability: int) -> list[str]:
    stats = {
        "unpredictability": unpredictability
    }

    titles = []

    for stat, value in stats.items():
        if value >= 8:
            titles.append(random.choice(NAMES["personalities"][stat]["high"]))
    if len(titles) > 0 and len(traits) == 0: #Add a 'the' if they have no other trait and only a title
        return f'the {titles[0]}'
    elif len(titles) > 0:
        return f'{titles[0]}'
    return ''

def format_traits(traits: list[str]) -> str:
    if not traits:
        return ""

    if len(traits) == 1:
        return f"the {traits[0]}"

    if len(traits) == 2:
        return f"the {traits[0]} and {traits[1]}"
    
    if len(traits) ==3: 
        return f"the {', '.join(traits[:-1])}, and {traits[-1]}"
    return 'check code for error'

def generate_npc(race: str = "human") -> NPC:
    charm = generate_stat()
    unpredictability = generate_stat()
    warmth = generate_stat()
    morality = generate_stat()

    personality = get_personality_traits(charm, warmth, morality)
    title = get_title(personality, unpredictability)
    first, last = generate_name(race)
    trait_string = format_traits(personality)

    return NPC(
        name=" ".join(part for part in [first, last, trait_string, title] if part),
        race=race,
        charm=charm,
        warmth=warmth,
        unpredictability=unpredictability,
        morality = morality
    )

npc = (generate_npc('human'))
print(npc.name)

