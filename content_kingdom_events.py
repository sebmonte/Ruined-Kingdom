"""
File for kingdom events (3 per month)

Each kingdom event is an EventDefinition whose builder returns an Encounter.
Choices can either:
- log/apply effects and call ctx.finish()
- or show a follow-up screen with ctx.show(...)
"""

import random

from models import GameState, Villager, Encounter, Choice, EventDefinition
from generators_villagers import generate_villager
from crops import CROP_DB

def remove_random_villagers(state: GameState, n: int) -> int:
    """Remove up to n random villagers from the kingdom. Returns how many were removed."""
    pop = state.kingdom.population
    to_remove = min(n, len(pop))
    if to_remove <= 0:
        return 0
    for _ in range(to_remove):
        pop.pop(random.randrange(len(pop)))
    return to_remove


# ---------------------------------------------------------------------------
# Infected crops
# ---------------------------------------------------------------------------

def build_infected_crops(state: GameState, ctx) -> Encounter:
    def burn_fields():
        loss = max(1, int(state.kingdom.total_food * 0.20))
        state.kingdom.total_food -= loss
        ctx.finish(f"You dump and burn the infested fields and lose {loss} food.")

    def do_nothing():
        count = len(state.kingdom.population)
        loss = max(1, int(count * 0.10))
        removed = remove_random_villagers(state, loss)
        state.add_log(f"You allow the people to eat the rotten food and lose {removed} population.")

        if random.random() < 0.5:
            count = len(state.kingdom.population)
            extra_loss = max(1, int(count * 0.20))
            extra_removed = remove_random_villagers(state, extra_loss)
            state.add_log(f"Sickness spreads further. You lose an additional {extra_removed} population.")

        ctx.finish()

    return Encounter(
        title="Infected Crops",
        description=(
            "A distraught farmer reports that an infection has taken over the food supplies. "
            "He asks what you propose to do about it. [Magic]"
        ),
        choices=[
            Choice("", "Burn down the infested fields (-20% total food)", burn_fields),
            Choice(
                "",
                "Do nothing; let the people eat the rotten food (-10% population, 50% chance of additional -20%)",
                do_nothing,
            ),
        ],
    )


INFECTED_CROPS = EventDefinition(
    event_id="infected_crops",
    builder=build_infected_crops,
    category="kingdom",
    repeatable=True,
    weight=1,
)


# ---------------------------------------------------------------------------
# Dog discovery
# ---------------------------------------------------------------------------

def build_dog_discovery(state: GameState, ctx) -> Encounter:
    def discover_dog():
        state.kingdom.population.extend(generate_villager("dog") for _ in range(2))
        state.add_log("You bring the animals into the settlement.")
        ctx.finish()

    return Encounter(
        title="Dog Discovery",
        description=(
            "A hunter brings back a pair of wild dogs from the forest. "
            "\"I reckon we can breed these to help with the hunt!\""
        ),
        choices=[Choice("", "Bring the dogs into the settlement", discover_dog)],
    )


DOG_DISCOVERY = EventDefinition(
    event_id="dog_discovery",
    builder=build_dog_discovery,
    category="kingdom",
    repeatable=True,
    weight=1,
)


# ---------------------------------------------------------------------------
# Rambunctious monkey
# ---------------------------------------------------------------------------

def build_rambunctious_monkey(state: GameState, ctx) -> Encounter:
    def tame_monkey():
        state.kingdom.population.append(generate_villager("human"))
        state.add_log("You tame the orangutan and bring it into the settlement.")
        ctx.finish()

    def send_raiding_party():
        state.kingdom.army_units["Warriors"] = max(
            0,
            state.kingdom.army_units.get("Warriors", 0) - 10,
        )
        state.add_log(
            "A raiding party leaves to find and escort the monkey away. "
            "10 Warriors are unavailable for the month."
        )
        ctx.finish()

    def mock_farmer():
        state.kingdom.loyalty -= 2
        state.add_log("Your cruelty lowers loyalty by 2.")
        ctx.finish()

    def use_bananas():
        state.kingdom.crops["Bananas"] = max(0, state.kingdom.crops.get("Bananas", 0) - 2)
        state.add_log("The bananas lure the monkey away.")
        ctx.finish()

    def has_animal_husbandry(s: GameState) -> bool:
        return "animal_husbandry" in s.kingdom.perks

    def has_bananas(s: GameState) -> bool:
        return s.kingdom.crops.get("Bananas", 0) >= 2

    def has_soldiers(s: GameState) -> bool:
        return s.kingdom.army_units.get("Warriors", 0) >= 10

    choices: list[Choice] = []

    if has_animal_husbandry(state):
        choices.append(
            Choice("", "[Animal Husbandry] Tame the orangutan and add it to your population", tame_monkey)
        )

    if has_soldiers(state):
        choices.append(
            Choice("", "Send a raiding party to return it to the jungle", send_raiding_party)
        )

    choices.append(
        Choice("", "\"You can't deal with an ape?\" Lose 2 loyalty", mock_farmer)
    )

    if has_bananas(state):
        choices.append(
            Choice("", "[Bananas] Give the farmer two bananas to lure the monkey away", use_bananas)
        )

    return Encounter(
        title="Rambunctious Monkey",
        description=(
            "An angry citizen approaches your desk. \"Sir, a wild orangutan has been disturbing "
            "the peace near my hovel. It wandered into the village and my bread is also going missing. "
            "I suspect the creature is at fault.\""
        ),
        choices=choices,
    )


