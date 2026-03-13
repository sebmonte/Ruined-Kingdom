"""Monthly advance logic: apply crop/villager effects and build summary for the report screen."""
from models import GameState
from crops import apply_crop_effects
from villager_effects import apply_villager_effects


def advance_month(state: GameState) -> None:
    """Apply monthly effects and build a summary for the monthly report screen."""
    state.last_month_summary = []
    apply_crop_effects(state)
    apply_villager_effects(state)
    state.add_log("A month passes in Ashvale.")
    state.last_month_summary.append("A month passed in Ashvale.")
