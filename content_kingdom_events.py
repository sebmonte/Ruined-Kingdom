import random
from models import GameState, KingdomEvent, EventOption, Villager
from generators_villagers import generate_villager
from crops import CROP_DB


def _get_addicted_villager_and_substance(state: GameState, only_when_substance_count_is_zero: bool = False) -> tuple[Villager, str] | None:
    """Return a random villager who has an addiction and one of their addicted substances (crop_id), or None.
    If only_when_substance_count_is_zero is True, only consider villagers whose addicted substance has count 0 in kingdom.crops."""
    addicted = [(v, s.target) for v in state.kingdom.population for s in v.status if s.kind == "addicted" and s.target]
    if only_when_substance_count_is_zero:
        # Only include (villager, crop_id) where the kingdom has 0 of that crop in storage
        addicted = [(v, cid) for v, cid in addicted if state.kingdom.crops.get(cid, 0) == 0]
    if not addicted:
        return None
    v, crop_id = random.choice(addicted)
    return (v, crop_id)


def _has_addicted_villager_with_zero_stock(state: GameState) -> bool:
    """True if at least one villager is addicted to a substance whose count in kingdom.crops is 0."""
    return _get_addicted_villager_and_substance(state, only_when_substance_count_is_zero=True) is not None


def remove_random_villagers(state: GameState, n: int) -> int:
    """Remove up to n random villagers from the kingdom. Returns how many were removed."""
    pop = state.kingdom.population
    to_remove = min(n, len(pop))
    if to_remove <= 0:
        return 0
    for _ in range(to_remove):
        pop.pop(random.randrange(len(pop)))
    return to_remove


def infected_crops_event(state: GameState, advance) -> KingdomEvent:

    def burn_fields():
        loss = max(1, int(state.kingdom.total_food * 0.20))
        state.kingdom.total_food -= loss
        state.add_log(f"You dump and burn the infested fields and lose {loss} food.")
        advance(state)

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

        advance(state)

    return KingdomEvent(
        event_id="infected_crops",
        title="Infected Crops",
        description=(
            "A distraught farmer reports that an infection has taken over the food supplies. "
            "He asks what you propose to do about it. [Magic]"
        ),
        options=[
            EventOption(
                "Burn down the infested fields (-20% total food)", 
                burn_fields),
            EventOption(
                "Do nothing; let the people eat the rotten food (-10% population, 50% chance of additional -20%)", 
                do_nothing),
        ],
    )

def dog_discovery_event(state: GameState, advance) -> KingdomEvent:

    def discover_dog():
        state.kingdom.population.extend(generate_villager("dog") for _ in range(2))
        state.add_log("You discover a dog in the forest and bring it into the settlement.")
        advance(state)

    return KingdomEvent(
        event_id="dog_discovery",
        title="Dog Discovery",
        description="A hunter brings back a pair of wolves from the forest. “I reckon we can breed these to help with the hunt!",
        options=[EventOption("Bring the dog into the settlement", discover_dog)],
        repeatable=False,
    )

