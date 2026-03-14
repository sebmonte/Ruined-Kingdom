from models import PerkDefinition

PERK_DEFINITIONS = [
    PerkDefinition(
        perk_id="irrigation",
        name="Irrigation",
        category="farming",
        description="Increase food production from crops.",
        cost_gold=20,
    ),
    PerkDefinition(
        perk_id="granary",
        name="Granary",
        category="farming",
        description="Reduces food loss and improves storage.",
        cost_gold=15,
    ),
    PerkDefinition(
        perk_id="conscription",
        name="Conscription",
        category="army",
        description="Allows rapid levy of troops.",
        cost_gold=25,
    ),
    PerkDefinition(
        perk_id="animal_husbandry",
        name="Animal Husbandry",
        category="farming",
        description="Allows the raising of animals.",
        cost_gold=10,
    ),
    PerkDefinition(
        perk_id="psychologist",
        name="Psychologist",
        category="experts",
        description="Studies the mentality of your villagers, and has a chance to randomly increase one of their attributes every year. Also unlocks unique psychology-themed events and technologies",
        cost_gold=10,
    ),
]