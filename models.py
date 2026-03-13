
# ----------------------------
# Data models
# ----------------------------
from dataclasses import dataclass, field
from typing import Callable

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

@dataclass # VillagerStatus is a status effect that can be applied to a villager.
class VillagerStatus:
    kind: str  # e.g. "addicted", "sick", "blessed"
    target: str | None = None  # e.g. crop_id for addiction

@dataclass # Villager is a villager in the kingdom.
class Villager:
    name: str
    race: str
    willpower: int
    extraversion: int
    luck: int
    conscientiousness: int
    status: list["VillagerStatus"] = field(default_factory=list) # A list of status effects that applied to the villager.
    isanimal: bool = False
    """True for dog, ape, etc.; used to treat villagers as animals where relevant."""

    def add_status(self, kind: str, target: str | None = None) -> None: # Add a status effect to the villager.
        self.status.append(VillagerStatus(kind=kind, target=target))

    def remove_status(self, kind: str, target: str | None = None) -> None: # Remove a status effect from the villager.
        self.status = [s for s in self.status if not (s.kind == kind and s.target == target)]

    def has_status(self, kind: str) -> bool: # Check if the villager has a specific status effect.
        return any(s.kind == kind for s in self.status)



@dataclass # EventOption is an option for a kingdom event.
class EventOption:
    text: str
    effect: Callable
    condition: Callable | None = None # A condition that must be met for the option to be available.

@dataclass # KingdomEvent is an event that can occur in the kingdom.
class KingdomEvent:
    event_id: str
    title: str
    description: str
    options: list[EventOption]
    repeatable: bool = True # If False, this event will not appear again after it has occurred once.
    """If False, this event will not appear again after it has occurred once."""
    retire_if: Callable[["GameState"], bool] | None = None # If set, when this returns True the event is excluded from the pool (e.g. make repeatable event stop appearing when a condition is met).
    """If set, when this returns True the event is excluded from the pool (e.g. make repeatable event stop appearing when a condition is met)."""
    available_if: Callable[["GameState"], bool] | None = None # If set, the event is only eligible for the pool when this returns True (e.g. only show when a villager is addicted).
    """If set, the event is only eligible for the pool when this returns True (e.g. only show when a villager is addicted)."""


@dataclass # Crop is a crop that can be grown in the kingdom.
class Crop:
    name: str
    description: str
    farmability: float = 1.0
    edible: bool = True
    food_value: int = 1
    monthly_effect: Callable | None = None # A function that is called every month to apply any effects to the crop.
    on_stock_change: Callable | None = None # A function that is called when the crop's stock changes.
    tags: list[str] = field(default_factory=list) 

@dataclass
class Kingdom:
    name: str = "Ashvale"
    crops: dict[str, int] = field(default_factory=lambda: {"Gloom_Corn": 10})
    total_food: int = 20
    advisor: NPC | None = None
    happiness: int = 50
    fear: int = 10
    population: list[Villager] = field(default_factory=list)
    loyalty: int = 50
    perks: list[str] = field(default_factory=list)
    army_units: dict[str, int] = field(default_factory=lambda: {"Soldiers": 10})
    advisor_candidates: list[NPC] = field(default_factory=list)

@dataclass
class GameState:
    area_index: int = 0
    current_biome: str = "Forest"
    current_encounter: Encounter | None = None
    log: list[str] = field(default_factory=list)
    flags: dict = field(default_factory=dict)
    current_npc: NPC | None = None
    kingdom: Kingdom = field(default_factory=Kingdom)
    kingdom_event_queue: list = field(default_factory=list)
    current_kingdom_event_index: int = 0
    events_remaining_this_month: int = 3
    last_month_summary: list[str] = field(default_factory=list)
    occurred_kingdom_event_ids: set[str] = field(default_factory=set)
    """Event IDs of non-repeatable kingdom events that have already occurred."""
    def add_log(self, text: str) -> None:
        self.log.append(text)



