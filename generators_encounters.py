import random
from typing import Callable
from models import GameState, Encounter, Choice, NPC, WorldEncounterDefinition
from content_loader import ENCOUNTERS
from generators_npc import generate_npc

# ----------------------------
# Procedural generation
# ----------------------------

def choice(text: str, effect) -> Choice:
    """Choice without a key; keys are assigned automatically when the encounter is set."""
    return Choice("", text, effect)


def encounter_traincar(state: GameState) -> Encounter:
    """Traincar encounter: enter or avoid; inside, depart or meet the seer."""

    def train_leave():
        end_encounter(state, "You leave the traincar alone.")

    def train_enter():
        state.add_log("You step into the traincar. Dust billows up from the floor.")
        scenarios = [train_depart, train_seer]
        random.choice(scenarios)()

    def train_depart():
        state.add_log("test1")
        set_encounter(
            state,
            title="The Departure",
            description="Suddenly you feel the car shake. The soft whine of a motor reverberates through the darkness. Slivers of light through holes in the roof bring in the sound of a departure bell.",
            choices=[choice("Await your destination", train_leave)],
        )

    def train_seer():
        state.add_log("test2")
        if state.current_npc is None:
            state.current_npc = generate_npc("human")
        seer = state.current_npc
        name_known = state.flags.get("seer_name_learned", False)
        if state.flags.get("seer_spoken", False):
            if name_known:
                desc = f"{seer.name} waits silently for your answer."
            else:
                desc = "The seer waits silently for your answer."
        else:
            desc = "A small lantern lights a wooden table at the end of the car, illuminating the long white beard of an old man who beckons you over."
            state.flags["seer_spoken"] = True
        choices = [
            choice("What is your name", seer_name),
            choice("What are you doing on this train?", seer_train),
            choice("What do you do?", seer_job),
            choice("Can you tell the future?", seer_future),
        ]
        if not state.flags.get("seer_help_taken", False):
            choices.append(choice("Can you help me?", seer_help))
        choices.append(choice("Leave the Seer", train_leave))
        set_encounter(state, title="The Seer", description=desc, choices=choices)

    def seer_future():
        set_encounter(
            state,
            title="The Seer",
            description=(
                '"When I peer into the beyond, I see a foggy haze.\n\n'
                "Sometimes I can grasp onto something there, the contours of an object perhaps, but it always seems to slip away.\n\n"
                'It is a life of frustration, but occasional insight."'
            ),
            choices=[choice("Back", train_seer)],
        )

    def seer_name():
        seer = state.current_npc
        state.flags["seer_name_learned"] = True
        set_encounter(
            state,
            title="The Seer",
            description=f"My friends call me {seer.name}.",
            choices=[choice("Back", train_seer)],
        )

    def seer_train():
        set_encounter(
            state,
            title="The Seer",
            description=(
                "Long ago, this track used to connect *Alderwyn* to the ruined city of *Kash*. I used it regularly for sojourns to a school of magic deep in the forest near *Kash*. This was nearly a century ago, before I retired to be caretaker of these woods. I found it broken down and decided to use it as my residence during my final years."
            ),
            choices=[choice("Back", train_seer)],
        )

    def seer_job():
        seer = state.current_npc
        if seer.morality >= 3:
            seer_job_desc = "I walk along the rivers and crags deep in the forest. I feed the animals; I protect them from darkness."
        else:
            seer_job_desc = "I walk along the rivers and crags deep in the forest. I try to spread the influence of the shadows; I chant spells to lead demons into the souls of the wildlife."
        set_encounter(
            state,
            title="The Seer",
            description=seer_job_desc,
            choices=[choice("Back", train_seer)],
        )

    def seer_help():
        state.flags["seer_help_taken"] = True
        set_encounter(
            state,
            title="The Seer",
            description='The seer draws your attention to a deck of cards on the table. "I have infused these cards with magical insight. Someone ought to make use of them before I pass. I will let you pick one." He splays three cards in front of you.',
            choices=[
                choice("The card a snake wrapped around a sword", train_seer),
                choice("The card with a bright, pulsating heart", train_seer),
                choice("The card a deer drinking at a stream", train_seer),
            ],
        )

    return Encounter(
        title="A Hidden Traincar",
        description=(
            "While walking through the wilds, you come to a clearing and spot "
            "an old train resting on rusty tracks. The final car on the train appears to be partially open, "
            "allowing you a way in if you so choose."
        ),
        choices=[
            choice("Enter the car", train_enter),
            choice("Avoid the car", train_leave),
        ],
    )


def encounter_golem(state: GameState) -> Encounter:
    """Golem encounter: talk to the golem then move to next area."""
    def only():
        state.add_log("You talk to the golem")
        next_area(state)

    return Encounter(
        title="A golem",
        description="A golem stands in the wilds.",
        choices=[choice("Talk to the golem", only)],
    )


