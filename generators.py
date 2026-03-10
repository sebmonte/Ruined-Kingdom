import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass, field
import random
from models import GameState, Encounter, Choice, Player, NPC
import json
import random
from content_loader import NAMES

# ----------------------------
# Procedural generation
# ----------------------------

BIOMES = ["Forest", "Ruins", "Swamp", "Cavern", "Desert"]
ENCOUNTER_TYPES = ["enemy", "traveler", "treasure", "hazard"]


def generate_name(race: str) -> tuple[str, str, str]:
    first = random.choice(NAMES["first_names"][race])
    last = random.choice(NAMES["surnames"][race])
    title = random.choice(NAMES["titles"])
    return first, last


def generate_stat() -> int:
    return round((random.randint(1, 10) + random.randint(1, 10)) / 2)


def get_personality_traits(charm: int, warmth: int) -> list[str]:
    stats = {
        "charm": charm,
        "warmth": warmth,
    }

    traits = []

    for stat, value in stats.items():
        if value >= 8:
            traits.append(random.choice(NAMES["personalities"][stat]["high"]))
        elif value <= 3:
            traits.append(random.choice(NAMES["personalities"][stat]["low"]))

    return traits

def get_title(unpredictability: int) -> list[str]:
    stats = {
        "unpredictability": unpredictability
    }

    titles = []

    for stat, value in stats.items():
        if value >= 8:
            titles.append(random.choice(NAMES["personalities"][stat]["high"]))
    if len(titles) > 0:
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
    return 'bug'

def generate_npc(race: str = "human") -> NPC:
    charm = generate_stat()
    unpredictability = generate_stat()
    warmth = generate_stat()

    personality = get_personality_traits(charm, warmth)
    title = get_title(unpredictability)
    first, last = generate_name(race)
    trait_string = format_traits(personality)

    return NPC(
        name=f"{first} {last} {trait_string} {title}",
        race=race,
        charm=charm,
        warmth=warmth,
        unpredictability=unpredictability,
    )


npc = generate_npc("human")
print(npc)
print(npc.name)
print(npc.charm)
#print(npc.personality)


def generate_biome(area_index: int) -> str:
    # Mild progression: later areas are a bit harsher
    if area_index < 2:
        pool = ["Forest", "Ruins"]
    elif area_index < 5:
        pool = ["Forest", "Ruins", "Swamp", "Cavern"]
    else:
        pool = BIOMES
    return random.choice(pool)


def generate_encounter(state: GameState) -> Encounter:
    biome = state.current_biome
    e_type = random.choice(ENCOUNTER_TYPES)

    if e_type == "enemy":
        enemy = random.choice(["Wolf", "Bandit", "Slime", "Spider", "Wraith"])
        strength = random.randint(1, 4) + state.area_index // 2

        def fight():
            damage = max(1, random.randint(0, strength))
            reward = random.randint(1, 4) + strength
            state.player.hp -= damage
            state.player.gold += reward
            state.add_log(
                f"You defeated the {enemy}, lost {damage} HP, and gained {reward} gold."
            )
            next_area(state)

        def sneak():
            success = random.random() < 0.65
            if success:
                state.add_log(f"You slipped past the {enemy}.")
            else:
                damage = random.randint(1, 2)
                state.player.hp -= damage
                state.add_log(f"You failed to sneak past the {enemy} and lost {damage} HP.")
            next_area(state)

        return Encounter(
            title=f"{enemy} in the {biome}",
            description=(
                f"You enter a {biome.lower()} path and encounter a hostile {enemy.lower()}.\n"
                f"It looks dangerous."
            ),
            choices=[
                Choice("1", "Fight", fight),
                Choice("2", "Sneak away", sneak),
            ],
        )

    if e_type == "traveler":
        traveler = random.choice(["Merchant", "Pilgrim", "Scout", "Hermit"])

        def trade():
            if state.player.gold >= 3:
                state.player.gold -= 3
                state.player.food += 2
                state.add_log(f"You trade with the {traveler.lower()} for 2 food.")
            else:
                state.add_log("You do not have enough gold to trade.")
            next_area(state)

        def ask():
            hint = random.choice([
                "You hear that the next region is dangerous.",
                "The traveler mentions hidden treasure in old places.",
                "The traveler warns you to conserve food.",
            ])
            state.add_log(f"The {traveler.lower()} shares a tip: {hint}")
            next_area(state)

        return Encounter(
            title=f"{traveler} on the Road",
            description=(
                f"A lone {traveler.lower()} waits beside the trail in the {biome.lower()}."
            ),
            choices=[
                Choice("1", "Trade (3 gold for 2 food)", trade),
                Choice("2", "Ask for advice", ask),
            ],
        )

    if e_type == "treasure":
        treasure = random.choice(["chest", "supply cache", "ancient shrine", "buried satchel"])

        def open_it():
            gold = random.randint(2, 6)
            food = random.randint(0, 2)
            state.player.gold += gold
            state.player.food += food
            state.add_log(f"You search the {treasure} and find {gold} gold and {food} food.")
            next_area(state)

        def ignore():
            state.add_log(f"You leave the {treasure} untouched and move on.")
            next_area(state)

        return Encounter(
            title=f"Found a {treasure.title()}",
            description=f"You discover a {treasure} hidden in the {biome.lower()}.",
            choices=[
                Choice("1", "Search it", open_it),
                Choice("2", "Ignore it", ignore),
            ],
        )

    # hazard
    hazard = random.choice(["quicksand", "poison spores", "rockfall", "thin ice"])

    def push_through():
        damage = random.randint(1, 3)
        state.player.hp -= damage
        state.add_log(f"You push through the {hazard} and lose {damage} HP.")
        next_area(state)

    def avoid():
        food_cost = 1
        if state.player.food >= food_cost:
            state.player.food -= food_cost
            state.add_log(f"You detour around the {hazard}, using {food_cost} food.")
        else:
            state.add_log(
                f"You try to avoid the {hazard}, but with no supplies you are slowed badly."
            )
        next_area(state)

    return Encounter(
        title=f"Hazard: {hazard.title()}",
        description=f"The way forward through the {biome.lower()} is blocked by {hazard}.",
        choices=[
            Choice("1", "Push through", push_through),
            Choice("2", "Take a detour", avoid),
        ],
    )


def next_area(state: GameState) -> None:
    state.area_index += 1

    # passive travel cost
    if state.player.food > 0:
        state.player.food -= 1
        state.add_log("You consume 1 food while traveling.")
    else:
        state.player.hp -= 1
        state.add_log("You have no food and lose 1 HP from exhaustion.")

    state.current_biome = generate_biome(state.area_index)
    state.current_encounter = generate_encounter(state)
