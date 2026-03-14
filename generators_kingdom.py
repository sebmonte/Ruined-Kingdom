"""
Kingdom hub and menu logic.

- enter_kingdom: main hub screen when the player returns home; presents menu choices.
- show_current_kingdom_event: pick one event at a time from current eligible (available_if evaluated each time).
- show_monthly_summary: shown after advancing the month; resets monthly counters on Continue.
- kingdom_*: individual menu screens (army, crops, population, perks, advisor, talk to king).
- set_kingdom_encounter: helper to set state.current_encounter for any kingdom screen.
"""

import random

from models import GameState, Choice, Encounter, EventDefinition
from generators_npc import generate_npc
from content_kingdom_events import KINGDOM_EVENT_DEFINITIONS
from crops import CROP_DB
from month_advance import advance_month
from event_runtime import EventContext, auto_number_choices, eligible_definitions, mark_occurred_if_needed
from content_perks import PERK_DEFINITIONS


def _perk_id_to_display_name(perk_id: str) -> str:
    """Resolve perk_id to display name for UI; event-granted perks may have no definition."""
    for p in PERK_DEFINITIONS:
        if p.perk_id == perk_id:
            return p.name
    return perk_id.replace("_", " ").title()


# ---------------------------------------------------------------------------
# Kingdom hub & entry
# ---------------------------------------------------------------------------

def enter_kingdom(state: GameState) -> None:
    """
    Main kingdom hub screen. Call this whenever the player returns home.
    Sets the current encounter to the hub menu.
    """
    def view_events():
        show_current_kingdom_event(state)

    def talk_to_advisor():
        kingdom_talk_to_advisor(state)

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
            Choice("", "Talk to your advisor", talk_to_advisor),
            Choice("", "View your army", view_army),
            Choice("", "View your crops", view_crops),
            Choice("", "View kingdom perks", view_perks),
            Choice("", "Appoint an advisor", appoint_advisor),
            Choice("", f"Events ({state.events_remaining_this_month} remaining)", view_events),
            Choice("", "View villagers", view_population),
            Choice("", "Advance month", do_advance_month),
            Choice("", "Leave the kingdom", depart_again),
        ],
    )


# ---------------------------------------------------------------------------
# Kingdom event system (queue, eligibility, showing events)
# ---------------------------------------------------------------------------

def _pick_one_kingdom_event(state: GameState) -> EventDefinition | None:
    """Pick one weighted random event from currently eligible definitions. Eligibility is evaluated now."""
    eligible = eligible_definitions(state, KINGDOM_EVENT_DEFINITIONS, "kingdom")
    if not eligible:
        return None
    weights = [d.weight for d in eligible]
    return random.choices(eligible, weights=weights, k=1)[0]


def show_current_kingdom_event(state: GameState) -> None:
    if state.events_remaining_this_month <= 0:
        enter_kingdom(state)
        return

    defn = _pick_one_kingdom_event(state)
    if defn is None:
        set_kingdom_encounter(
            state,
            "No events available",
            "No kingdom events are available this month.",
            [Choice("", "Back", lambda: enter_kingdom(state))],
        )
        return

    def on_finish(s: GameState) -> None:
        mark_occurred_if_needed(s, defn)
        s.events_remaining_this_month -= 1
        enter_kingdom(s)

    ctx = EventContext(
        state=state,
        category="kingdom",
        event_id=defn.event_id,
        on_finish=on_finish,
    )
    state.current_encounter = auto_number_choices(defn.builder(state, ctx))


def set_kingdom_encounter(
    state: GameState,
    title: str,
    description: str,
    choices: list[Choice],
) -> None:
    state.current_encounter = auto_number_choices(
        Encounter(
            title=title,
            description=description,
            choices=choices,
        )
    )


# ---------------------------------------------------------------------------
# Monthly summary (after "Advance month")
# ---------------------------------------------------------------------------

