"""
Kingdom hub and menu logic.

- enter_kingdom: main hub screen when the player returns home; presents menu choices.
- event_picker: builds the monthly event queue, filters by eligibility (occurred, retire_if, available_if),
  and shows the next kingdom event when the player chooses "Events".
- advance_kingdom_event / finish_kingdom_events: handle event completion and return to hub.
- show_monthly_summary: shown after advancing the month; resets event count and queue on Continue.
- kingdom_*: individual menu screens (army, crops, population, perks, advisor, talk to king).
- set_kingdom_encounter: helper to set state.current_encounter for any kingdom screen.
"""
from models import GameState, KingdomEvent, EventOption, Choice, Encounter
from generators_npc import generate_npc
from content_kingdom_events import KINGDOM_EVENT_BUILDERS
from crops import CROP_DB
from month_advance import advance_month
import random


# ---------------------------------------------------------------------------
# Kingdom hub & entry
# ---------------------------------------------------------------------------

def enter_kingdom(state: GameState) -> None:
    """
    Main kingdom hub screen. Call this whenever the player returns home.
    Sets the current encounter to the hub menu (talk to king, view army/crops/perks/villagers,
    view events, advance month, leave).
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

    def view_perks():
        kingdom_view_perks(state)

    def view_population():
        kingdom_view_population(state)

    def do_advance_month():
        advance_month(state)
        show_monthly_summary(state)

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
            Choice("4", "View kingdom perks", view_perks),
            Choice("5", "Appoint an advisor", appoint_advisor),
            Choice("6", f"Events ({state.events_remaining_this_month} remaining)", view_events),
            Choice("7", "View villagers", view_population),
            Choice("8", "Advance month", do_advance_month),
            Choice("9", "Leave the kingdom", depart_again),
        ],
    )


# ---------------------------------------------------------------------------
# Kingdom event system (queue, eligibility, showing events)
# ---------------------------------------------------------------------------

def event_picker(state: GameState) -> None:
    """
    Handles the "Events" menu option. Builds a queue of up to 3 kingdom events when needed;
    each time the player chooses Events, shows the next event from the queue, then returns to hub.

    Eligibility: an event is included only if
    - its event_id is not in occurred_kingdom_event_ids (for non-repeatable events),
    - retire_if is None or returns False,
    - available_if is None or returns True.
    """
    if state.events_remaining_this_month <= 0:
        set_kingdom_encounter(
            state,
            title="No events remaining",
            description=(
                "You have no events remaining this month.\n\n"
                "Choose 'Advance month' from the kingdom to start a new month and receive new events."
            ),
            choices=[
                Choice("1", "Back", lambda: enter_kingdom(state)),
            ],
        )
        return

    queue = getattr(state, "kingdom_event_queue", []) or []
    index = getattr(state, "current_kingdom_event_index", 0)

    # Build a fresh queue only when we have none or we've exhausted it this month
    if not queue or index >= len(queue):
        # Every builder returns a KingdomEvent; we then filter by eligibility
        built = [builder(state, advance_kingdom_event) for builder in KINGDOM_EVENT_BUILDERS]
        occurred = getattr(state, "occurred_kingdom_event_ids", set()) or set()
        eligible = [
            e for e in built
            if e.event_id not in occurred
            and (e.retire_if is None or not e.retire_if(state))
            and (e.available_if is None or e.available_if(state))
        ]
        if not eligible:
            set_kingdom_encounter(
                state,
                title="No events available",
                description="No kingdom events are available this month (all have already occurred or are retired).",
                choices=[Choice("1", "Back", lambda: enter_kingdom(state))],
            )
            return
        # Sample up to 3 events for this month; player will see them one by one
        state.kingdom_event_queue = random.sample(eligible, k=min(3, len(eligible)))
        state.current_kingdom_event_index = 0

    show_current_kingdom_event(state)

def show_current_kingdom_event(state: GameState) -> None:
    """Display the next event in the queue, or finish the event flow if queue is exhausted."""
    if state.current_kingdom_event_index >= len(state.kingdom_event_queue):
        finish_kingdom_events(state)
        return

    event = state.kingdom_event_queue[state.current_kingdom_event_index]

    # Build choices from event options; skip options whose condition(state) is False
    choices = []
    key_counter = 1
    for option in event.options:
        if option.condition is None or option.condition(state):
            choices.append(Choice(str(key_counter), option.text, option.effect))
            key_counter += 1

    state.current_encounter = Encounter(
        title=event.title,
        description=event.description,
        choices=choices,
    )

def advance_kingdom_event(state: GameState) -> None:
    """Called when the player picks an option on a kingdom event. Records completion and returns to hub."""
    if state.current_kingdom_event_index < len(state.kingdom_event_queue):
        event = state.kingdom_event_queue[state.current_kingdom_event_index]
        if not event.repeatable:
            if not hasattr(state, "occurred_kingdom_event_ids"):
                state.occurred_kingdom_event_ids = set()
            state.occurred_kingdom_event_ids.add(event.event_id)
    state.current_kingdom_event_index += 1
    state.events_remaining_this_month -= 1
    enter_kingdom(state)


def finish_kingdom_events(state: GameState) -> None:
    """No more events this month; clear queue and counters, return to hub."""
    state.kingdom_event_queue = []
    state.current_kingdom_event_index = 0
    state.events_remaining_this_month = 0
    enter_kingdom(state)


# ---------------------------------------------------------------------------
# Monthly summary (after "Advance month")
# ---------------------------------------------------------------------------

def show_monthly_summary(state: GameState) -> None:
    """Show the monthly effects summary. 'Continue' resets events remaining to 3 and returns to hub."""
    def continue_to_kingdom():
        state.events_remaining_this_month = 3
        state.encounters_remaining_this_month = 3
        state.kingdom_event_queue = []
        state.current_kingdom_event_index = 0
        enter_kingdom(state)

    summary_text = "\n".join(state.last_month_summary) if state.last_month_summary else "Nothing to report."
    set_kingdom_encounter(
        state,
        title="Monthly report",
        description=summary_text,
        choices=[
            Choice("1", "Continue", continue_to_kingdom),
        ],
    )


# ---------------------------------------------------------------------------
# Kingdom menu screens (view army, crops, population, perks, advisor, talk to king)
# ---------------------------------------------------------------------------

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
            f'Total food: {state.kingdom.total_food}\n'
            f'Population: {len(state.kingdom.population)}'
        ),
        choices=[
            Choice("1", "Back", lambda: enter_kingdom(state)),
        ],
    )


def kingdom_view_army(state: GameState) -> None:
    """Show army unit counts; Back returns to hub."""
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
    """Show crop inventory (name, amount, description) and total food; Back returns to hub."""
    if state.kingdom.crops:
        crop_lines = []
        for crop_id, amount in state.kingdom.crops.items():
            crop = CROP_DB[crop_id]
            crop_lines.append(f"{crop.name}: {amount} — {crop.description}")
        crops_text = "\n".join(crop_lines)
    else:
        crops_text = "No crops planted."

    set_kingdom_encounter(
        state,
        title="The Crops",
        description=(
            f"{crops_text}\n\n"
            f"Stored food: {state.kingdom.total_food}\n"
        ),
        choices=[
            Choice("1", "Back", lambda: enter_kingdom(state)),
        ],
    )


# ---------------------------------------------------------------------------
# Population display helpers (status formatting, summary and full list text)
# ---------------------------------------------------------------------------

def _format_villager_status(s) -> str:
    """Turn a VillagerStatus into a display string (e.g. 'Addicted to Gloom Corn' or plain kind)."""
    if s.kind == "addicted" and s.target and s.target in CROP_DB:
        return f"Addicted to {CROP_DB[s.target].name}"
    if s.kind == "addicted" and s.target:
        return f"Addicted to {s.target}"
    return s.kind


# Trait thresholds for population summary: 9–10 = very high, 1–2 = very low
TRAIT_NAMES = ["willpower", "extraversion", "luck", "conscientiousness"]


def _population_summary_text(pop: list) -> str:
    """Build summary: race counts, very high/low trait counts, and status effect counts."""
    if not pop:
        return "You have no villagers."

    # Race counts
    race_counts: dict[str, int] = {}
    for v in pop:
        race = v.race.strip() or "unknown"
        race_counts[race] = race_counts.get(race, 0) + 1
    race_parts = [f"{race}s: {count}" for race, count in sorted(race_counts.items())]
    race_line = "Races: " + ", ".join(race_parts)

    # Trait counts: very high = 9-10, very low = 1-2
    trait_lines = []
    for attr in TRAIT_NAMES:
        high = sum(1 for v in pop if getattr(v, attr) >= 9)
        low = sum(1 for v in pop if getattr(v, attr) <= 2)
        parts = []
        if high:
            parts.append(f"{high} with very high {attr}")
        if low:
            parts.append(f"{low} with very low {attr}")
        if parts:
            trait_lines.append(", ".join(parts))

    # Status effect counts (e.g. "3 addicted to Gloom Corn, 2 sick")
    status_counts: dict[str, int] = {}
    for v in pop:
        for s in v.status:
            label = _format_villager_status(s)
            status_counts[label] = status_counts.get(label, 0) + 1
    status_parts = [f"{count} {label}" for label, count in sorted(status_counts.items())]
    status_line = ", ".join(status_parts) if status_parts else "None"

    lines = [race_line]
    if trait_lines:
        lines.append("")
        lines.append("Traits (very high = 9–10, very low = 1–2):")
        lines.extend(trait_lines)
    lines.append("")
    lines.append("Status effects: " + status_line)
    return "\n".join(lines)


def _population_full_list_text(pop: list) -> str:
    """Full per-villager list for the 'view full list' screen."""
    if not pop:
        return "You have no villagers."
    lines = []
    for i, v in enumerate(pop, start=1):
        status_text = ", ".join(_format_villager_status(s) for s in v.status) if v.status else "None"
        lines.append(f"{i}. {v.name} ({v.race}) | Status: {status_text}")
    return "\n".join(lines)


def kingdom_view_population(state: GameState) -> None:
    """Show population summary (races, traits, status counts) with option to view full per-villager list."""
    pop = state.kingdom.population
    summary_text = _population_summary_text(pop)

    def view_full_list():
        full_text = _population_full_list_text(pop)
        set_kingdom_encounter(
            state,
            title="Villagers — Full list",
            description=full_text,
            choices=[
                Choice("1", "Back", lambda: kingdom_view_population(state)),
            ],
        )

    set_kingdom_encounter(
        state,
        title="Villagers",
        description=summary_text,
        choices=[
            Choice("1", "View full list of villagers", view_full_list),
            Choice("2", "Back", lambda: enter_kingdom(state)),
        ],
    )


def kingdom_view_perks(state: GameState) -> None:
    """Show list of acquired perks; Back returns to hub."""
    if state.kingdom.perks:
        perk_text = "\n".join(state.kingdom.perks)
    else:
        perk_text = "No perks acquired."

    set_kingdom_encounter(
        state,
        title="Perks",
        description=f"{perk_text}\n",
        choices=[
            Choice("1", "Back", lambda: enter_kingdom(state)),
        ],
    )


def kingdom_appoint_advisor(state: GameState) -> None:
    """Create 3 advisor candidates if needed, then show choose-one screen; choosing sets kingdom.advisor."""
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


# ---------------------------------------------------------------------------
# Leaving kingdom & shared encounter setter
# ---------------------------------------------------------------------------

def leave_kingdom(state: GameState) -> None:
    """Leave the kingdom and re-enter encounter mode. Uses 3 encounters per month; if none left, show return-to-kingdom screen."""
    state.add_log(f"You leave {state.kingdom.name} and head back into the wilds.")

    from generators_encounters import get_next_encounter, _no_encounters_encounter

    encounter = get_next_encounter(state)
    if encounter is None:
        state.current_encounter = _no_encounters_encounter(state)
    else:
        state.current_encounter = encounter


def set_kingdom_encounter(state: GameState, title: str, description: str, choices: list[Choice]) -> None:
    """Set state.current_encounter to a kingdom menu or event screen (title, description, choices)."""
    state.current_encounter = Encounter(
        title=title,
        description=description,
        choices=choices,
    )