from dataclasses import dataclass
from typing import Callable

from models import Encounter, Choice, EventDefinition, GameState


@dataclass
class EventContext:
    state: "GameState"
    category: str
    event_id: str
    on_finish: Callable[["GameState"], None]

    def show(self, title: str, description: str, choices: list["Choice"]) -> None:
        self.state.current_encounter = auto_number_choices(
            Encounter(title=title, description=description, choices=choices)
        )

    def finish(self, log_text: str = "") -> None:
        if log_text:
            self.state.add_log(log_text)
        self.on_finish(self.state)


def auto_number_choices(encounter: Encounter) -> Encounter:
    return Encounter(
        title=encounter.title,
        description=encounter.description,
        choices=[Choice(str(i), c.text, c.effect) for i, c in enumerate(encounter.choices, 1)],
    )


def get_occurred_set(state, category: str) -> set[str]:
    if category == "kingdom":
        return state.occurred_kingdom_event_ids
    return state.occurred_encounter_ids


def get_remaining_count(state, category: str) -> int:
    if category == "kingdom":
        return state.events_remaining_this_month
    return state.encounters_remaining_this_month


def set_remaining_count(state, category: str, value: int) -> None:
    if category == "kingdom":
        state.events_remaining_this_month = value
    else:
        state.encounters_remaining_this_month = value


def eligible_definitions(state, definitions: list[EventDefinition], category: str) -> list[EventDefinition]:
    occurred = get_occurred_set(state, category)
    out = []

    for d in definitions:
        if d.category != category:
            continue
        if d.event_id in occurred and not d.repeatable:
            continue
        if d.retire_if is not None and d.retire_if(state):
            continue
        if d.available_if is not None and not d.available_if(state):
            continue
        out.append(d)

    return out


def mark_occurred_if_needed(state, defn: EventDefinition) -> None:
    if not defn.repeatable:
        occurred = get_occurred_set(state, defn.category)
        occurred.add(defn.event_id)