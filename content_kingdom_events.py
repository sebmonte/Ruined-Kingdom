import random
from models import GameState, KingdomEvent, EventOption


def infected_crops_event(state: GameState, advance) -> KingdomEvent:

    def burn_fields():
        loss = max(1, int(state.kingdom.total_food * 0.20))
        state.kingdom.total_food -= loss
        state.add_log(f"You burn the infested fields and lose {loss} food.")
        advance(state)

    def do_nothing():
        loss = max(1, int(state.kingdom.population * 0.10))
        state.add_log(f"You allow the people to eat the rotten food and lose {loss} population.")
        state.kingdom.population = max(
            0,
            state.kingdom.population - loss)

        if random.random() < 0.5:
            extra_loss = max(1, int(state.kingdom.population * 0.20))
            state.kingdom.population = max(0, state.kingdom.population - extra_loss)
            state.add_log(f"Sickness spreads further. You lose an additional {extra_loss} population.")

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


def rambunctious_monkey_event(state: GameState, advance) -> KingdomEvent:
    def tame_monkey():
        state.kingdom.population += 1
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
        event_id="rambunctious_monkey",
        title="Rambunctious Monkey",
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
]
    )


KINGDOM_EVENT_BUILDERS = [
    infected_crops_event,
    rambunctious_monkey_event,
    animal_language
]