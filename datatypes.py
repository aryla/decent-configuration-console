import math
from enum import Enum, Flag
from typing import NamedTuple, Sequence


class Changes(Flag):
    Alias = 0x01
    HidMode = 0x04
    Profile = 0x08


class HidMode(Enum):
    Hidden = 0
    Keyboard = 1
    Joystick = 2


class PanelId(Enum):
    Left = 0
    Down = 1
    Up = 2
    Right = 3


class ProfileId(Enum):
    Profile1 = 0
    Profile2 = 1
    Profile3 = 2
    Profile4 = 3


class _CurveBand(NamedTuple):
    below: float
    above: float


class CurveBand(_CurveBand):
    def __new__(cls, below: float, above: float):
        if not math.isfinite(below) or below < 0 or below > 0.15:
            raise ValueError('below must be in [0.00, 0.15]')
        if not math.isfinite(above) or above < 0 or above > 0.15:
            raise ValueError('above must be in [0.00, 0.15]')
        return super().__new__(cls, below, above)


class _CurvePoint(NamedTuple):
    x: float
    y: float


class CurvePoint(_CurvePoint):
    def __new__(cls, x: float, y: float):
        if not math.isfinite(x) or x < -1 or x > 1:
            raise ValueError('x must be in [-1, 1]')
        if not math.isfinite(y) or y < 0 or y > 1:
            raise ValueError('y must be in [0, 1]')
        return super().__new__(cls, x, y)


class _Curve(NamedTuple):
    band: CurveBand
    points: Sequence[CurvePoint]


class Curve(_Curve):
    def __new__(cls, band: CurveBand, points: Sequence[CurvePoint]):
        if len(points) < 2 or len(points) > 10:
            raise ValueError('must have 2 to 10 points')
        return super().__new__(cls, band, tuple(points))

    @classmethod
    def default(cls):
        return cls(CurveBand(0.025, 0.025), [CurvePoint(-1.0, 0.5), CurvePoint(1.0, 0.5)])


class Readings(NamedTuple):
    panel: PanelId
    pressed: bool
    x: float
    y: float
    sensors: tuple[int, int]


class _SensorRange(NamedTuple):
    min: int
    max: int


class SensorRange(_SensorRange):
    def __new__(cls, min: int, max: int):
        if min < 0 or min > 4095 or min + 48 > max:
            raise ValueError('min must be in [0, max - 48]')
        if max < 0 or max > 4095 or max < min + 48:
            raise ValueError('max must be in [min + 48, 4095]')
        return super().__new__(cls, min, max)


class _Sensitivity(NamedTuple):
    sensitivity: int


class Sensitivity(_Sensitivity):
    def __new__(cls, sensitivity: int):
        if sensitivity < 0 or sensitivity > 1000:
            raise ValueError('sensitivity must be in [0, 1000]')
        return super().__new__(cls, sensitivity)
