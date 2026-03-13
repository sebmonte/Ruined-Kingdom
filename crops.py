import random
from models import Crop
from typing import Callable
from models import GameState


def gloom_corn_effect(state: GameState, amount: int, summary: list[str] | None = None) -> None:
    penalty = amount // 10
    state.kingdom.loyalty -= penalty
    if summary is not None and penalty:
        summary.append(f"loyalty −{penalty}")

def ale_effect(state: GameState, amount: int, summary: list[str] | None = None) -> None:
    bonus = amount // 5
    state.kingdom.loyalty += bonus
    if summary is not None and bonus:
        summary.append(f"loyalty +{bonus}")

def goop_effect(state: GameState, amount: int, summary: list[str] | None = None) -> None:
    if "Flammable_Weapons" not in state.flags:
        state.flags["Flammable_Weapons"] = True
        state.add_log("Flammable Weapons have been unlocked.")
        if summary is not None:
            summary.append("Flammable Weapons unlocked.")

def amanita_effect(state: GameState, amount: int, summary: list[str] | None = None) -> None:
    if amount <= 0:
        return

    people = []
    if state.kingdom.advisor:
        people.append(state.kingdom.advisor)
    people.extend(state.kingdom.advisor_candidates)

    effect_parts: list[str] = []
    if people:
        target = random.choice(people)
        target.unpredictability += 1
        state.add_log(f"{target.name} becomes more unpredictable from Amanita Muscaria.")
        effect_parts.append(f"{target.name} more unpredictable")

    if "Mushroom_Ritual" not in state.flags:
        state.flags["Mushroom_Ritual"] = True
        state.add_log("The Mushroom Ritual event has been unlocked.")
        effect_parts.append("Mushroom Ritual unlocked")

    if summary is not None and effect_parts:
        summary.append("; ".join(effect_parts) + ".")

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
        description=f"A staple of most societies.",
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
        description="A viscous green substance.",
        farmability=1.0,
        edible=False,
        food_value=0,
        monthly_effect=goop_effect,
    ),
}

def apply_crop_effects(state: GameState) -> None:
    # Recalculate food from edible crops and collect per-crop summary data
    additional_food = 0
    crop_reports: list[dict] = []  # each: name, food, new_total, effects

    for crop_id, amount in state.kingdom.crops.items():
        crop = CROP_DB[crop_id]

        food = amount * crop.food_value if crop.edible and amount > 0 else 0
        if crop.edible and amount > 0:
            additional_food += food

        new_total = amount
        if crop.farmability > 0:
            new_total = amount + int(amount * crop.farmability)
            state.kingdom.crops[crop_id] = new_total

        effects_this: list[str] = []
        if crop.monthly_effect:
            crop.monthly_effect(state, amount, effects_this)

        crop_reports.append({
            "name": crop.name,
            "food": food,
            "new_total": new_total,
            "effects": effects_this,
        })

    state.kingdom.total_food = state.kingdom.total_food + additional_food
    if hasattr(state, "last_month_summary") and crop_reports:
        lines: list[str] = []
        for r in crop_reports:
            food_phrase = f"produced {r['food']} food" if r["food"] else "produced no food"
            crop_phrase = f"grew to {r['new_total']} total crops"
            if r["effects"]:
                effects_phrase = "and had the following effects: " + "; ".join(r["effects"]) + "."
            else:
                effects_phrase = "and had no special effects."
            lines.append(f"Your {r['name']} {food_phrase}, {crop_phrase}, {effects_phrase}")
        state.last_month_summary.append("Crops: " + " ".join(lines))