import unittest
from sg0hann_crosshair import draw_reticle

class FakeCanvas:
    def __init__(self):self.lines=[];self.arcs=[];self.ovals=[]
    def create_line(self,x1,y1,x2,y2,**kw):self.lines.append((x1,y1,x2,y2))
    def create_arc(self,*coords,**kw):self.arcs.append(coords)
    def create_oval(self,*coords,**kw):self.ovals.append(coords)

class VideoMeasuredGeometryTests(unittest.TestCase):
    def test_ar_marks_match_video_baseline_and_expanded(self):
        initial=FakeCanvas()
        draw_reticle(initial,100,100,"AR / Sniper","#44FF44",1,3,spread=1.0)
        # horizontal left bar: 100-33 to 100-20
        self.assertEqual(initial.lines[0],(67,100,80,100))
        self.assertEqual(initial.lines[1],(120,100,133,100))
        expanded=FakeCanvas()
        draw_reticle(expanded,100,100,"AR / Sniper","#44FF44",1,3,spread=1.95)
        self.assertEqual(expanded.lines[0],(48,100,61,100))
        self.assertEqual(expanded.lines[1],(139,100,152,100))

    def test_shotgun_idle_ring_radius_from_video(self):
        canvas=FakeCanvas()
        draw_reticle(canvas,100,100,"Shotgun","#55FFFF",1,3,spread=1.0)
        self.assertEqual(len(canvas.arcs),4)
        self.assertEqual(canvas.arcs[0],(66,66,134,134))

if __name__=="__main__":unittest.main()