RAMBUNCTIOUS_MONKEY = EventDefinition(
    event_id="rambunctious_monkey",
    builder=build_rambunctious_monkey,
    category="kingdom",
    repeatable=True,
    weight=1,
)


# ---------------------------------------------------------------------------
# Animal language
# ---------------------------------------------------------------------------

def build_animal_language(state: GameState, ctx) -> Encounter:
    def reject_animal_language():
        state.add_log("May man be ever separate from lower creatures.")
        ctx.finish()

    def acquire_animal_language():
        state.add_log("You learn the secrets of bestial talk.")
        state.kingdom.perks.append("animal_language")
        ctx.finish()

    return Encounter(
        title="Animal Language",
        description=(
            "Your psychologist has befriended a local monkey and used classical conditioning "
            "techniques to successfully teach him sign language. Amazingly, he also taught the "
            "psychologist how to communicate with the animals of the forest. He suggests teaching "
            "you these secrets."
        ),
        choices=[
            Choice("", "Learn Animal Language!", acquire_animal_language),
            Choice("", "Reject Animal Language.", reject_animal_language),
        ],
    )


ANIMAL_LANGUAGE = EventDefinition(
    event_id="animal_language",
    builder=build_animal_language,
    category="kingdom",
    repeatable=False,
    retire_if=lambda s: "animal_language" in s.kingdom.perks,
    available_if=lambda s: "psychologist" in s.kingdom.perks,
    weight=100,
)


# ---------------------------------------------------------------------------
# Drug withdrawal
# ---------------------------------------------------------------------------

def _get_addicted_villager_and_substance(
    state: GameState,
    only_when_substance_count_is_zero: bool = False,
) -> tuple[Villager, str] | None:
    """
    Return a random villager who has an addiction and one of their addicted substances (crop_id),
    or None. If only_when_substance_count_is_zero is True, only consider villagers whose addicted
    substance has count 0 in kingdom.crops.
    """
    addicted = [
        (v, s.target)
        for v in state.kingdom.population
        for s in v.status
        if s.kind == "addicted" and s.target
    ]

    if only_when_substance_count_is_zero:
        addicted = [(v, cid) for v, cid in addicted if state.kingdom.crops.get(cid, 0) == 0]

    if not addicted:
        return None

    v, crop_id = random.choice(addicted)
    return (v, crop_id)


def _has_addicted_villager_with_zero_stock(state: GameState) -> bool:
    """True if at least one villager is addicted to a substance whose count in kingdom.crops is 0."""
    return _get_addicted_villager_and_substance(
        state,
        only_when_substance_count_is_zero=True,
    ) is not None


def build_drug_withdrawal(state: GameState, ctx) -> Encounter:
    """
    A villager addicted to a substance confronts you about the stores being empty.
    Only appears when at least one villager is addicted and that substance count is 0.
    """
    pair = _get_addicted_villager_and_substance(state, only_when_substance_count_is_zero=True)

    if pair is None:
        return Encounter(
            title="Drug Withdrawal",
            description="No one in the settlement is currently in withdrawal.",
            choices=[Choice("", "Back", lambda: ctx.finish())],
        )

    villager, crop_id = pair
    substance_display = CROP_DB[crop_id].name if crop_id in CROP_DB else crop_id

    description = (
        f"{villager.name} arrives at your office, looking furious. Beady, red eyes glare at you. "
        f"\"Sir, there is no {substance_display} left in our stores. Frankly, I am morally revolted "
        f"that we are out of {substance_display}. How am I supposed to feed my family?\""
    )

    def send_away():
        state.kingdom.loyalty = max(0, state.kingdom.loyalty - 2)
        state.add_log("You send them away. Loyalty drops by 2.")
        ctx.finish()

    def execute_addict():
        if villager in state.kingdom.population:
            state.kingdom.population.remove(villager)
        state.kingdom.fear += 4
        state.add_log(
            f"You execute {villager.name} on the spot. They are removed from the population, and fear spreads."
        )
        ctx.finish()

    def offer_food():
        give = min(5, state.kingdom.total_food)
        state.kingdom.total_food -= give
        state.add_log(f"You offer {give} food from the stores. They take it and leave.")
        ctx.finish()

    return Encounter(
        title="Drug Withdrawal",
        description=description,
        choices=[
            Choice("", "Send them away (-2 loyalty)", send_away),
            Choice("", "Execute the disgruntled villager on the spot", execute_addict),
            Choice("", "Offer food from the stores (-5 food)", offer_food),
        ],
    )


