# ============================================
# Proyecto:  MEOWGUARD — Sistema Robótico Autónomo de Control de Plagas
# Archivo:   traccion.py
# Objetivo:  Control diferencial de tracción 4WD con corrección de rumbo por giroscopio y encoders
# Equipo:    Mónica Moreno Torres (23241119), Leonardo Gael Niño Cabrera (23240382)
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# ============================================
import time

import config as cfg

WHEELS = ("delantera izquierda", "trasera izquierda", "delantera derecha", "trasera derecha")


def rueda_sospechosa(speeds, yaw_difference):
    """Compara cada rueda con su pareja y la velocidad estimada a partir del otro lado."""
    suspects = []
    for index, speed in enumerate(speeds):
        mate = speeds[index ^ 1]
        opposite = (speeds[index ^ 2], speeds[index ^ 3])
        if abs(opposite[0] - opposite[1]) > max(8, 0.25 * max(opposite)):
            continue
        opposite_speed = sum(opposite) / 2
        expected = opposite_speed + (yaw_difference if index >= 2 else -yaw_difference)
        if expected < 10 or abs(mate - expected) > max(8, 0.30 * expected):
            continue
        if speed - max(expected, mate) >= max(12, 0.45 * max(expected, mate)):
            suspects.append((index, "giro_excesivo"))
        elif min(expected, mate) - speed >= max(10, 0.55 * expected):
            suspects.append((index, "rueda_lenta"))
    return suspects[0] if len(suspects) == 1 else None


class Traccion:
    def __init__(self, encoders):
        self.encoders = encoders
        self.yaw = 0.0
        self.healthy = False
        self.raw_valid = False
        self.speeds = None
        self.reset("s", time.ticks_ms())

    def reset(self, motion, now):
        self.motion = motion
        self.since = now
        self.angle = 0.0
        self.drift_since = None
        self.drift = False
        self.wheel = None
        self.candidate = None
        self.last_window = now
        self.window_angle = 0.0
        self.collecting = False
        self.speeds = None

    def update(self, motion, base, sample, now, elapsed_ms):
        self.healthy = sample is not None
        if motion != self.motion or (self.raw_valid != self.healthy):
            self.reset(motion, now)
        self.raw_valid = self.healthy
        self.yaw = 0.65 * self.yaw + 0.35 * sample if self.healthy else 0.0
        self.angle += self.yaw * elapsed_ms / 1000
        if motion == "s":
            self.angle = 0.0
            return 0, 0
        if not self.healthy:
            return base, base
        floor = min(base, 30)
        if motion in ("l", "r"):
            limited = max(floor, base - min(15, max(0, abs(self.yaw) - 105) * 0.25))
            return limited, limited

        sign = 1 if motion == "f" else -1
        age = time.ticks_diff(now, self.since)
        if age >= 320:
            strong = abs(self.yaw) >= 26 and abs(self.angle) >= 5
            if strong and self.drift_since is None:
                self.drift_since = now
            elif abs(self.yaw) < 17:
                self.drift_since = None
                self.drift = False
            if strong and time.ticks_diff(now, self.drift_since) >= 180:
                self.drift = True
        self._compare_wheels(sign, age, now)

        # Yaw positivo = nariz girando a la izquierda. En reversa se invierte el lado.
        correction = max(-18, min(18, (0.24 * self.yaw + 0.60 * self.angle) * sign))
        if self.drift:
            base = max(floor, base - 8)
        left = base + min(0, correction)
        right = base - max(0, correction)
        if self.wheel is not None:
            index, reason = self.wheel
            if reason == "giro_excesivo":
                if index < 2:
                    left = min(left, base - 12)
                else:
                    right = min(right, base - 12)
            else:
                left, right = left - 8, right - 8
        return max(floor, left), max(floor, right)

    def _compare_wheels(self, sign, age, now):
        if self.encoders is None or age < 380:
            return
        if not self.collecting:
            self.collecting = True
            self.last_window = now
            self.window_angle = self.angle
            self.encoders.reset()
            return
        interval = time.ticks_diff(now, self.last_window)
        if interval < 320:
            return
        seconds = interval / 1000
        self.last_window = now
        yaw = (self.angle - self.window_angle) / seconds
        self.window_angle = self.angle
        self.speeds = self.encoders.speeds(seconds)
        candidate = rueda_sospechosa(self.speeds, sign * yaw * 0.0174533 * cfg.TRACK_CM)
        self.wheel = candidate if candidate is not None and candidate == self.candidate else None
        self.candidate = candidate
