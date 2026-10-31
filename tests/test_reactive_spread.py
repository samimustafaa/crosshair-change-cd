import unittest
from reactive_spread import ReactiveSpread, SpreadTuning

class SpreadTests(unittest.TestCase):
    def setUp(self):
        self.s = ReactiveSpread()
        self.opt = SpreadTuning()

    def tick(self, dt=0.016, **params):
        defaults=dict(focused=True, mode="AR / Sniper", firing=False,
                      jumping=False, building=False, aiming=False,
                      enabled=True, tuning=self.opt)
        defaults.update(params)
        return self.s.update(dt, **defaults)

    def test_shooting_expands_on_first_press(self):
        first=self.tick(firing=True)
        self.assertGreater(first, 1.05)
        for _ in range(18): last=self.tick(firing=True)
        self.assertGreater(last, first)
        self.assertLessEqual(last, 1.86)

    def test_release_recovers_smoothly(self):
        for _ in range(24): self.tick(firing=True)
        last=self.tick()
        self.assertGreater(last, 1)
        for _ in range(25): last=self.tick()
        self.assertAlmostEqual(last, 1.0, places=3)

    def test_jump_instant_then_returns(self):
        self.assertGreater(self.tick(jumping=True),1.4)
        for _ in range(23): val=self.tick()
        self.assertGreater(val,1.1)
        for _ in range(26): val=self.tick()
        self.assertAlmostEqual(val,1.0,places=3)

    def test_both_inputs_stack(self):
        self.assertGreater(self.tick(firing=True,jumping=True),1.5)

    def test_aim_build_and_pickaxe_do_not_expand(self):
        for toggles in (dict(mode="Pickaxe",firing=True),
                        dict(building=True,firing=True),
                        dict(aiming=True,firing=True),
                        dict(focused=False,firing=True),
                        dict(enabled=False,firing=True)):
            with self.subTest(toggles=toggles):
                self.s.reset()
                self.assertEqual(self.tick(**toggles),1.0)

    def test_release_focus_resets_state(self):
        self.tick(firing=True,jumping=True)
        self.assertEqual(self.tick(focused=False),1.0)
        self.assertEqual(self.tick(),1.0)

    def test_frame_time_independence(self):
        values=[]
        for dt,frames in ((.008,30),(.016,15),(.03,8)):
            local=ReactiveSpread()
            for _ in range(frames):
                result=local.update(dt,focused=True,mode="AR / Sniper",
                                    firing=True,jumping=False,building=False,
                                    aiming=False,enabled=True,tuning=self.opt)
            values.append(result)
        self.assertLess(max(values)-min(values),.02)

    def test_limits_user_tuning(self):
        n=SpreadTuning(spray_percent=999,jump_percent=999,recovery_ms=-5)
        for _ in range(20): value=self.tick(firing=True,jumping=True,tuning=n)
        self.assertLessEqual(value,4.3)

if __name__=="__main__":
    unittest.main()
