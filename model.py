import math
from typing import Callable

import PySide6.QtCore
import PySide6.QtQml
from PySide6.QtCore import QObject, QPointF, Signal, Slot

from datatypes import (
    Changes,
    Curve,
    CurveBand,
    HidMode,
    PanelId,
    ProfileId,
    Readings,
    Sensitivity,
    SensorRange,
)

QML_IMPORT_NAME = 'Model'
QML_IMPORT_MAJOR_VERSION = 1


# Workarounds for incomplete type annotations.


def QmlElement[T](x: T) -> T:
    return PySide6.QtQml.QmlElement(x)  # pyright: ignore[reportReturnType]


def Property(*args, **kwargs) -> Callable[[object], property]:
    return PySide6.QtCore.Property(*args, **kwargs)  # pyright: ignore[reportReturnType]


@QmlElement
class CurveView(QObject):
    below_changed = Signal()
    above_changed = Signal()
    points_changed = Signal()

    band_set = Signal()

    def __init__(self, parent):
        super().__init__(parent)
        self._points = list[QPointF]()
        self._below = 0.025
        self._above = 0.025

    @Property(float, notify=below_changed, final=True)
    def below(self):
        return self._below

    @below.setter
    def below(self, x):
        if self._below != x:
            self._below = x
            self.below_changed.emit()
            self.band_set.emit()

    @Property(float, notify=above_changed, final=True)
    def above(self):
        return self._above

    @above.setter
    def above(self, x):
        if self._above != x:
            self._above = x
            self.above_changed.emit()
            self.band_set.emit()

    @Property(list, notify=points_changed, final=True)
    def points(self):
        return self._points

    @Slot(CurveBand)
    def pad_band(self, band: CurveBand):
        self._below = band.below
        self._above = band.above
        self.below_changed.emit()
        self.above_changed.emit()

    @Slot(Curve)
    def pad_curve(self, curve: Curve):
        self.pad_band(curve.band)
        self._points = [QPointF(p.x, p.y) for p in curve.points]
        self.points_changed.emit()


@QmlElement
class Range(QObject):
    min_changed = Signal()
    max_changed = Signal()

    range_set = Signal()

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
    def min(self):
        return self._to_unit_range(self._min)

    @min.setter
    def min(self, x):
        i = min(self._from_unit_range(x), self._max - self._width_limit)
        if i != self._min:
            self._min = i
            self.min_changed.emit()
            self.range_set.emit()

    @Property(float, notify=max_changed, final=True)
    def min_limit(self):
        return self._to_unit_range(self._max - self._width_limit)

    @Property(float, notify=max_changed, final=True)
    def max(self):
        return self._to_unit_range(self._max)

    @max.setter
    def max(self, x):
        i = max(self._from_unit_range(x), self._min + self._width_limit)
        if i != self._max:
            self._max = i
            self.max_changed.emit()
            self.range_set.emit()

    @Property(float, notify=min_changed, final=True)
    def max_limit(self):
        return self._to_unit_range(self._min + self._width_limit)

    @Slot(SensorRange)
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
        self._range = Range(self)

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
    dot_changed = Signal()
    pressed_changed = Signal()

    range_set = Signal(PanelId, tuple)
    sensitivity_set = Signal(PanelId, Sensitivity)

    def __init__(self, parent, id: PanelId, sensor1_name: str, sensor2_name: str, flipped: bool):
        super().__init__(parent)
        self._id = id
        self._curve = CurveView(self)
        self._dot = QPointF(0.0, -10.0)
        self._flipped = flipped
        self._pressed = False
        self._sensitivity = 0
        self.sensors = (Sensor(self, sensor1_name), Sensor(self, sensor2_name))
        for sensor in self.sensors:
            sensor._range.range_set.connect(
                lambda: self.range_set.emit(
                    self._id,
                    (
                        SensorRange(self.sensors[0]._range._min, self.sensors[0]._range._max),
                        SensorRange(self.sensors[1]._range._min, self.sensors[1]._range._max),
                    ),
                )
            )

    @Property(CurveView, constant=True, final=True)
    def curve(self):
        return self._curve

    @Property(QPointF, notify=dot_changed, final=True)
    def dot(self):
        return self._dot

    @Property(str, constant=True, final=True)
    def name(self):
        return self._id.name

    @Property(bool, final=True)
    def pressed(self):
        return self._pressed

    @Property(Sensor, constant=True, final=True)
    def sensor0(self):
        return self.sensors[1 if self._flipped else 0]

    @Property(Sensor, constant=True, final=True)
    def sensor1(self):
        return self.sensors[0 if self._flipped else 1]

    @Property(int, notify=sensitivity_changed, final=True)
    def sensitivity(self):
        return self._sensitivity

    @sensitivity.setter
    def sensitivity(self, x):
        if self._sensitivity != x:
            self._sensitivity = x
            self.sensitivity_changed.emit()
            self.sensitivity_set.emit(self._id, Sensitivity(self._sensitivity))

    @Slot(Readings)
    def pad_readings(self, readings: Readings):
        self._pressed = readings.pressed
        self._dot = QPointF(readings.x, readings.y)
        self.pressed_changed.emit()
        self.dot_changed.emit()
        for i in range(2):
            self.sensors[i].pad_level(readings.sensors[i])

    @Slot(Sensitivity)
    def pad_sensitivity(self, sensitivity: Sensitivity):
        self._sensitivity = sensitivity.sensitivity
        self.sensitivity_changed.emit()


