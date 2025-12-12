import enum
import typing


class SensorRange(typing.NamedTuple):
    min: int
    max: int

    def valid(self):
        return (
            0 <= self.min
            and self.min <= 4095
            and 0 <= self.max
            and self.max <= 4095
            and self.min + 48 <= self.max
        )


class Sensitivity(typing.NamedTuple):
    sensitivity: int

    def valid(self):
        return 0 <= self.sensitivity and self.sensitivity <= 1000


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


class SensorRanges(typing.NamedTuple):
    panel: PanelId
    ranges: tuple[SensorRange, SensorRange]
