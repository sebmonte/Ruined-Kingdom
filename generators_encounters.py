import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass, field
import random
from models import GameState, Encounter, Choice, Player, NPC
import json
import random
from content_loader import ENCOUNTERS
from generators_npc import generate_npc

# ----------------------------
# Procedural generation
# ----------------------------

BIOMES = ["Forest", "Ruins"]
ENCOUNTER_TYPES = ["Enemy", 'Traveler']



def generate_biome(area_index: int) -> str:
    # Mild progression: later areas are a bit harsher
    if area_index < 2:
        pool = ["Forest", "Ruins"]
    elif area_index < 5:
        pool = ["Forest", "Ruins"]
    else:
        pool = BIOMES
    return random.choice(pool)


def generate_encounter(state: GameState) -> Encounter:
    biome = state.current_biome
    e_type = random.choice(ENCOUNTERS["encounters"])

    if e_type == "traincar":

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
                choices=[Choice("1", "Await your destination", train_leave)],
        )        
        def train_seer():

            state.add_log("test2")
            if state.current_npc is None:
                state.current_npc = generate_npc("human")


            seer = state.current_npc
            print(seer)
            print(seer.name)
            print(seer.morality)

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
                Choice("1", "What is your name", seer_name),
                Choice("2", "What are you doing on this train?", seer_train),
                Choice("3", "What do you do?", seer_job),
                Choice("4", "Can you tell the future?", seer_future),
            ]

            if not state.flags.get("seer_help_taken", False):
                choices.append(Choice("5", "Can you help me?", seer_help))


            choices.append(Choice("6", "Leave the Seer", train_leave))

            set_encounter(
                state,
                title="The Seer",
                description=desc,
                choices=choices,
            )
        def seer_future():
            set_encounter(
                state,
                title="The Seer",
                description=(
            '"When I peer into the beyond, I see a foggy haze.\n\n'
            'Sometimes I can grasp onto something there, the contours of an object perhaps, but it always seems to slip away.\n\n'
            'It is a life of frustration, but occasional insight."'
            ),
                choices=[
            Choice("1", "Back", train_seer)
                ],
        )
        def seer_name():
            seer = state.current_npc
            state.flags["seer_name_learned"] = True
            set_encounter(
                state,
                title="The Seer",
                description=(f"My friends call me {seer.name}."
            ),
                choices=[
            Choice("1", "Back", train_seer)
                ],
        )
        def seer_train():
            set_encounter(
                state,
                title="The Seer",
                description=(
            'Long ago, this track used to connect *Alderwyn* to the ruined city of *Kash*. I used it regularly for sojourns to a school of magic deep in the forest near *Kash*. This was nearly a century ago, before I retired to be caretaker of these woods. I found it broken down and decided to use it as my residence during my final years.'
            ), 
                choices=[
            Choice("1", "Back", train_seer)
                ],
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
                description=(
            seer_job_desc
            ),
                choices=[
            Choice("1", "Back", train_seer)
                ],
        )
        def seer_help():
            state.flags["seer_help_taken"] = True

            set_encounter(
                state,
                title="The Seer",
                description=('The seer draws your attention to a deck of cards on the table. "I have infused these cards with magical insight. Someone ought to make use of them before I pass. I will let you pick one." He splays three cards in front of you.'),
                choices=[Choice("1", "The card a snake wrapped around a sword", train_seer), 
                         Choice("2", 'The card with a bright, pulsating heart', train_seer),
                         Choice("3", 'The card a deer drinking at a stream', train_seer)],
            )
        return Encounter(
            title="A Hidden Traincar",
            description=(
                f"While walking through the {biome.lower()}, you come to a clearing and spot "
                "an old train resting on rusty tracks. The final car on the train appears to be partially open, "
                "allowing you a way in if you so choose."
            ),
            choices=[
                Choice("1", "Enter the car", train_enter),
                Choice("2", "Avoid the car", train_leave),
            ],
        )

    if e_type == "golem":

        def only():
            state.add_log("You talk to the golem")
            next_area(state)

        return Encounter(
            title="A golem",
            description=f"Golem stands {biome.lower()}.",
            choices=[
                Choice("1", "Talk to the golem", only),
            ],
        )

def next_area(state: GameState) -> None:
    state.area_index += 1

    # passive travel cost
    if state.player.food > 0:
        state.player.food -= 1
        state.add_log("You consume 1 food while traveling.")
    else:
        state.player.hp -= 1
        state.add_log("You have no food and lose 1 HP from exhaustion.")

    state.current_biome = generate_biome(state.area_index)
    state.current_encounter = generate_encounter(state)
def set_encounter(state: GameState, title: str, description: str, choices: list[Choice]) -> None:
    state.current_encounter = Encounter(
        title=title,
        description=description,
        choices=choices,
    )

def end_encounter(state: GameState, log_text: str = "") -> None:
    if log_text:
        state.add_log(log_text)
    next_area(state)