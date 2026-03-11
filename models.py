
# ----------------------------
# Data models
# ----------------------------
from dataclasses import dataclass, field
from typing import Callable

@dataclass
class Player:
    hp: int = 10
    gold: int = 0
    food: int = 5
    level: int = 1


@dataclass
class Choice:
    key: str
    text: str
    effect: callable


@dataclass
class Encounter:
    title: str
    description: str
    choices: list[Choice]

@dataclass
class NPC:
    name: str
    race: str
    charm: int
    warmth: int
    unpredictability: int
    morality: int

@dataclass
class EventOption:
    text: str
    effect: Callable
    condition: Callable | None = None

@dataclass
class KingdomEvent:
    event_id: str
    title: str
    description: str
    options: list[EventOption]

from dataclasses import dataclass, field

@dataclass
class Kingdom:
    name: str = "Ashvale"
    crops: dict[str, int] = field(default_factory=lambda: {"Gloom_Corn": 10})
    total_food: int = 20
    advisor: NPC | None = None
    happiness: int = 50
    fear: int = 10
    population: int = 100
    loyalty: int = 50
    perks: list[str] = field(default_factory=list)
    army_units: dict[str, int] = field(default_factory=lambda: {"Soldiers": 20})
    advisor_candidates: list[NPC] = field(default_factory=list)

@dataclass
class GameState:
    player: Player = field(default_factory=Player)
    area_index: int = 0
    current_biome: str = "Forest"
    current_encounter: Encounter | None = None
    log: list[str] = field(default_factory=list)
    flags: dict = field(default_factory=dict)
    current_npc: NPC | None = None
    kingdom: Kingdom = field(default_factory=Kingdom)
    kingdom_event_queue: list = field(default_factory=list)
    current_kingdom_event_index: int = 0

    def add_log(self, text: str) -> None:
        self.log.append(text)

@dataclass
class Crop:
    name: str
    description: str
    farmability: float = 1.0
    edible: bool = True
    food_value: int = 1
    monthly_effect: Callable | None = None
    on_stock_change: Callable | None = None
    tags: list[str] = field(default_factory=list)


