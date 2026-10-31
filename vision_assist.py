"""Optional high-confidence screen-center reticle shape estimation.

Only small center crop; no game files, memory reads or injection.
A detected white shape is not guaranteed to be the native HUD, so every
estimate is confidence-gated and the input-based model remains a fallback.
"""
from __future__ import annotations

import math
import statistics
import threading
import time
from collections import deque

import numpy as np

MIN_CONFIDENCE = 0.77


def _sample_white(rgb: np.ndarray, x: float, y: float, thickness: int = 2) -> float:
    h, w, _ = rgb.shape
    x, y = int(round(x)), int(round(y))
    if x < thickness or y < thickness or x + thickness >= w or y + thickness >= h:
        return 0.0
    block = rgb[y-thickness:y+thickness+1, x-thickness:x+thickness+1]
    hi = block.max(axis=2).astype(np.int16)
    lo = block.min(axis=2).astype(np.int16)
    bright = (lo > 187) & (hi-lo < 38)
    return float(np.mean(bright))


def _ring_score(rgb: np.ndarray, r: float, center: tuple[float,float]) -> float:
    cx,cy = center
    # Cardinal-quarter arcs (the shotgun's four-part circle).
    points=[]
    for deg in (0, 12, -12, 90, 78, 102, 180,168,192,270,258,282):
        rad=math.radians(deg)
        x,y=cx+math.cos(rad)*r,cy+math.sin(rad)*r
        on = _sample_white(rgb,x,y)
        off = max(_sample_white(rgb,x+math.cos(rad)*8,y+math.sin(rad)*8),
                  _sample_white(rgb,x-math.cos(rad)*8,y-math.sin(rad)*8))
        points.append(max(0.0,on-.65*off))
    # Require evidence across multiple arcs; no single bright area should win.
    groups=[sum(points[i:i+3])/3 for i in range(0,12,3)]
    if sum(v>.35 for v in groups)<3:
        return 0.0
    return min(1.0,sum(groups)/4/.70)


def _cross_score(rgb: np.ndarray, r: float, center: tuple[float,float]) -> float:
    cx,cy=center
    group=[]
    for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
        along=[_sample_white(rgb,cx+dx*(r+t),cy+dy*(r+t),1)
               for t in (-2,0,2,4)]
        lateral=[_sample_white(rgb,cx+dx*(r+t)+dy*7,
                               cy+dy*(r+t)+dx*7,1)
                 for t in (-2,0,2,4)]
        group.append(max(0.0,sum(along)/4 - .6*sum(lateral)/4))
    if sum(v>.32 for v in group)<3:
        return 0.0
    return min(1.0,sum(group)/4/.65)


def estimate_native_radius(rgb: np.ndarray, mode: str) -> tuple[float, float] | None:
    """Returns (radius, confidence), only for strongly symmetric white HUD shapes.

    Args: RGB center crop 180-300px square, ideally overlay colored (not white).
    """
    if rgb.ndim!=3 or rgb.shape[2]<3 or min(rgb.shape[:2])<100:
        return None
    cx,cy=(rgb.shape[1]-1)/2,(rgb.shape[0]-1)/2
    scorer = _ring_score if mode=="Shotgun" else _cross_score
    candidates=[]
    for r in range(13, min(rgb.shape[:2])//2 - 12):
        score=scorer(rgb,r,(cx,cy))
        if score>=MIN_CONFIDENCE:
            candidates.append((r,score))
    if not candidates:
        return None
    # Favor complete strong symmetrical grouping over peripheral bright scenery.
    radius,confidence=max(candidates,key=lambda p:(p[1], -abs(p[0]-35)*.0002))
    if confidence < MIN_CONFIDENCE:
        return None
    return float(radius), float(confidence)


class VisionBaseline:
    """Learning idle reticle radius only when stable, gun exposed, no ADS."""
    def __init__(self):
        self.reference: dict[str,float]={}
        self.idle_samples: dict[str,deque]={}

    def clear(self):
        self.reference.clear()
        self.idle_samples.clear()

    def observe(self, mode: str, radius: float, confidence: float,
                idle: bool) -> float | None:
        if confidence < MIN_CONFIDENCE:
            return None
        if idle:
            samples=self.idle_samples.setdefault(mode,deque(maxlen=24))
            samples.append(radius)
            if len(samples)>=6:
                base=float(statistics.median(samples))
                # The measured idle reticle should not jump wildly in size.
                if mode not in self.reference:
                    self.reference[mode]=base
                elif abs(base-self.reference[mode])<self.reference[mode]*.14:
                    self.reference[mode]=self.reference[mode]*.98+base*.02
        base=self.reference.get(mode)
        if not base:
            return None
        multiplier=radius/base
        return multiplier if .62<=multiplier<=2.8 else None


class VisionAssist:
    """Capture thread. Tkinter polls a thread-safe snapshot, never captures on UI thread."""
    def __init__(self, area=220):
        self.area=area
        self._lock=threading.Lock()
        self._state=(False,"",True,False) # focused, mode, idle, allowed
        self._result=None
        self._stop=threading.Event()
        self.baseline=VisionBaseline()
        self._worker=None
        self._last_mode=None

    def start(self):
        if self._worker is not None:
            return
        self._worker=threading.Thread(target=self._run,daemon=True,name="reticle-vision")
        self._worker.start()

    def stop(self):
        self._stop.set()

    def set_state(self,*,focused:bool,mode:str,idle:bool,allowed:bool):
        with self._lock:
            self._state=(focused,mode,idle,allowed)
            if not focused or not allowed:
                self._result=None

    def latest(self):
        with self._lock:
            return self._result

    def reset(self):
        with self._lock:
            self.baseline.clear()
            self._result=None

    def _run(self):
        try:
            import mss
        except Exception:
            return
        try:
            with mss.mss() as cap:
                while not self._stop.is_set():
                    with self._lock:
                        focused,mode,idle,allowed=self._state
                    if not (focused and allowed and mode in ("Shotgun","AR / Sniper")):
                        self._stop.wait(.12)
                        continue
                    if self._last_mode != mode:
                        self._last_mode=mode
                        with self._lock:
                            self._result=None
                    monitor=cap.monitors[1]
                    x=monitor["left"]+monitor["width"]//2-self.area//2
                    y=monitor["top"]+monitor["height"]//2-self.area//2
                    box={"left":x,"top":y,"width":self.area,"height":self.area}
                    screen=np.asarray(cap.grab(box))
                    # mss returns BGRA.
                    rgb=screen[:,:,:3][:,:,::-1]
                    found=estimate_native_radius(rgb,mode)
                    if found:
                        radius,confidence=found
                        with self._lock:
                            multiplier=self.baseline.observe(mode,radius,confidence,idle)
                            self._result=(time.monotonic(),mode,multiplier,confidence)
                    else:
                        with self._lock:
                            self._result=None
                    self._stop.wait(.030) # ~30 FPS aim, bounded CPU usage.
        except Exception:
            with self._lock:
                self._result=None
