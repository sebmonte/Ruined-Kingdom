from models import GameState
import random
from collections import Counter

from crops import CROP_DB
from generators_villagers import generate_villager


def addiction_chance_from_willpower(willpower: int) -> float:
    """
    Returns probability of addiction as a float from 0.0 to 1.0.

    0 willpower  -> 10% chance
    10 willpower -> 0% chance
    """
    willpower = max(0, min(10, willpower))  # clamp to 0-10
    return 0.10 * (1 - willpower / 10)

def fertility_chance_from_extraversion(extraversion: int) -> float:
    """
    Returns probability of fertility as a float from 0.0 to 1.0.

    0 extraversion  -> 18% chance
    10 extraversion -> 45% chance
    """
    extraversion = max(1, min(10, extraversion)) # clamp to 0-10
    return 0.15 + (extraversion / 10) * 0.3


def apply_villager_effects(state: GameState) -> None:
    new_villagers: list[str] = []
    for villager in state.kingdom.population:
        chance = fertility_chance_from_extraversion(villager.extraversion)
        if random.random() < chance:
            new_villagers.append(generate_villager(villager.race))
    state.kingdom.population.extend(new_villagers)
    if hasattr(state, "last_month_summary"):
        state.last_month_summary.append(f"Villagers: {len(new_villagers)} new villagers born.")


    newly_addicted: list[tuple[str, str]] = []  # (villager_name, crop_id)

    crop_ids = [
        cid for cid, amount in state.kingdom.crops.items()
        if amount > 0 and cid in CROP_DB and CROP_DB[cid].edible
    ]
    if not crop_ids:
        if hasattr(state, "last_month_summary"):
            state.last_month_summary.append("Villagers: no edible crops in the kingdom; no addiction checks.")
        return
    for villager in state.kingdom.population:
        if villager.has_status("addicted"):
            continue
        chance = addiction_chance_from_willpower(villager.willpower)
        if random.random() >= chance:
            continue
        crop_id = random.choice(crop_ids)
        villager.add_status("addicted", crop_id)
        newly_addicted.append((villager.name, crop_id))

    if hasattr(state, "last_month_summary"):
        if newly_addicted:
            crop_counts = Counter(crop_id for _, crop_id in newly_addicted)
            parts = []
            for crop_id, count in crop_counts.items():
                crop_name = CROP_DB[crop_id].name if crop_id in CROP_DB else crop_id
                v = "villager" if count == 1 else "villagers"
                parts.append(f"{count} {v} became addicted to {crop_name}")
            state.last_month_summary.append("Villagers: " + ", ".join(parts) + ".")