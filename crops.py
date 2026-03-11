import random
from models import Crop
from typing import Callable
from models import GameState


def gloom_corn_effect(state: GameState, amount: int) -> None:
    penalty = amount // 10
    state.kingdom.loyalty -= penalty

def ale_effect(state: GameState, amount: int) -> None:
    bonus = amount // 5
    state.kingdom.loyalty += bonus
def goop_effect(state: GameState, amount: int) -> None:
    if "Flammable_Weapons" not in state.flags:
        state.flags["Flammable_Weapons"] = True
        state.add_log("Flammable Weapons have been unlocked.")

def amanita_effect(state: GameState, amount: int) -> None:
    if amount <= 0:
        return

    people = []
    if state.kingdom.advisor:
        people.append(state.kingdom.advisor)
    people.extend(state.kingdom.advisor_candidates)

    if people:
        target = random.choice(people)
        target.unpredictability += 1
        state.add_log(f"{target.name} becomes more unpredictable from Amanita Muscaria.")

    if "Mushroom_Ritual" not in state.flags:
        state.flags["Mushroom_Ritual"] = True
        state.add_log("The Mushroom Ritual event has been unlocked.")

CROP_DB = {
    "Gloom_Corn": Crop(
        name="Gloom Corn",
        description="The last farmable crop before the fall of Ashvale, known to cause depression.",
        farmability=0.5,
        edible=True,
        food_value=1,
        monthly_effect=gloom_corn_effect,
    ),
    "Wheat": Crop(
        name="Wheat",
        description="A staple of most societies.",
        farmability=1.0,
        edible=True,
        food_value=1,
    ),
    "Bananas": Crop(
        name="Bananas",
        description="Delicious forest fruit.",
        farmability=2.0,
        edible=True,
        food_value=1,
    ),
    "Ooze": Crop(
        name="Ooze",
        description="A mysterious substance dreamt up by a mad scientist. Inedible, but perhaps useful.",
        farmability=1.0,
        edible=False,
        food_value=0,
        tags=["resistant_all"],
    ),
    "Ale": Crop(
        name="Ale",
        description="A warm brew heartens the spirits.",
        farmability=1.0,
        edible=False,
        food_value=0,
        monthly_effect=ale_effect,
    ),
    "Amanita_Muscaria": Crop(
        name="Amanita Muscaria",
        description="Mysterious mushrooms procured from a strange group.",
        farmability=1.0,
        edible=False,
        food_value=0,
        monthly_effect=amanita_effect,
    ),
    "Goop": Crop(
        name="Goop",
        description="A viscous green substance",
        farmability=1.0,
        edible=False,
        food_value=0,
        monthly_effect=goop_effect,
    ),
}

def apply_crop_effects(state: GameState) -> None:
    # Recalculate food from edible crops
    additional_food = 0

    for crop_id, amount in state.kingdom.crops.items():
        crop = CROP_DB[crop_id]

        if crop.edible:
            additional_food += amount * crop.food_value

        if crop.monthly_effect:
            crop.monthly_effect(state, amount)

    state.kingdom.total_food = state.kingdom.total_food + additional_food