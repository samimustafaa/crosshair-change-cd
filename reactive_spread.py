"""Low-latency, input-driven approximation of crosshair expansion.

Uses ordinary held mouse/keyboard states only. Does not inspect game memory,
read anticheat state or claim the exact native spread value.

Time-step based for stable behavior at different frame rates.
"""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class SpreadTuning:
    spray_percent: int = 85
    jump_percent: int = 55
    recovery_ms: int = 320


class ReactiveSpread:
    def __init__(self):
        self.fire_amount = 0.0
        self.jump_amount = 0.0
        self.jump_hold_left = 0.0
        self.previous_firing = False
        self.previous_jumping = False

    def reset(self):
        self.fire_amount = 0.0
        self.jump_amount = 0.0
        self.jump_hold_left = 0.0
        self.previous_firing = False
        self.previous_jumping = False

    def update(self, dt: float, *, focused: bool, mode: str,
               firing: bool, jumping: bool, building: bool, aiming: bool,
               enabled: bool, tuning: SpreadTuning) -> float:
        """Return size multiplier (>=1.0); only active for gun reticles.

        Fire: quick impulse + progressive increase while LMB is down.
        Jump: impulse for one jump, held briefly, then settles.
        """
        if not (focused and enabled and mode in ("Shotgun", "AR / Sniper")) or building or aiming:
            self.reset()
            return 1.0

        # Clamp dt: avoids large jumps after a paused or delayed UI frame.
        dt = max(0.0, min(float(dt), 0.12))
        tuning = SpreadTuning(
            spray_percent=max(0, min(180, int(tuning.spray_percent))),
            jump_percent=max(0, min(140, int(tuning.jump_percent))),
            recovery_ms=max(100, min(1500, int(tuning.recovery_ms)))
        )
        recovery_seconds = tuning.recovery_ms / 1000.0

        if firing:
            if not self.previous_firing:
                self.fire_amount = max(self.fire_amount, .14)
            # Continuous firing increases spread in around 0.24 seconds.
            self.fire_amount = min(1.0, self.fire_amount + dt / .24)
        else:
            self.fire_amount = max(0.0, self.fire_amount - dt / recovery_seconds)

        if jumping and not self.previous_jumping:
            self.jump_amount = 1.0
            # Hold expansion during the first part of a typical jump.
            self.jump_hold_left = .38
        if self.jump_hold_left > 0:
            self.jump_hold_left = max(0.0, self.jump_hold_left - dt)
        elif not jumping:
            self.jump_amount = max(0.0, self.jump_amount - dt / max(.3, recovery_seconds))
        # While Space is held, decay is paused; no repeated jump impulses.
        self.previous_firing = bool(firing)
        self.previous_jumping = bool(jumping)

        # Max 3.7x in extreme combinations; default peak ~2.4x.
        return 1.0 + self.fire_amount * tuning.spray_percent/100.0 + self.jump_amount * tuning.jump_percent/100.0
