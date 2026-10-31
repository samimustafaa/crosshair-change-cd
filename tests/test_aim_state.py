import unittest

from aim_state import AimTracker, crosshair_visible


class AimTrackerTests(unittest.TestCase):
    def test_hold_aim_hides_only_while_right_mouse_pressed(self):
        tracker = AimTracker()
        self.assertFalse(tracker.update(True, False, "Hold"))
        self.assertTrue(tracker.update(True, True, "Hold"))
        self.assertTrue(tracker.update(True, True, "Hold"))
        self.assertFalse(tracker.update(True, False, "Hold"))

    def test_toggle_aim_uses_each_right_mouse_click(self):
        tracker = AimTracker()
        self.assertFalse(tracker.update(True, False, "Toggle"))
        self.assertTrue(tracker.update(True, True, "Toggle"))
        self.assertTrue(tracker.update(True, False, "Toggle"))
        self.assertFalse(tracker.update(True, True, "Toggle"))
        self.assertFalse(tracker.update(True, False, "Toggle"))

    def test_focus_loss_ends_aim_and_discards_input(self):
        tracker = AimTracker()
        tracker.update(True, True, "Toggle")
        self.assertFalse(tracker.update(False, True, "Toggle"))
        self.assertFalse(tracker.update(True, False, "Toggle"))

    def test_mode_change_reinitializes_aim_state(self):
        tracker = AimTracker()
        tracker.update(True, True, "Hold")
        self.assertFalse(tracker.update(True, False, "Toggle"))

    def test_render_rules(self):
        self.assertTrue(crosshair_visible(True, True, True, True, False))
        self.assertFalse(crosshair_visible(True, True, True, True, True))
        self.assertTrue(crosshair_visible(True, True, True, False, True))
        self.assertFalse(crosshair_visible(True, False, True, True, False))
        self.assertTrue(crosshair_visible(True, False, False, True, False))
        self.assertFalse(crosshair_visible(False, True, False, False, False))


if __name__ == "__main__":
    unittest.main()
