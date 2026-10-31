import math
import unittest
import numpy as np

from vision_assist import estimate_native_radius, VisionBaseline, MIN_CONFIDENCE


class VisionTests(unittest.TestCase):
    @staticmethod
    def draw(mode, radius):
        img=np.zeros((220,220,3),dtype=np.uint8)
        cx=cy=109.5
        if mode=="Shotgun":
            for angle in (0,12,-12,90,78,102,180,168,192,270,258,282):
                a=math.radians(angle)
                x,y=round(cx+radius*math.cos(a)),round(cy+radius*math.sin(a))
                img[y-2:y+3,x-2:x+3]=245
        else:
            for d in range(19,32):
                for x,y in ((cx+d,cy),(cx-d,cy),(cx,cy+d),(cx,cy-d)):
                    px,py=round(x),round(y)
                    img[py-2:py+3,px-2:px+3]=242
        return img

    def test_shotgun_ring_candidates(self):
        result=estimate_native_radius(self.draw("Shotgun",35),"Shotgun")
        self.assertIsNotNone(result)
        r,conf=result
        self.assertTrue(30 <= r <= 42,(r,conf))
        self.assertGreaterEqual(conf, MIN_CONFIDENCE)

    def test_ar_lines_candidates(self):
        result=estimate_native_radius(self.draw("AR / Sniper",24),"AR / Sniper")
        self.assertIsNotNone(result)
        r,conf=result
        self.assertGreaterEqual(conf,MIN_CONFIDENCE)
        self.assertTrue(14 <= r <= 37,(r,conf))

    def test_plain_bright_scenery_does_not_trigger(self):
        self.assertIsNone(estimate_native_radius(
            np.full((220,220,3),235,dtype=np.uint8),"Shotgun"))
        self.assertIsNone(estimate_native_radius(
            np.full((220,220,3),235,dtype=np.uint8),"AR / Sniper"))

    def test_baseline_waits_for_six_idle_samples(self):
        cal=VisionBaseline()
        for i in range(5):
            self.assertIsNone(cal.observe("Shotgun",35,0.92,True))
        self.assertAlmostEqual(cal.observe("Shotgun",35,0.92,True),1.0)
        self.assertAlmostEqual(cal.observe("Shotgun",43,0.92,False),43/35)
        self.assertIsNone(cal.observe("Shotgun",400,0.92,False))
        self.assertIsNone(cal.observe("Shotgun",35,0.10,False))
        cal.clear()
        self.assertIsNone(cal.observe("Shotgun",35,0.92,False))


if __name__=="__main__":
    unittest.main()