@QmlElement
class Model(QObject):
    alias_changed = Signal()
    connected_changed = Signal()
    changes_changed = Signal()
    message_changed = Signal()
    profile_changed = Signal()
    serial_changed = Signal()

    alias_set = Signal(str)
    changes_reverted = Signal(Changes)
    changes_saved = Signal(Changes)
    do_connect = Signal()
    do_disconnect = Signal()
    profile_set = Signal(ProfileId)
    range_set = Signal(PanelId, tuple)
    sensitivity_set = Signal(PanelId, Sensitivity)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._alias = 'Unnamed'
        self._changes = Changes(0)
        self._connected = False
        self._message = None
        self._profile = -1

        self.panels = (
            Panel(self, PanelId.Left, 'Back', 'Front', flipped=True),
            Panel(self, PanelId.Down, 'Right', 'Left', flipped=True),
            Panel(self, PanelId.Up, 'Left', 'Right', flipped=False),
            Panel(self, PanelId.Right, 'Front', 'Back', flipped=False),
        )

        for panel in self.panels:
            panel.range_set.connect(self.range_set)
            panel.sensitivity_set.connect(self.sensitivity_set)
            panel.range_set.connect(self._handle_change)
            panel.sensitivity_set.connect(self._handle_change)

    @Property(str, notify=alias_changed, final=True)
    def alias(self):
        return self._alias

    @alias.setter
    def alias(self, x):
        if len(x.encode('utf-8')) > 30:
            self.alias_changed.emit()
        elif self._alias != x:
            self._alias = x
            self.alias_changed.emit()
            self.alias_set.emit(x)
            self._changes |= Changes.Alias
            self.changes_changed.emit()

    @Property(bool, notify=connected_changed, final=True)
    def connected(self):
        return self._connected

    @Property(bool, notify=changes_changed, final=True)
    def has_changes(self):
        return bool(self._changes)

    @Property(str, notify=message_changed, final=True)
    def message(self):
        return self._message

    @message.setter
    def message(self, x):
        if self._message != x:
            self._message = x
            self.message_changed.emit()

    @Property(int, notify=profile_changed, final=True)
    def profile(self):
        return self._profile

    @profile.setter
    def profile(self, x):
        if self._profile != x:
            self._profile = x
            self.profile_changed.emit()
            self.profile_set.emit(ProfileId(x))

    @Property(Panel, constant=True, final=True)
    def panel0(self):
        return self.panels[0]

    @Property(Panel, constant=True, final=True)
    def panel1(self):
        return self.panels[1]

    @Property(Panel, constant=True, final=True)
    def panel2(self):
        return self.panels[2]

    @Property(Panel, constant=True, final=True)
    def panel3(self):
        return self.panels[3]

    @Property(int, final=True)
    def serial(self):
        return self._serial

    @Slot()
    def _handle_change(self):
        self._changes |= Changes.Profile
        self.changes_changed.emit()

    @Slot()
    def revert_changes(self):
        if self._changes:
            self.changes_reverted.emit(self._changes)
            self._changes = Changes(0)
            self.changes_changed.emit()

    @Slot()
    def save_changes(self):
        if self._changes:
            self.changes_saved.emit(self._changes)
            self._changes = Changes(0)
            self.changes_changed.emit()

    @Slot(str)
    def pad_alias(self, alias: str):
        self._alias = alias
        self.alias_changed.emit()

    @Slot(PanelId, CurveBand)
    def pad_band(self, panel: PanelId, band: CurveBand):
        self.panels[panel.value].curve.pad_band(band)

    @Slot(Changes)
    def pad_changes(self, changes: Changes):
        if self._changes != changes:
            self._changes = changes
            self.changes_changed.emit()

    @Slot()
    def pad_connected(self):
        self._connected = True
        self.connected_changed.emit()

    @Slot(PanelId, Curve)
    def pad_curve(self, panel: PanelId, curve: Curve):
        self.panels[panel.value].curve.pad_curve(curve)

    @Slot()
    def pad_disconnected(self):
        self._connected = False
        self.connected_changed.emit()

    @Slot(HidMode)
    def pad_hidmode(self, mode: HidMode):
        pass

    @Slot(ProfileId)
    def pad_profile(self, profile: ProfileId):
        self._profile = profile.value
        self.profile_changed.emit()

    @Slot(PanelId, tuple)
    def pad_ranges(self, panel: PanelId, ranges: tuple[SensorRange, SensorRange]):
        for i in range(2):
            self.panels[panel.value].sensors[i]._range.pad_range(ranges[i])

    @Slot(Readings)
    def pad_readings(self, readings: Readings):
        self.panels[readings.panel.value].pad_readings(readings)

    @Slot(int)
    def pad_serial(self, serial: int):
        self._serial = serial
        self.serial_changed.emit()

    @Slot(PanelId, Sensitivity)
    def pad_sensitivity(self, panel: PanelId, sensitivity: Sensitivity):
        self.panels[panel.value].pad_sensitivity(sensitivity)

    @Slot(str)
    def pad_error(self, error: str):
        self.message = error