def show_monthly_summary(state: GameState) -> None:
    """Show the monthly effects summary. 'Continue' resets events remaining to 3 and returns to hub."""
    def continue_to_kingdom():
        state.events_remaining_this_month = 3
        state.encounters_remaining_this_month = 3
        enter_kingdom(state)

    summary_text = "\n".join(state.last_month_summary) if state.last_month_summary else "Nothing to report."
    set_kingdom_encounter(
        state,
        title="Monthly report",
        description=summary_text,
        choices=[
            Choice("", "Continue", continue_to_kingdom),
        ],
    )


# ---------------------------------------------------------------------------
# Kingdom menu screens (view army, crops, population, perks, advisor, talk to king)
# ---------------------------------------------------------------------------

def kingdom_talk_to_advisor(state: GameState) -> None:
    advisor_text = (
        state.kingdom.advisor.name + "listens in silence." if state.kingdom.advisor is not None else "No advisor appointed"
    )

    set_kingdom_encounter(
        state,
        title="Audience with your advisor",
        description=(
            f"{advisor_text}\n\n"
            f"Happiness: {state.kingdom.happiness}\n"
            f"Loyalty: {state.kingdom.loyalty}\n"
            f"Gold: {state.kingdom.gold}\n"
            f"Fear: {state.kingdom.fear}\n"
            f"Total food: {state.kingdom.total_food}\n"
            f"Population: {len(state.kingdom.population)}"
        ),
        choices=[
            Choice("", "Back", lambda: enter_kingdom(state)),
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
            Choice("", "Back", lambda: enter_kingdom(state)),
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
            Choice("", "Back", lambda: enter_kingdom(state)),
        ],
    )


# ---------------------------------------------------------------------------
# Population display helpers (status formatting, summary and full list text)
# ---------------------------------------------------------------------------

def _format_villager_status(s) -> str:
    """Turn a VillagerStatus into a display string."""
    if s.kind == "addicted" and s.target and s.target in CROP_DB:
        return f"Addicted to {CROP_DB[s.target].name}"
    if s.kind == "addicted" and s.target:
        return f"Addicted to {s.target}"
    return s.kind


TRAIT_NAMES = ["willpower", "extraversion", "luck", "conscientiousness"]


def _population_summary_text(pop: list) -> str:
    """Build summary: race counts, very high/low trait counts, and status effect counts."""
    if not pop:
        return "You have no villagers."

    race_counts: dict[str, int] = {}
    for v in pop:
        race = v.race.strip() or "unknown"
        race_counts[race] = race_counts.get(race, 0) + 1
    race_parts = [f"{race}s: {count}" for race, count in sorted(race_counts.items())]
    race_line = "Races: " + ", ".join(race_parts)

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
    """Show population summary with option to view full per-villager list."""
    pop = state.kingdom.population
    summary_text = _population_summary_text(pop)

    def view_full_list():
        full_text = _population_full_list_text(pop)
        set_kingdom_encounter(
            state,
            title="Villagers — Full list",
            description=full_text,
            choices=[
                Choice("", "Back", lambda: kingdom_view_population(state)),
            ],
        )

    set_kingdom_encounter(
        state,
        title="Villagers",
        description=summary_text,
        choices=[
            Choice("", "View full list of villagers", view_full_list),
            Choice("", "Back", lambda: enter_kingdom(state)),
        ],
    )
####PERKS####

def purchase_perk(state: GameState, perk) -> None:
    if perk.perk_id in state.kingdom.perks:
        kingdom_view_perk_detail(state, perk)
        return

    if state.kingdom.gold < perk.cost_gold:
        kingdom_view_perk_detail(state, perk)
        return

    if perk.purchase_if is not None and not perk.purchase_if(state):
        kingdom_view_perk_detail(state, perk)
        return

    state.kingdom.gold -= perk.cost_gold
    state.kingdom.perks.append(perk.perk_id)

    if perk.on_purchase is not None:
        perk.on_purchase(state)

    set_kingdom_encounter(
        state,
        title="Perk Purchased",
        description=f"You purchase {perk.name}.",
        choices=[
            Choice("", "Back to category", lambda: kingdom_view_perk_category(state, perk.category)),
            Choice("", "Back to perks", lambda: kingdom_view_perks(state)),
        ],
    )

