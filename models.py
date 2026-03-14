# ----------------------------
# Data models
# ----------------------------
from dataclasses import dataclass, field
from typing import Callable, Literal


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
class EventDefinition:
    event_id: str
    builder: Callable[["GameState", "EventContext"], Encounter]
    category: Literal["kingdom", "world"]
    repeatable: bool = True
    retire_if: Callable[["GameState"], bool] | None = None
    available_if: Callable[["GameState"], bool] | None = None
    weight: int = 1

@dataclass
class PerkDefinition:
    perk_id: str
    name: str
    category: str   # "farming", "army", "laws"
    description: str
    cost_gold: int = 0
    available_if: Callable[["GameState"], bool] | None = None
    purchase_if: Callable[["GameState"], bool] | None = None
    on_purchase: Callable[["GameState"], None] | None = None


@dataclass
class NPC:
    name: str
    race: str
    charm: int
    warmth: int
    unpredictability: int
    morality: int


@dataclass
class VillagerStatus:
    kind: str
    target: str | None = None


@dataclass
class Villager:
    name: str
    race: str
    willpower: int
    extraversion: int
    luck: int
    conscientiousness: int
    status: list["VillagerStatus"] = field(default_factory=list)
    isanimal: bool = False

    def add_status(self, kind: str, target: str | None = None) -> None:
        self.status.append(VillagerStatus(kind=kind, target=target))

    def remove_status(self, kind: str, target: str | None = None) -> None:
        self.status = [s for s in self.status if not (s.kind == kind and s.target == target)]

    def has_status(self, kind: str) -> bool:
        return any(s.kind == kind for s in self.status)


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

@dataclass
class RelationshipModifier:
    source: str          # "policy", "event", "history", etc.
    description: str
    amount: int


@dataclass
class RaceRelationship:
    race_a: str
    race_b: str
    base_reputation: int
    modifiers: list[RelationshipModifier] = field(default_factory=list)

    @property
    def reputation(self) -> int:
        total = self.base_reputation + sum(m.amount for m in self.modifiers)
        return max(-500, min(500, total))

@dataclass
class WorldHistory:
    race_relationships: dict[tuple[str, str], RaceRelationship] = field(default_factory=dict)
    history_log: list[str] = field(default_factory=list)


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
    army_units: dict[str, int] = field(default_factory=lambda: {"Warriors": 10})
    gold: int = 1000
    advisor_candidates: list[NPC] = field(default_factory=list)


@dataclass
class GameState:
    area_index: int = 0
    current_encounter: Encounter | None = None
    log: list[str] = field(default_factory=list)
    flags: dict = field(default_factory=dict)
    current_npc: NPC | None = None
    kingdom: Kingdom = field(default_factory=Kingdom)
    world_history: WorldHistory = field(default_factory=WorldHistory)
    

    # kingdom monthly event system
    events_remaining_this_month: int = 3
    occurred_kingdom_event_ids: set[str] = field(default_factory=set)

    # world monthly encounter system
    encounters_remaining_this_month: int = 3
    occurred_encounter_ids: set[str] = field(default_factory=set)

    # monthly summary
    last_month_summary: list[str] = field(default_factory=list)

    def add_log(self, text: str) -> None:
        self.log.append(text)