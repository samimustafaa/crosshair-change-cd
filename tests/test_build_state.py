import unittest

from build_state import BUILD_KEYS, BuildTracker, displayed_reticle


class BuildTrackerTests(unittest.TestCase):
    def test_build_hotkeys_enter_circle_mode_from_shotgun_or_ar(self):
        for key in BUILD_KEYS:
            with self.subTest(key=key):
                tracker = BuildTracker()
                self.assertFalse(tracker.update(True))
                self.assertTrue(tracker.update(True, {key}))
                self.assertEqual(displayed_reticle("Shotgun", tracker.active), "Pickaxe")
                self.assertEqual(displayed_reticle("AR / Sniper", tracker.active), "Pickaxe")
                self.assertTrue(tracker.update(True))  # retains mode after releasing key

    def test_cancel_key_restores_previous_weapon_reticle(self):
        tracker = BuildTracker()
        tracker.update(True, {"F"})
        self.assertFalse(tracker.update(True, {"E"}))
        self.assertEqual(displayed_reticle("Shotgun", tracker.active), "Shotgun")
        tracker.update(True, {"C"})
        self.assertFalse(tracker.update(True, {"ESC"}))

    def test_weapon_slot_returns_to_weapon_mode(self):
        for slot in "12345":
            with self.subTest(slot=slot):
                tracker = BuildTracker()
                tracker.update(True, {"X"})
                self.assertFalse(tracker.update(True, {slot}))
                self.assertEqual(displayed_reticle("AR / Sniper", tracker.active), "AR / Sniper")

    def test_switching_build_type_keeps_circle_active(self):
        tracker = BuildTracker()
        tracker.update(True, {"F"})
        self.assertTrue(tracker.update(True, {"G"}))  # G is "Type", not cancel
        self.assertTrue(tracker.update(True, {"C"}))

    def test_cancel_wins_over_build_keys_when_pressed_together(self):
        tracker = BuildTracker()
        tracker.update(True, {"F"})
        self.assertFalse(tracker.update(True, {"E", "C"}))

    def test_unfocused_or_disabled_clears_mode(self):
        tracker = BuildTracker()
        tracker.update(True, {"F"})
        self.assertFalse(tracker.update(False))
        tracker.update(True, {"X"})
        self.assertFalse(tracker.update(True, enabled=False))


if __name__ == "__main__":
    unittest.main()
