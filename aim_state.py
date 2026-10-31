"""ADS (aim-down-sights) input tracking, independent of Windows/Tkinter.

The game can use hold-to-aim or toggle-to-aim. This tracks the player's
chosen control scheme, rather than claiming to inspect the game's scope.
"""


class AimTracker:
    def __init__(self):
        self.aiming = False
        self._previous_pressed = False
        self._previous_mode = None

    def reset(self):
        self.aiming = False
        self._previous_pressed = False

    def update(self, game_focused: bool, right_pressed: bool, input_mode: str = "Hold") -> bool:
        if not game_focused:
            self.reset()
            return False
        if input_mode != self._previous_mode:
            self.reset()
            self._previous_mode = input_mode
        if input_mode == "Toggle":
            if right_pressed and not self._previous_pressed:
                self.aiming = not self.aiming
        else:
            self.aiming = bool(right_pressed)
        self._previous_pressed = bool(right_pressed)
        return self.aiming


def crosshair_visible(enabled: bool, game_focused: bool,
                      only_in_game: bool, hide_while_aiming: bool,
                      aiming: bool) -> bool:
    """Only suppress overlays for aim input while the game is focused."""
    return (bool(enabled)
            and (bool(game_focused) or not bool(only_in_game))
            and not (bool(game_focused) and bool(hide_while_aiming) and bool(aiming)))
