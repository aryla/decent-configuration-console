import enum
import typing


class HidMode(enum.Enum):
    Hidden = 0
    Keyboard = 1
    Joystick = 2


class PanelId(enum.Enum):
    Left = 0
    Down = 1
    Up = 2
    Right = 3


class ProfileId(enum.Enum):
    Profile1 = 0
    Profile2 = 1
    Profile3 = 2
    Profile4 = 3


class Readings(typing.NamedTuple):
    panel: PanelId
    pressed: bool
    x: float
    y: float
    sensors: tuple[int, int]


class _SensorRange(typing.NamedTuple):
    min: int
    max: int


class SensorRange(_SensorRange):
    def __new__(cls, min: int, max: int):
        if min < 0 or min > 4095 or min + 48 > max:
            raise ValueError('min must be in [0, max - 48]')
        if max < 0 or max > 4095 or max < min + 48:
            raise ValueError('max must be in [min + 48, 4095]')
        return super().__new__(cls, min, max)


class _Sensitivity(typing.NamedTuple):
    sensitivity: int


class Sensitivity(_Sensitivity):
    def __new__(cls, sensitivity: int):
        if sensitivity < 0 or sensitivity > 1000:
            raise ValueError('sensitivity must be in [0, 1000]')
        return super().__new__(cls, sensitivity)
