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


def _sample_luma(gray: np.ndarray, x: float, y: float) -> float:
    x, y = int(round(x)), int(round(y))
    h, w = gray.shape
    if x < 2 or y < 2 or x + 2 >= w or y + 2 >= h:
        return 0.0
    return float(gray[y-1:y+2, x-1:x+2].mean())


def _neutral_white(rgb: np.ndarray, x: float, y: float) -> bool:
    """Reject colored overlays/muzzle flashes; inspect only whitish HUD marks."""
    x, y = int(round(x)), int(round(y))
    if x < 2 or y < 2 or x+2 >= rgb.shape[1] or y+2 >= rgb.shape[0]:
        return False
    patch = rgb[y-1:y+2, x-1:x+2, :3].mean(axis=(0, 1))
    return float(patch.min()) > 165 and float(patch.max()-patch.min()) < 55


def _ring_score(rgb: np.ndarray, gray: np.ndarray, radius: float,
                center: tuple[float, float]) -> float:
    cx, cy = center
    groups = []
    for cardinal in (0, 90, 180, 270):
        contrast = []
        for delta in (-13, -8, -3, 3, 8, 13):
            angle = math.radians(cardinal + delta)
            dx, dy = math.cos(angle), math.sin(angle)
            x, y = cx + dx * radius, cy + dy * radius
            if not _neutral_white(rgb, x, y):
                contrast.append(0.0)
                continue
            on = _sample_luma(gray, x, y)
            away = (_sample_luma(gray, x+dx*6, y+dy*6)
                    + _sample_luma(gray, x-dx*6, y-dy*6)) / 2
            contrast.append(max(0.0, on-away))
        groups.append(sum(contrast)/len(contrast))
    # Require multiple arc components; a single bright shape should not qualify.
    if sum(v > 12.0 for v in groups) < 3:
        return 0.0
    return min(1.0, float(statistics.median(groups)) / 28.0)


def _cross_score(rgb: np.ndarray, gray: np.ndarray, radius: float,
                 center: tuple[float, float]) -> float:
    cx, cy = center
    groups = []
    for dx, dy in ((1,0), (-1,0), (0,1), (0,-1)):
        contrast = []
        for delta in (1,3,5,7,9,11):
            x, y = cx+dx*(radius+delta), cy+dy*(radius+delta)
            if not _neutral_white(rgb, x, y):
                contrast.append(0.0)
                continue
            on = _sample_luma(gray, x, y)
            # True HUD bars are thin; compare with nearby perpendicular pixels.
            side = (_sample_luma(gray, x+dy*10, y+dx*10)
                    + _sample_luma(gray, x-dy*10, y-dx*10)) / 2
            contrast.append(max(0.0, on-side))
        groups.append(sum(contrast)/len(contrast))
    if min(groups) < 12.0 or max(groups) > min(groups)*1.85:
        return 0.0
    return min(1.0, float(statistics.median(groups))/27.0)


def estimate_native_radius(rgb: np.ndarray, mode: str) -> tuple[float, float] | None:
    """Estimate native shotgun radius or AR inner bar gap from a centered crop.

    Uses local shape contrast on bright and dark backgrounds. Rejects colored
    overlays and high-asymmetry screen features; falls back when uncertain.
    """
    if rgb.ndim != 3 or rgb.shape[2] < 3 or min(rgb.shape[:2]) < 100:
        return None
    cx, cy = (rgb.shape[1]-1)/2, (rgb.shape[0]-1)/2
    gray = (rgb[:, :, 0].astype(np.float32)*.299
            + rgb[:, :, 1].astype(np.float32)*.587
            + rgb[:, :, 2].astype(np.float32)*.114)
    scorer = _ring_score if mode=="Shotgun" else _cross_score
    max_radius = min(76, min(rgb.shape[:2])//2-13)
    candidates = [(r, scorer(rgb, gray, r, (cx,cy)))
                  for r in range(14, max_radius)]
    good = [p for p in candidates if p[1] >= MIN_CONFIDENCE]
    if not good:
        return None
    if mode == "Shotgun":
        radius, conf = max(good, key=lambda p:p[1])
    else:
        peak=max(s for _,s in good)
        # On AR we need the *start* of each bar, not its midpoint.
        threshold=max(MIN_CONFIDENCE,peak*.90)
        radius, conf = min((r,s) for r,s in good if s>=threshold)
    return float(radius), float(conf)

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