def rambunctious_monkey_event(state: GameState, advance) -> KingdomEvent:
    def tame_monkey():
        state.kingdom.population.append(generate_villager("human"))
        state.add_log("You tame the orangutan and bring it into the settlement.")
        advance(state)

    def send_raiding_party():
        state.kingdom.army_units["Soldiers"] = max(
            0,
            state.kingdom.army_units.get("Soldiers", 0) - 10 #If soldiers doesn't exist, return 0
        )
        state.add_log("A raiding party leaves to find and escort the monkey away. 10 soldiers are unavailable for the month.")
        advance(state)

    def mock_farmer():
        state.kingdom.loyalty = state.kingdom.loyalty - 2
        state.add_log("Your cruelty lowers loyalty by 2.")
        advance(state)

    def use_bananas():
        if "Bananas" in state.kingdom.crops:
            state.kingdom.crops["Bananas"] = max(0, state.kingdom.crops["Bananas"] - 2)
        state.add_log("The bananas lure the monkey away.")
        advance(state)

    def has_animal_husbandry(s: GameState) -> bool:
        return "Animal Husbandry" in s.kingdom.perks

    def has_bananas(s: GameState) -> bool:
        return s.kingdom.crops.get("Bananas", 0) >= 2
    def has_soldiers(s: GameState) -> bool:
        return s.kingdom.army_units.get("Soldiers", 0) >= 10

    return KingdomEvent(
        event_id="rambunctious_monkey",
        title="Rambunctious Monkey",
        description=(
            "An angry citizen approaches your desk. 'Sir, a wild orangutan has been disturbing "
            "the peace near my hovel. It wandered into the village and my bread is also going missing. "
            "I suspect the creature is at fault.'"
        ),
options=[
    EventOption(
        "[Animal Husbandry] Tame the orangutan and add it to your population",
        tame_monkey,
        has_animal_husbandry
    ),
    EventOption(
        "Send a raiding party to return it to the jungle",
        send_raiding_party,
        has_soldiers
    ),
    EventOption(
        "\"You can't deal with an ape?\" Lose 2 loyalty",
        mock_farmer
    ),
    EventOption(
        "[Bananas] Give the farmer two bananas to lure the monkey away",
        use_bananas,
        has_bananas
    ),
]
    )




def animal_language(state: GameState, advance) -> KingdomEvent:

    def reject_animal_language():
        state.add_log("May man be ever separate from lower creatures.")
        advance(state)

    def acquire_animal_language():
        state.kingdom.perks.append("Animal_Language")
        advance(state)
        return 

    return KingdomEvent(
        event_id="animal_language",
        title="Animal Language",
        description=(
            "Your psychologist has befriended a local monkey and used classical conditioning techniques to successfully teach him sign language."
            "Amazingly, he also taught the psychologist how to communicate with the animals of the forest. He suggests teaching you these secrets."
        ),
        options=[
            EventOption(
                "Learn Animal Language!",
                acquire_animal_language
            ),
            EventOption(
                "Reject Animal Language.",
                reject_animal_language,
            ),
        ],
        repeatable=True,
        retire_if=lambda s: "Animal_Language" in s.kingdom.perks,
    )



def drug_withdrawal_event(state: GameState, advance) -> KingdomEvent:
    """
    A villager addicted to a substance confronts you about the stores being empty.
    Only appears when at least one villager is addicted AND that substance's count in kingdom.crops is 0.
    """
    pair = _get_addicted_villager_and_substance(state, only_when_substance_count_is_zero=True)
    if pair is None:
        return KingdomEvent(
            event_id="drug_withdrawal",
            title="Drug Withdrawal",
            description="(This event is not available.)",
            options=[],
            available_if=_has_addicted_villager_with_zero_stock,
        )
    villager, crop_id = pair
    substance_display = CROP_DB[crop_id].name if crop_id in CROP_DB else crop_id
    description = (
        f"{villager.name} arrives at your office, looking furious. Beady, red eyes glare at you. "
        f'"Sir, there is no {substance_display} left in our stores. Frankly, I am disgusted that we are out of '
        f'{substance_display}. How am I supposed to feed my family?"'
    )

    def send_away():
        state.kingdom.loyalty = max(0, state.kingdom.loyalty - 2)
        state.add_log("You send them away. Loyalty drops by 2.")
        advance(state)

    def promise_restock():
        state.add_log("You promise to restock. They leave, somewhat mollified.")
        advance(state)

    def offer_food():
        give = min(5, state.kingdom.total_food)
        state.kingdom.total_food -= give
        state.add_log(f"You offer {give} food from the stores. They take it and leave.")
        advance(state)

    return KingdomEvent(
        event_id="drug_withdrawal",
        title="Drug Withdrawal",
        description=description,
        options=[
            EventOption("Send them away (-2 loyalty)", send_away),
            EventOption("Promise to restock", promise_restock),
            EventOption("Offer food from the stores (-5 food)", offer_food),
        ],
        repeatable=True,
        available_if=_has_addicted_villager_with_zero_stock,
    )


KINGDOM_EVENT_BUILDERS = [
    infected_crops_event,
    rambunctious_monkey_event,
    animal_language,
    dog_discovery_event,
    drug_withdrawal_event,
]