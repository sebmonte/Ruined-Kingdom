from models import GameState, KingdomEvent, EventOption, Choice, Encounter
from generators_npc import generate_npc
from content_kingdom_events import KINGDOM_EVENT_BUILDERS
import random







def enter_kingdom(state: GameState) -> None:
    """
    Main kingdom hub screen.
    Call this whenever the player returns home.
    """
    def view_events():
        event_picker(state)
    def talk_to_king():
        kingdom_talk_to_king(state)

    def view_army():
        kingdom_view_army(state)

    def view_crops():
        kingdom_view_crops(state)

    def appoint_advisor():
        kingdom_appoint_advisor(state)

    def depart_again():
        leave_kingdom(state)

    set_kingdom_encounter(
        state,
        title=f"{state.kingdom.name}",
        description=(
            f"You return to {state.kingdom.name}.\n\n"
            f"The halls are quiet, and the burdens of rule await you."
        ),
        choices=[
            Choice("1", "Talk to the king", talk_to_king),
            Choice("2", "View your army", view_army),
            Choice("3", "View your crops", view_crops),
            Choice("4", "Appoint an advisor", appoint_advisor),
            Choice("5", "Events", view_events),
            Choice("6", "Leave the kingdom", depart_again),
        ],
    )

def event_picker(state: GameState) -> None:
    """
    Picks 3 random kingdom events and starts the event cycle.
    """
    chosen_builders = random.sample(KINGDOM_EVENT_BUILDERS, k=min(3, len(KINGDOM_EVENT_BUILDERS)))
    state.kingdom_event_queue = [builder(state, advance_kingdom_event) for builder in chosen_builders]
    state.current_kingdom_event_index = 0
    show_current_kingdom_event(state)

def show_current_kingdom_event(state: GameState) -> None:
    if state.current_kingdom_event_index >= len(state.kingdom_event_queue): #If we have been through three events, finish the queue
        finish_kingdom_events(state)
        return

    event = state.kingdom_event_queue[state.current_kingdom_event_index] #Select the current event

    choices = [] #Loop through the options for events and append the choices
    key_counter = 1

    for option in event.options:
        if option.condition is None or option.condition(state):
            choices.append(
                Choice(str(key_counter), option.text, option.effect)
            )
            key_counter += 1
    state.current_encounter = Encounter(
        title=event.title,
        description=event.description,
        choices=choices,
    )
def advance_kingdom_event(state: GameState) -> None:
    state.current_kingdom_event_index += 1
    show_current_kingdom_event(state)

def finish_kingdom_events(state: GameState) -> None:
    state.kingdom_event_queue = []
    state.current_kingdom_event_index = 0
    enter_kingdom(state)

def kingdom_talk_to_king(state: GameState) -> None:
    advisor_text = (
        state.kingdom.advisor.name if state.kingdom.advisor is not None else "No advisor appointed"
    )

    set_kingdom_encounter(
        state,
        title="Audience with the King",
        description=(
            f'The king sits on the cedar throne and listens in silence.\n\n'
            f'Advisor: {advisor_text}\n'
            f'Happiness: {state.kingdom.happiness}\n'
            f'Fear: {state.kingdom.fear}\n'
            f'Total food: {state.kingdom.total_food}'
        ),
        choices=[
            Choice("1", "Back", lambda: enter_kingdom(state)),
        ],
    )


def kingdom_view_army(state: GameState) -> None:
    if state.kingdom.army_units:
        army_text = "\n".join(
            f"{unit}: {count}" for unit, count in state.kingdom.army_units.items()
        )
    else:
        army_text = "Your army is empty."

    set_kingdom_encounter(
        state,
        title="The Army",
        description=army_text,
        choices=[
            Choice("1", "Back", lambda: enter_kingdom(state)),
        ],
    )


def kingdom_view_crops(state: GameState) -> None:
    crops_text = ", ".join(state.kingdom.crop_types) if state.kingdom.crop_types else "No crops planted."

    set_kingdom_encounter(
        state,
        title="The Crops",
        description=(
            f"Crop types: {crops_text}\n\n"
            f"Stored food: {state.kingdom.total_food}"
        ),
        choices=[
            Choice("1", "Back", lambda: enter_kingdom(state)),
        ],
    )


def kingdom_appoint_advisor(state: GameState) -> None:
    """
    Creates 3 candidates if none exist yet, then lets the player inspect/choose.
    """
    if not hasattr(state.kingdom, "advisor_candidates") or not state.kingdom.advisor_candidates:
        state.kingdom.advisor_candidates = [
            generate_npc("human"),
            generate_npc("human"),
            generate_npc("human"),
        ]

    cands = state.kingdom.advisor_candidates

    def choose_candidate(index: int):
        candidate = state.kingdom.advisor_candidates[index]
        state.kingdom.advisor = candidate
        state.kingdom.advisor_candidates = []
        set_kingdom_encounter(
            state,
            title="Advisor Appointed",
            description=f"You appoint {candidate.name} as your advisor.",
            choices=[
                Choice("1", "Back", lambda: enter_kingdom(state)),
            ],
        )

    desc_lines = []
    for i, npc in enumerate(cands, start=1):
        desc_lines.append(
            f"{i}. {npc.name} | Charm {npc.charm}, Warmth {npc.warmth}, "
            f"Morality {npc.morality}, Unpredictability {npc.unpredictability}"
        )

    set_kingdom_encounter(
        state,
        title="Choose an Advisor",
        description="\n\n".join(desc_lines),
        choices=[
            Choice("1", f"Appoint {cands[0].name}", lambda: choose_candidate(0)),
            Choice("2", f"Appoint {cands[1].name}", lambda: choose_candidate(1)),
            Choice("3", f"Appoint {cands[2].name}", lambda: choose_candidate(2)),
            Choice("4", "Back", lambda: enter_kingdom(state)),
        ],
    )


def leave_kingdom(state: GameState) -> None:
    """
    Sends the player back out into encounter mode.
    """
    state.add_log(f"You leave {state.kingdom.name} and head back into the wilds.")

    # You can reset a countdown here later if you want.
    # Example:
    # state.steps_until_kingdom = 5

    from generators_encounters import generate_biome, generate_encounter

    state.current_biome = generate_biome(state.area_index)
    state.current_encounter = generate_encounter(state)


def set_kingdom_encounter(state: GameState, title: str, description: str, choices: list[Choice]) -> None:
    state.current_encounter = Encounter(
        title=title,
        description=description,
        choices=choices,
    )