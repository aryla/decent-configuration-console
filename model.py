import math

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtQml import QmlElement

from datatypes import HidMode, ProfileId, Readings, SensorRange, SensorRanges

QML_IMPORT_NAME = 'Model'
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class Range(QObject):
    min_changed = Signal()
    max_changed = Signal()

    def __init__(self, parent, min: int = 0, max: int = 4095, width: int = 48):
        super().__init__(parent)
        self._zero = min
        self._width = max - min
        self._width_limit = width
        self._min = min
        self._max = max

    def _to_unit_range(self, x: int) -> float:
        return (x - self._zero) / self._width

    def _from_unit_range(self, x: float):
        return math.ceil(self._zero + x * self._width)

    @Property(float, notify=min_changed, final=True)
    def min(self):  # pyright: ignore[reportRedeclaration]
        return self._to_unit_range(self._min)

    @min.setter
    def min(self, x):
        i = min(self._from_unit_range(x), self._max - self._width_limit)
        if i != self._min:
            self._min = i
            self.min_changed.emit()

    @Property(float, notify=max_changed, final=True)
    def min_limit(self):
        return self._to_unit_range(self._max - self._width_limit)

    @Property(float, notify=max_changed, final=True)
    def max(self):  # pyright: ignore[reportRedeclaration]
        return self._to_unit_range(self._max)

    @max.setter
    def max(self, x):
        i = max(self._from_unit_range(x), self._min + self._width_limit)
        if i != self._max:
            self._max = i
            self.max_changed.emit()

    @Property(float, notify=min_changed, final=True)
    def max_limit(self):
        return self._to_unit_range(self._min + self._width_limit)

    @Slot()
    def pad_range(self, range: SensorRange):
        self._min = range.min
        self._max = range.max
        self.min_changed.emit()
        self.max_changed.emit()


@QmlElement
class Sensor(QObject):
    level_changed = Signal()

    def __init__(self, parent, name: str):
        super().__init__(parent)
        self._name = name
        self._level = 0
        self._range = Range(self)  # pyright: ignore[reportCallIssue]

    @Property(str, constant=True, final=True)
    def name(self):
        return self._name

    @Property(float, notify=level_changed, final=True)
    def level(self):
        return self._level

    @Property(Range, constant=True, final=True)
    def range(self):
        return self._range

    @Slot(int)
    def pad_level(self, level: int):
        self._level = level / 4095.0
        self.level_changed.emit()


@QmlElement
class Panel(QObject):
    sensitivity_changed = Signal()

    def __init__(self, parent, name: str, sensor1_name: str, sensor2_name: str, flipped: bool):
        super().__init__(parent)
        self._name = name
        self._sensors = (Sensor(self, sensor1_name), Sensor(self, sensor2_name))
        self._flipped = flipped
        self._sensitivity = 0

    @Property(str, constant=True, final=True)
    def name(self):
        return self._name

    @Property(Sensor, constant=True, final=True)
    def sensor0(self):
        return self._sensors[1 if self._flipped else 0]

    @Property(Sensor, constant=True, final=True)
    def sensor1(self):
        return self._sensors[0 if self._flipped else 1]

    @Property(int, notify=sensitivity_changed, final=True)
    def sensitivity(self):  # pyright: ignore[reportRedeclaration]
        return self._sensitivity

    @sensitivity.setter
    def sensitivity(self, x):
        if self._sensitivity != x:
            self._sensitivity = x
            self.sensitivity_changed.emit()


@QmlElement
class Model(QObject):
    alias_changed = Signal()
    profile_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._alias = 'Unnamed'
        self._profile = 1
        self._panels = (
            Panel(self, 'Left', 'Back', 'Front', flipped=True),  # pyright: ignore[reportCallIssue]
            Panel(self, 'Down', 'Right', 'Left', flipped=True),  # pyright: ignore[reportCallIssue]
            Panel(self, 'Up', 'Left', 'Right', flipped=False),  # pyright: ignore[reportCallIssue]
            Panel(self, 'Right', 'Front', 'Back', flipped=False),  # pyright: ignore[reportCallIssue]
        )

    @Property(str, notify=alias_changed, final=True)
    def alias(self):  # pyright: ignore[reportRedeclaration]
        return self._alias

    @alias.setter
    def alias(self, x):
        if self._alias != x:
            self._alias = x
            self.alias_changed.emit()

    @Property(int, notify=profile_changed, final=True)
    def profile(self):  # pyright: ignore[reportRedeclaration]
        return self._profile

    @profile.setter
    def profile(self, x):
        if self._profile != x:
            self._profile = x
            self.profile_changed.emit()

    @Property(Panel, constant=True, final=True)
    def panel0(self):
        return self._panels[0]

    @Property(Panel, constant=True, final=True)
    def panel1(self):
        return self._panels[1]

    @Property(Panel, constant=True, final=True)
    def panel2(self):
        return self._panels[2]

    @Property(Panel, constant=True, final=True)
    def panel3(self):
        return self._panels[3]

    @Slot(str)
    def pad_alias(self, alias: str):
        self._alias = alias
        self.alias_changed.emit()

    @Slot()
    def pad_connected(self):
        pass

    @Slot()
    def pad_disconnected(self):
        pass

    @Slot(HidMode)
    def pad_hidmode(self, mode: HidMode):
        pass

    @Slot(ProfileId)
    def pad_profile(self, profile: ProfileId):
        self._profile = profile.value
        self.profile_changed.emit()

    @Slot(Readings)
    def pad_readings(self, readings: Readings):
        panel = self._panels[readings.panel.value]
        for i in range(2):
            panel._sensors[i].pad_level(readings.sensors[i])

    @Slot(SensorRanges)
    def pad_ranges(self, ranges: SensorRanges):
        panel = self._panels[ranges.panel.value]
        for i in range(2):
            panel._sensors[i]._range.pad_range(ranges.ranges[i])