def kingdom_view_perk_detail(state: GameState, perk) -> None:
    owned = perk.perk_id in state.kingdom.perks
    can_afford = state.kingdom.gold >= perk.cost_gold
    passes_req = perk.purchase_if(state) if perk.purchase_if is not None else True

    description = (
        f"{perk.description}\n\n"
        f"Cost: {perk.cost_gold} gold"
    )

    if owned:
        description += "\n\nYou already own this perk."
    elif not can_afford:
        description += "\n\nYou cannot afford this."
    elif not passes_req:
        description += "\n\nRequirements are not met."

    choices = []

    if not owned and can_afford and passes_req:
        choices.append(Choice("", f"Buy {perk.name}", lambda: purchase_perk(state, perk)))

    choices.append(Choice("", "Back", lambda: kingdom_view_perk_category(state, perk.category)))

    set_kingdom_encounter(
        state,
        title=perk.name,
        description=description,
        choices=choices,
    )
def kingdom_view_perk_category(state: GameState, category: str) -> None:
    perks = [p for p in PERK_DEFINITIONS if p.category == category]

    visible = []
    for p in perks:
        if p.available_if is None or p.available_if(state):
            visible.append(p)

    if not visible:
        set_kingdom_encounter(
            state,
            title=category.title(),
            description="No perks are currently available in this category.",
            choices=[Choice("", "Back", lambda: kingdom_view_perks(state))],
        )
        return

    desc_lines = []
    choices = []

    for perk in visible:
        owned = perk.perk_id in state.kingdom.perks
        status = "OWNED" if owned else f"{perk.cost_gold} gold"
        desc_lines.append(f"{perk.name} — {status}\n{perk.description}")

        choices.append(
            Choice("", f"View {perk.name}", lambda p=perk: kingdom_view_perk_detail(state, p))
        )

    choices.append(Choice("", "Back", lambda: kingdom_view_perks(state)))

    set_kingdom_encounter(
        state,
        title=category.title(),
        description="\n\n".join(desc_lines),
        choices=choices,)

def kingdom_view_perks(state: GameState) -> None:
    set_kingdom_encounter(
        state,
        title="Perks",
        description=(
            "Choose a category.\n\n"
            f"Gold: {state.kingdom.gold}\n"
            f"Owned perks: {', '.join(_perk_id_to_display_name(pid) for pid in state.kingdom.perks) if state.kingdom.perks else 'None'}"
        ),
        choices=[
            Choice("", "Farming perks", lambda: kingdom_view_perk_category(state, "farming")),
            Choice("", "Army perks", lambda: kingdom_view_perk_category(state, "army")),
            Choice("", "Expert perks", lambda: kingdom_view_perk_category(state, "experts")),
            Choice("", "Laws", lambda: kingdom_view_perk_category(state, "laws")),
            Choice("", "Back", lambda: enter_kingdom(state)),
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
                Choice("", "Back", lambda: enter_kingdom(state)),
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
            Choice("", f"Appoint {cands[0].name}", lambda: choose_candidate(0)),
            Choice("", f"Appoint {cands[1].name}", lambda: choose_candidate(1)),
            Choice("", f"Appoint {cands[2].name}", lambda: choose_candidate(2)),
            Choice("", "Back", lambda: enter_kingdom(state)),
        ],
    )


# ---------------------------------------------------------------------------
# Leaving kingdom
# ---------------------------------------------------------------------------

from generators_encounters import get_next_world_event


def leave_kingdom(state: GameState) -> None:
    state.add_log(f"You leave {state.kingdom.name} and head back into the wilds.")
    state.current_encounter = get_next_world_event(state)