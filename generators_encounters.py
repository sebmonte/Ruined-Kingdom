import random

from models import GameState, Encounter, Choice, EventDefinition
from event_runtime import EventContext, auto_number_choices, eligible_definitions, mark_occurred_if_needed
from content_world_events import WORLD_EVENT_DEFINITIONS


# ----------------------------
# World flow
# ----------------------------

def no_encounters_screen(state: GameState) -> Encounter:
    from generators_kingdom import enter_kingdom

    return Encounter(
        title="No encounters remaining",
        description=(
            "You have no encounters remaining this month.\n\n"
            "Return to the kingdom and choose 'Advance month' to start a new month "
            "and receive three more encounters."
        ),
        choices=[Choice("", "Return to the kingdom", lambda: enter_kingdom(state))],
    )


def get_next_world_event(state: GameState) -> Encounter:
    if state.encounters_remaining_this_month <= 0:
        return auto_number_choices(no_encounters_screen(state))

    eligible = eligible_definitions(state, WORLD_EVENT_DEFINITIONS, "world")
    if not eligible:
        return auto_number_choices(no_encounters_screen(state))

    defn = random.choices(
        eligible,
        weights=[d.weight for d in eligible],
        k=1
    )[0]

    def on_finish(s: GameState):
        mark_occurred_if_needed(s, defn)
        s.encounters_remaining_this_month -= 1
        s.area_index += 1
        s.current_encounter = get_next_world_event(s)

    ctx = EventContext(
        state=state,
        category="world",
        event_id=defn.event_id,
        on_finish=on_finish,
    )
    return auto_number_choices(defn.builder(state, ctx))