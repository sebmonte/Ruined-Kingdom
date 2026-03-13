import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass, field
import random
from models import Villager
import json
import random
from content_loader import VILLAGERS


def generate_name(race: str) -> tuple[str, str]:
    first = random.choice(VILLAGERS["first_names"][race])
    last = random.choice(VILLAGERS["surnames"][race])
    return first, last


def generate_stat() -> int:
    return random.choices(
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        weights=[1, 3, 9, 10, 12, 10, 9, 3, 1, 1],
        k=1
    )[0]


def get_personality_traits(willpower: int, extraversion: int, luck: int, conscientiousness: int) -> list[str]:
    stats = {
        "willpower": willpower,
        "extraversion": extraversion,
        "luck": luck,
        "conscientiousness": conscientiousness
    }

    traits = []

    for stat, value in stats.items():
        if value >= 8:
            traits.append(random.choice(VILLAGERS["personalities"][stat]["high"]))
        elif value <= 3:
            traits.append(random.choice(VILLAGERS["personalities"][stat]["low"]))

    return traits

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

def generate_villager(race: str = "human") -> Villager:
    willpower = generate_stat()
    extraversion = generate_stat()
    luck = generate_stat()
    conscientiousness = generate_stat()

    personality = get_personality_traits(willpower, extraversion, luck, conscientiousness)
    trait_string =format_traits(personality)
    first, last = generate_name(race)
    isanimal = race in ["dog", "ape"]

    return Villager(
        name=" ".join(part for part in [first, last, trait_string] if part),
        race=race,
        isanimal=isanimal, # boolean for if the villager is an animal
        willpower=willpower,
        extraversion=extraversion,
        luck=luck,
        conscientiousness=conscientiousness,
    )



