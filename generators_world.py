from dataclasses import dataclass
from itertools import combinations
import random
from models import GameState, RaceRelationship, Villager
from generators_villagers import generate_villager


@dataclass
class RaceRelationship:
    race_a: str
    race_b: str
    reputation: int
    reasons: list[str]


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def relationship_label(value: int) -> str:
    if value <= -250:
        return "Abhors"
    elif value <= -100:
        return "Dislikes"
    elif value < 100:
        return "Neutral"
    elif value < 250:
        return "Admires"
    return "Reveres"

def generate_relationship_reasons(rep: int, race_a: str, race_b: str) -> list[str]:
    if rep <= -250:
        return ["ancient hatred"]
    elif rep <= -100:
        return ["old grievances"]
    elif rep < 100:
        return ["they lack shared history"]
    elif rep < 250:
        return ["historical cooperation"]
    else:
        return ["deep cultural bonds"]
def generate_race_relationships(races: list[str]) -> dict[tuple[str, str], RaceRelationship]:
    relationships = {}

    for a, b in combinations(sorted(races), 2):
        rep = clamp(int(random.gauss(0, 150)), -500, 500)

        reasons = generate_relationship_reasons(rep, a, b)

        relationships[(a, b)] = RaceRelationship(
            race_a=a,
            race_b=b,
            reputation=rep,
            reasons=reasons,
        )

    return relationships

def get_race_relationship(
    relationships: dict[tuple[str, str], RaceRelationship],
    race_a: str,
    race_b: str
) -> RaceRelationship | None:
    if race_a == race_b:
        return None
    key = tuple(sorted((race_a, race_b)))
    return relationships.get(key)

def races_are_neutral_or_better(
    relationships: dict[tuple[str, str], RaceRelationship],
    race_a: str,
    race_b: str
) -> bool:
    if race_a == race_b:
        return True

    relationship = get_race_relationship(relationships, race_a, race_b)
    if relationship is None:
        return True

    return relationship.reputation >= -99
import random


def generate_starting_population(state: GameState, races: list[str]) -> list[Villager]:
    relationships = state.world_history.race_relationships

    primary_race = random.choice(races)

    remaining_races = [r for r in races if r != primary_race]
    secondary_race = random.choice(remaining_races)

    valid_third_races = [
        r for r in remaining_races
        if r != secondary_race and races_are_neutral_or_better(relationships, primary_race, r)
    ]

    if valid_third_races:
        third_race = random.choice(valid_third_races)
    else:
        # if none qualify, just pick any remaining race
        third_race = random.choice([r for r in remaining_races if r != secondary_race])

    population = []
    population.extend(generate_villager(primary_race.lower()) for _ in range(7))
    population.extend(generate_villager(secondary_race.lower()) for _ in range(2))
    population.extend(generate_villager(third_race.lower()) for _ in range(1))

    random.shuffle(population)
    return population

def initialize_new_game(state: GameState) -> None:
    races = ["human", "goblin", "dwarf", "gnome", "titan", "umbralite", "mirekin", "troll"]

    state.world_history.race_relationships = generate_race_relationships(races)
    print(state.world_history.race_relationships)
    state.kingdom.population = generate_starting_population(state, races)