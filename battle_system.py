from dataclasses import dataclass
from models import Kingdom

from dataclasses import dataclass
from models import Kingdom


@dataclass
class UnitDefinition:
    unit_type: str
    hp: int
    attack_dice: list[int]   # e.g. [6] or [6, 6] or [10]
    priority: int


@dataclass
class Combatant:
    combatant_id: int
    side: str
    unit_type: str
    current_hp: int
    max_hp: int
    attack_dice: list[int]
    priority: int


UNIT_DEFINITIONS: dict[str, UnitDefinition] = {
    "Warriors": UnitDefinition(
        unit_type="Warriors",
        hp=10,
        attack_dice=[6],
        priority=1,
    ),
    "Goblin Warriors": UnitDefinition(
        unit_type="Goblin Warriors",
        hp=10,
        attack_dice=[2],
        priority=1,
    ),
    "Goblin Archers": UnitDefinition(
        unit_type="Goblin Archers",
        hp=10,
        attack_dice=[2],
        priority=2,
    ),
}


def build_combatants(unit_counts: dict[str, int], side: str) -> list[Combatant]:
    combatants: list[Combatant] = []
    next_id = 1

    for unit_type, count in unit_counts.items():
        if unit_type not in UNIT_DEFINITIONS:
            raise KeyError(f"Unknown unit type: {unit_type}")

        definition = UNIT_DEFINITIONS[unit_type]

        for _ in range(count):
            combatants.append(
                Combatant(
                    combatant_id=next_id,
                    side=side,
                    unit_type=definition.unit_type,
                    current_hp=definition.hp,
                    max_hp=definition.hp,
                    attack_dice=definition.attack_dice[:],
                    priority=definition.priority,
                )
            )
            next_id += 1

    return combatants


def build_combatants_from_kingdom(kingdom: Kingdom, side: str = "allies") -> list[Combatant]:
    return build_combatants(kingdom.army_units, side)

import random
from collections import Counter


def roll_damage(attack_dice: list[int]) -> int:
    return sum(random.randint(1, sides) for sides in attack_dice)


def alive_combatants(combatants: list[Combatant]) -> list[Combatant]:
    return [c for c in combatants if c.current_hp > 0]


def count_survivors_by_type(combatants: list[Combatant]) -> dict[str, int]:
    alive = alive_combatants(combatants)
    counter = Counter(c.unit_type for c in alive)
    return dict(counter)


def resolve_battle(
    allied_unit_counts: dict[str, int],
    enemy_unit_counts: dict[str, int],
) -> dict:
    allies = build_combatants(allied_unit_counts, side="allies")
    enemies = build_combatants(enemy_unit_counts, side="enemies")

    battle_log: list[str] = []
    round_num = 1

    while alive_combatants(allies) and alive_combatants(enemies):
        battle_log.append(f"--- Round {round_num} ---")

        turn_order = alive_combatants(allies) + alive_combatants(enemies)

        # Group by priority, highest first
        priorities = sorted({c.priority for c in turn_order}, reverse=True)
        ordered_combatants: list[Combatant] = []

        for prio in priorities:
            group = [c for c in turn_order if c.priority == prio]
            random.shuffle(group)
            ordered_combatants.extend(group)

        for attacker in ordered_combatants:
            if attacker.current_hp <= 0:
                continue

            if attacker.side == "allies":
                targets = alive_combatants(enemies)
            else:
                targets = alive_combatants(allies)

            if not targets:
                break

            target = random.choice(targets)
            damage = roll_damage(attacker.attack_dice)
            target.current_hp -= damage

            battle_log.append(
                f"{attacker.unit_type} ({attacker.side}) hits "
                f"{target.unit_type} ({target.side}) for {damage} damage."
            )

            if target.current_hp <= 0:
                battle_log.append(
                    f"{target.unit_type} ({target.side}) is slain."
                )
            else:
                battle_log.append(
                    f"{target.unit_type} ({target.side}) has {target.current_hp}/{target.max_hp} HP left."
                )

        round_num += 1

    allied_survivors = count_survivors_by_type(allies)
    enemy_survivors = count_survivors_by_type(enemies)

    if alive_combatants(allies):
        winner = "allies"
    else:
        winner = "enemies"

    battle_log.append(f"Battle ended. Winner: {winner}.")

    return {
        "winner": winner,
        "rounds": round_num - 1,
        "log": battle_log,
        "allied_survivors": allied_survivors,
        "enemy_survivors": enemy_survivors,
    }


result = resolve_battle(
    allied_unit_counts={"Warriors": 10},
    enemy_unit_counts={"Goblin Warriors": 10, "Goblin Archers": 10},
)

for line in result["log"]:
    print(line)

print("Allied survivors:", result["allied_survivors"])
print("Enemy survivors:", result["enemy_survivors"])