# Registry: each encounter has an id, builder, and optional repeatable / retire_if / available_if (like kingdom events)
WORLD_ENCOUNTER_DEFINITIONS: list[WorldEncounterDefinition] = [
    WorldEncounterDefinition("traincar", encounter_traincar, repeatable=True),
    WorldEncounterDefinition("golem", encounter_golem, repeatable=True),
]
WORLD_ENCOUNTER_BY_ID: dict[str, WorldEncounterDefinition] = {
    d.encounter_id: d for d in WORLD_ENCOUNTER_DEFINITIONS
}

# Optional pool from data: if set, only these ids can be chosen; otherwise all definitions are eligible
ENCOUNTER_POOL_IDS: list[str] = ENCOUNTERS.get("encounters", [d.encounter_id for d in WORLD_ENCOUNTER_DEFINITIONS])


def _get_eligible_definitions(state: GameState) -> list[WorldEncounterDefinition]:
    """Definitions that can be offered: in pool, not occurred (or repeatable), retire_if and available_if pass."""
    occurred = getattr(state, "occurred_encounter_ids", set()) or set()
    pool_set = set(ENCOUNTER_POOL_IDS)
    eligible = []
    for d in WORLD_ENCOUNTER_DEFINITIONS:
        if d.encounter_id not in pool_set: #if encounter id is not in the pool, skip
            continue
        if d.encounter_id in occurred and not d.repeatable: #if encounter id has already occurred and is not repeatable, skip
            continue
        if d.retire_if is not None and d.retire_if(state): #if retire_if is not None and retire_if returns True, skip
            continue
        if d.available_if is not None and not d.available_if(state): #if avaiable_if is missing or returns False, skip (avaiable if is a condition that must be met for the encounter to be eligible)
            continue
        eligible.append(d)
    return eligible


def _finish_current_encounter(state: GameState) -> None:
    """If there is a current encounter id and it is non-repeatable, mark it occurred; clear the id."""
    eid = getattr(state, "current_encounter_id", None)
    if eid is None:
        return
    state.current_encounter_id = None
    defn = WORLD_ENCOUNTER_BY_ID.get(eid)
    if defn is not None and not defn.repeatable:
        if not hasattr(state, "occurred_encounter_ids"):
            state.occurred_encounter_ids = set()
        state.occurred_encounter_ids.add(eid)


def _auto_number_choices(encounter: Encounter) -> Encounter:
    """Return a copy of the encounter with choices keyed 1, 2, 3... (like kingdom events)."""
    rekeyed = [Choice(str(i), c.text, c.effect) for i, c in enumerate(encounter.choices, 1)]
    return Encounter(title=encounter.title, description=encounter.description, choices=rekeyed)


def get_next_encounter(state: GameState) -> Encounter | None:
    """
    Finish the current encounter (mark occurred if non-repeatable), then if the player has
    encounters remaining this month and there is an eligible definition, pick one at random,
    decrement remaining, set current_encounter_id, and return the built encounter. Otherwise return None.
    """
    _finish_current_encounter(state)
    remaining = getattr(state, "encounters_remaining_this_month", 3)
    if remaining <= 0:
        return None
    eligible = _get_eligible_definitions(state)
    if not eligible:
        return None
    defn = random.choice(eligible)
    state.encounters_remaining_this_month = remaining - 1
    state.current_encounter_id = defn.encounter_id
    return _auto_number_choices(defn.builder(state))


def _no_encounters_encounter(state: GameState) -> Encounter:
    """Screen shown when the player has no encounters left this month; choice returns to kingdom."""
    from generators_kingdom import enter_kingdom
    return Encounter(
        title="No encounters remaining",
        description=(
            "You have no encounters remaining this month.\n\n"
            "Return to the kingdom and choose 'Advance month' to start a new month and receive three more encounters."
        ),
        choices=[choice("Return to the kingdom", lambda: enter_kingdom(state))],
    )


def generate_encounter(state: GameState) -> Encounter:
    """Legacy: pick a random encounter without 3-per-month or eligibility. Prefer get_next_encounter for normal flow."""
    eligible = _get_eligible_definitions(state)
    if not eligible:
        defn = WORLD_ENCOUNTER_DEFINITIONS[0]
    else:
        defn = random.choice(eligible)
    return defn.builder(state)


def next_area(state: GameState) -> None:
    """Move to next area and show next encounter, or 'no encounters remaining' and return to kingdom."""
    state.area_index += 1
    encounter = get_next_encounter(state)
    if encounter is not None:
        state.current_encounter = _auto_number_choices(encounter)
    else:
        state.current_encounter = _auto_number_choices(_no_encounters_encounter(state))


def set_encounter(state: GameState, title: str, description: str, choices: list[Choice]) -> None:
    encounter = Encounter(title=title, description=description, choices=choices)
    state.current_encounter = _auto_number_choices(encounter)


def end_encounter(state: GameState, log_text: str = "") -> None:
    if log_text:
        state.add_log(log_text)
    next_area(state)