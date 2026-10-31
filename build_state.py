"""Infer temporary build mode from Creative Destruction's configured hotkeys.

This app never reads game memory or modifies files. It reacts only to keypresses
while the game is foreground; build mode is therefore an input-based estimate.
"""

BUILD_KEYS = frozenset({"F", "X", "C", "H", "F4"})
CANCEL_KEYS = frozenset({"E", "ESC"})
WEAPON_SLOT_KEYS = frozenset({"1", "2", "3", "4", "5"})


class BuildTracker:
    def __init__(self):
        self.active = False

    def reset(self):
        self.active = False

    def update(self, game_focused: bool, pressed_keys=(), enabled: bool = True) -> bool:
        if not game_focused or not enabled:
            self.reset()
            return False
        keys = set(pressed_keys)
        # Cancel or weapon selection must win if several keys land together.
        if keys & (CANCEL_KEYS | WEAPON_SLOT_KEYS):
            self.active = False
        elif keys & BUILD_KEYS:
            self.active = True
        return self.active


def displayed_reticle(weapon_mode: str, building: bool) -> str:
    """Build-preview crosshair uses pickaxe style without changing weapon slot."""
    return "Pickaxe" if building else weapon_mode
