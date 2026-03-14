"""
File for world encounters (3 per month)
"""


from models import GameState, Encounter, Choice, EventDefinition
from generators_npc import generate_npc
from event_runtime import EventContext
import random

# ----------------------------
# World event builders
# ----------------------------
def _get_traincar_state(state: GameState) -> dict:
    if "traincar_state" not in state.flags:
        state.flags["traincar_state"] = {
            "seer": generate_npc("human"),
            "seer_spoken": False,
            "seer_name_learned": False,
            "seer_help_taken": False,
        }
    return state.flags["traincar_state"]


def _clear_traincar_state(state: GameState) -> None:
    state.flags.pop("traincar_state", None)

def build_traincar(state: GameState, ctx: EventContext) -> Encounter:
    def finish_traincar(log_text: str = ""):
        _clear_traincar_state(state)
        ctx.finish(log_text)

    def train_leave():
        finish_traincar("You leave the traincar alone.")

    def train_enter():
        state.add_log("You step into the traincar. Dust billows up from the floor.")
        random.choice([train_depart, train_seer])()

    def train_depart():
        ctx.show(
            title="The Departure",
            description=(
                "Suddenly you feel the car shake. The soft whine of a motor reverberates "
                "through the darkness. Slivers of light through holes in the roof bring in "
                "the sound of a departure bell."
            ),
            choices=[Choice("", "Await your destination", train_leave)],
        )

    def train_seer():
        event_state = _get_traincar_state(state)
        seer = event_state["seer"]

        if event_state["seer_spoken"]:
            if event_state["seer_name_learned"]:
                desc = f"{seer.name} waits silently for your answer."
            else:
                desc = "The seer waits silently for your answer."
        else:
            desc = (
                "A small lantern lights a wooden table at the end of the car, "
                "illuminating the long white beard of an old man who beckons you over."
            )
            event_state["seer_spoken"] = True

        choices = [
            Choice("", "What is your name", seer_name),
            Choice("", "What are you doing on this train?", seer_train),
            Choice("", "What do you do?", seer_job),
            Choice("", "Can you tell the future?", seer_future),
        ]

        if not event_state["seer_help_taken"]:
            choices.append(Choice("", "Can you help me?", seer_help))

        choices.append(Choice("", "Leave the Seer", train_leave))
        ctx.show("The Seer", desc, choices)

    def seer_name():
        event_state = _get_traincar_state(state)
        seer = event_state["seer"]
        event_state["seer_name_learned"] = True
        ctx.show(
            title="The Seer",
            description=f"My friends call me {seer.name}.",
            choices=[Choice("", "Back", train_seer)],
        )

    def seer_train():
        ctx.show(
            title="The Seer",
            description=(
                "Long ago, this track used to connect Alderwyn to the ruined city of Kash. "
                "I used it regularly for sojourns to a school of magic deep in the forest near Kash. "
                "This was nearly a century ago, before I retired to be caretaker of these woods. "
                "I found it broken down and decided to use it as my residence during my final years."
            ),
            choices=[Choice("", "Back", train_seer)],
        )

    def seer_job():
        event_state = _get_traincar_state(state)
        seer = event_state["seer"]

        if seer.morality >= 3:
            desc = (
                "I walk along the rivers and crags deep in the forest. "
                "I feed the animals; I protect them from darkness."
            )
        else:
            desc = (
                "I walk along the rivers and crags deep in the forest. "
                "I try to spread the influence of the shadows; I chant spells "
                "to lead demons into the souls of the wildlife."
            )

        ctx.show(
            title="The Seer",
            description=desc,
            choices=[Choice("", "Back", train_seer)],
        )

    def seer_future():
        ctx.show(
            title="The Seer",
            description=(
                '"When I peer into the beyond, I see a foggy haze.\n\n'
                "Sometimes I can grasp onto something there, the contours of an object perhaps, "
                "but it always seems to slip away.\n\n"
                'It is a life of frustration, but occasional insight."'
            ),
            choices=[Choice("", "Back", train_seer)],
        )

    def seer_help():
        event_state = _get_traincar_state(state)
        event_state["seer_help_taken"] = True
        ctx.show(
            title="The Seer",
            description=(
                'The seer draws your attention to a deck of cards on the table. '
                '"I have infused these cards with magical insight. Someone ought to make use of them '
                'before I pass. I will let you pick one." He splays three cards in front of you.'
            ),
            choices=[
                Choice("", "The card with a snake wrapped around a sword", train_seer),
                Choice("", "The card with a bright, pulsating heart", train_seer),
                Choice("", "The card with a deer drinking at a stream", train_seer),
            ],
        )

    return Encounter(
        title="A Hidden Traincar",
        description=(
            "While walking through the wilds, you come to a clearing and spot an old train "
            "resting on rusty tracks. The final car on the train appears to be partially open, "
            "allowing you a way in if you so choose."
        ),
        choices=[
            Choice("", "Enter the car", train_enter),
            Choice("", "Avoid the car", train_leave),
        ],
    )


def build_golem(state: GameState, ctx: EventContext) -> Encounter:
    def only():
        state.add_log("You talk to the golem.")
        ctx.finish()

    return Encounter(
        title="A Golem",
        description="A golem stands in the wilds.",
        choices=[Choice("", "Talk to the golem", only)],
    )


# ----------------------------
# World event registry
# ----------------------------

TRAINCAR = EventDefinition(
    event_id="traincar",
    builder=build_traincar,
    category="world",
    repeatable=True,
    weight=1
)

GOLEM = EventDefinition(
    event_id="golem",
    builder=build_golem,
    category="world",
    repeatable=True,
    weight = 1
)

WORLD_EVENT_DEFINITIONS: list[EventDefinition] = [
    TRAINCAR,
    GOLEM,
]