DRUG_WITHDRAWAL = EventDefinition(
    event_id="drug_withdrawal",
    builder=build_drug_withdrawal,
    category="kingdom",
    repeatable=True,
    available_if=_has_addicted_villager_with_zero_stock,
    weight=1,
)


# ---------------------------------------------------------------------------
# Hidden treasure
# ---------------------------------------------------------------------------

def _villager_with_highest_luck(state: GameState) -> Villager | None:
    """Return a villager with the highest luck in the kingdom; if tie, pick one at random."""
    if not state.kingdom.population:
        return None
    best_luck = max(v.luck for v in state.kingdom.population)
    candidates = [v for v in state.kingdom.population if v.luck == best_luck]
    return random.choice(candidates)


def _has_any_villagers(state: GameState) -> bool:
    return len(state.kingdom.population) > 0


def build_hidden_treasure(state: GameState, ctx) -> Encounter:
    villager = _villager_with_highest_luck(state)

    if villager is None:
        return Encounter(
            title="Hidden Treasure",
            description="There is no one in the kingdom to make such a claim.",
            choices=[Choice("", "Back", lambda: ctx.finish())],
        )

    kingdom_name = state.kingdom.name
    lucky_name = villager.name
    lucky_luck = villager.luck

    def wave_away():
        ctx.finish(f"You wave {lucky_name} out of your office.")

    def send_to_fetch():
        odds_by_luck = {
            10: (0.90, 0.08, 0.02),
            9: (0.80, 0.18, 0.02),
            8: (0.70, 0.25, 0.05),
            7: (0.45, 0.45, 0.10),
            6: (0.35, 0.50, 0.15),
            5: (0.10, 0.70, 0.20),
            4: (0.04, 0.51, 0.45),
            3: (0.01, 0.36, 0.63),
            2: (0.005, 0.21, 0.785),
            1: (0.002, 0.12, 0.878),
        }

        success_prob, moderate_prob, _failure_prob = odds_by_luck[lucky_luck]
        r = random.random()

        intro = (
            f"{lucky_name} closes their eyes and sticks their hand out, calling for their luck to guide them. "
            "They reach a random spot in the fields and point to it. \"Gold is buried here, I know it!\"\n\n"
        )

        if r < success_prob:
            gold_found = random.randint(20, 50)
            state.kingdom.gold += gold_found
            outcome = intro + f"You dig up a pirate's chest filled with gold. ({gold_found} gold added.)"
            state.add_log(f"{gold_found} gold was found.")
        elif r < success_prob + moderate_prob:
            outcome = intro + f"You dig up the ground and find nothing. {lucky_name} looks surprised."
            state.add_log("No treasure was found.")
        else:
            if villager in state.kingdom.population:
                state.kingdom.population.remove(villager)
            outcome = intro + f"You uncover a device that explodes, killing {lucky_name} instantly."
            state.add_log(f"{lucky_name} failed to find the treasure and was killed.")

        ctx.show(
            title="Hidden Treasure",
            description=outcome,
            choices=[Choice("", "Return to the kingdom", lambda: ctx.finish())],
        )

    return Encounter(
        title="Hidden Treasure",
        description=(
            f"{lucky_name} approaches you. They proudly proclaim, "
            f"\"I have been declared the luckiest citizen of {kingdom_name}! "
            f"I recently sensed the presence of a nearby treasure buried underground. "
            f"Shall I fetch it?\" (Luck: {lucky_luck})"
        ),
        choices=[
            Choice("", "Send the villager to fetch the chest.", send_to_fetch),
            Choice("", "Wave the villager out of your office.", wave_away),
        ],
    )


HIDDEN_TREASURE = EventDefinition(
    event_id="hidden_treasure",
    builder=build_hidden_treasure,
    category="kingdom",
    repeatable=True,
    available_if=_has_any_villagers,
    weight=1,
)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

KINGDOM_EVENT_DEFINITIONS: list[EventDefinition] = [
    INFECTED_CROPS,
    RAMBUNCTIOUS_MONKEY,
    ANIMAL_LANGUAGE,
    DOG_DISCOVERY,
    DRUG_WITHDRAWAL,
    HIDDEN_TREASURE,
]