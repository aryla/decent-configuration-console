import math
from typing import Callable

import PySide6.QtCore
import PySide6.QtQml
from PySide6.QtCore import QObject, QPointF, Signal, Slot

from datatypes import (
    Changes,
    Curve,
    CurveBand,
    CurvePoint,
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
class CurveModel(QObject):
    below_changed = Signal()
    above_changed = Signal()
    points_changed = Signal()

    band_set = Signal(PanelId, CurveBand)
    curve_reset = Signal(PanelId)
    curve_set = Signal(PanelId, Curve)
    point_added = Signal(PanelId, int, CurvePoint)
    point_moved = Signal(PanelId, int, CurvePoint)

    def __init__(self, parent: QObject | None, id: PanelId):
        super().__init__(parent)
        self._id = id
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
            self.band_set.emit(self._id, CurveBand(self._below, self._above))

    @Property(float, notify=above_changed, final=True)
    def above(self):
        return self._above

    @above.setter
    def above(self, x):
        if self._above != x:
            self._above = x
            self.above_changed.emit()
            self.band_set.emit(self._id, CurveBand(self._below, self._above))

    @Property(list, notify=points_changed, final=True)
    def points(self):
        return self._points

    @Slot(int, float, float)
    def add_point(self, index: int, x: float, y: float):
        assert len(self._points) < 10
        assert index == 0 or x >= self._points[index - 1].x() + 0.01
        assert index == len(self._points) or x <= self._points[index].x() - 0.01
        self._points.insert(index, QPointF(x, y))
        self.points_changed.emit()
        self.point_added.emit(self._id, index, CurvePoint(x, y))

    @Slot(int, float, float)
    def move_point(self, index: int, x: float, y: float):
        assert index == 0 or x >= self._points[index - 1].x() + 0.01
        assert index == len(self._points) - 1 or x <= self._points[index + 1].x() - 0.01
        self._points[index] = QPointF(x, y)
        self.points_changed.emit()
        self.point_moved.emit(self._id, index, CurvePoint(x, y))

    @Slot(int)
    def remove_point(self, index):
        assert len(self._points) > 2
        self._points.pop(index)
        self.points_changed.emit()
        self.curve_set.emit(
            self._id,
            Curve(
                CurveBand(self._below, self._above),
                [CurvePoint(p.x(), p.y()) for p in self._points],
            ),
        )

    @Slot()
    def reset_points(self):
        self.curve_reset.emit(self._id)

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
        return max(
            self._zero, min(self._zero + self._width, math.ceil(self._zero + x * self._width))
        )

    @Property(float, notify=min_changed, final=True)
    def min(self):
        return self._to_unit_range(self._min)

    @min.setter
    def min(self, x):
        i = self._from_unit_range(x)
        clamped = min(i, self._max - self._width_limit)
        if clamped != self._min:
            self._min = clamped
            self.min_changed.emit()
            self.range_set.emit()
        elif clamped != i:
            self.min_changed.emit()

    @Property(float, notify=max_changed, final=True)
    def min_limit(self):
        return self._to_unit_range(self._max - self._width_limit)

    @Property(float, notify=max_changed, final=True)
    def max(self):
        return self._to_unit_range(self._max)

    @max.setter
    def max(self, x):
        i = self._from_unit_range(x)
        clamped = max(self._from_unit_range(x), self._min + self._width_limit)
        if clamped != self._max:
            self._max = clamped
            self.max_changed.emit()
            self.range_set.emit()
        elif clamped != i:
            self.max_changed.emit()

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
        self._curve = CurveModel(self, id)
        self._dot = QPointF(0.0, -10.0)
        self._flipped = flipped
        self._pressed = False
        self._sensitivity = 0
        self._sensors = (Sensor(self, sensor1_name), Sensor(self, sensor2_name))
        for sensor in self._sensors:
            sensor._range.range_set.connect(
                lambda: self.range_set.emit(
                    self._id,
                    (
                        SensorRange(self._sensors[0]._range._min, self._sensors[0]._range._max),
                        SensorRange(self._sensors[1]._range._min, self._sensors[1]._range._max),
                    ),
                )
            )

    @Property(CurveModel, constant=True, final=True)
    def curve(self):
        return self._curve

    @Property(QPointF, notify=dot_changed, final=True)
    def dot(self):
        return self._dot

    @Property(str, constant=True, final=True)
    def name(self):
        return self._id.name

    @Property(bool, notify=pressed_changed, final=True)
    def pressed(self):
        return self._pressed

    @Property(list, constant=True, final=True)
    def sensors(self):
        if self._flipped:
            return list(reversed(self._sensors))
        else:
            return list(self._sensors)

    @Property(float, notify=sensitivity_changed, final=True)
    def sensitivity(self):
        return self._sensitivity / 1000.0

    @sensitivity.setter
    def sensitivity(self, x):
        i = max(0, min(1000, math.ceil(x * 1000.0)))
        if self._sensitivity != i:
            self._sensitivity = i
            self.sensitivity_changed.emit()
            self.sensitivity_set.emit(self._id, Sensitivity(self._sensitivity))

    @Slot(Readings)
    def pad_readings(self, readings: Readings):
        self._pressed = readings.pressed
        self._dot = QPointF(readings.x, readings.y)
        self.pressed_changed.emit()
        self.dot_changed.emit()
        for i in range(2):
            self._sensors[i].pad_level(readings.sensors[i])

    @Slot(Sensitivity)
    def pad_sensitivity(self, sensitivity: Sensitivity):
        self._sensitivity = sensitivity.sensitivity
        self.sensitivity_changed.emit()


@QmlElement
class Model(QObject):
    alias_changed = Signal()
    connected_changed = Signal()
    changes_changed = Signal()
    hidmode_changed = Signal()
    message_changed = Signal()
    profile_changed = Signal()
    serial_changed = Signal()

    alias_set = Signal(str)
    curve_band_set = Signal(PanelId, CurveBand)
    changes_reverted = Signal(Changes)
    changes_saved = Signal(Changes)
    curve_point_added = Signal(PanelId, int, CurvePoint)
    curve_point_moved = Signal(PanelId, int, CurvePoint)
    curve_reset = Signal(PanelId)
    curve_set = Signal(PanelId, Curve)
    do_connect = Signal()
    do_disconnect = Signal()
    hidmode_set = Signal(HidMode)
    profile_set = Signal(ProfileId)
    range_set = Signal(PanelId, tuple)
    sensitivity_set = Signal(PanelId, Sensitivity)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._alias = 'Unnamed'
        self._changes = Changes(0)
        self._connected = False
        self._hidmode = HidMode.Hidden
        self._message = None
        self._profile = -1
        self._serial = 0

        self._panels = (
            Panel(self, PanelId.Left, 'Back', 'Front', flipped=True),
            Panel(self, PanelId.Down, 'Right', 'Left', flipped=True),
            Panel(self, PanelId.Up, 'Left', 'Right', flipped=False),
            Panel(self, PanelId.Right, 'Front', 'Back', flipped=False),
        )

        for panel in self._panels:
            panel.range_set.connect(self.range_set)
            panel.sensitivity_set.connect(self.sensitivity_set)
            panel.curve.band_set.connect(self.curve_band_set)
            panel.curve.curve_reset.connect(self.curve_reset)
            panel.curve.curve_set.connect(self.curve_set)
            panel.curve.point_moved.connect(self.curve_point_moved)
            panel.curve.point_added.connect(self.curve_point_added)

            panel.range_set.connect(self._handle_change)
            panel.sensitivity_set.connect(self._handle_change)
            panel.curve.band_set.connect(self._handle_change)
            panel.curve.curve_reset.connect(self._handle_change)
            panel.curve.curve_set.connect(self._handle_change)
            panel.curve.point_moved.connect(self._handle_change)
            panel.curve.point_added.connect(self._handle_change)

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

    @Property(int, notify=hidmode_changed, final=True)
    def hidmode(self):
        return self._hidmode.value

    @hidmode.setter
    def hidmode(self, x):
        mode = HidMode(x)
        if self._hidmode != mode:
            self._hidmode = mode
            self.hidmode_changed.emit()
            self.hidmode_set.emit(mode)
            self._changes |= Changes.HidMode
            self.changes_changed.emit()

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

    @Property(list, constant=True, final=True)
    def panels(self):
        return list(self._panels)

    @Property(int, notify=serial_changed, final=True)
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
        self._panels[panel.value].curve.pad_band(band)

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
        self._panels[panel.value].curve.pad_curve(curve)

    @Slot()
    def pad_disconnected(self):
        self._connected = False
        self.connected_changed.emit()

    @Slot(HidMode)
    def pad_hidmode(self, mode: HidMode):
        self._hidmode = mode
        self.hidmode_changed.emit()

    @Slot(ProfileId)
    def pad_profile(self, profile: ProfileId):
        self._profile = profile.value
        self.profile_changed.emit()

    @Slot(PanelId, tuple)
    def pad_ranges(self, panel: PanelId, ranges: tuple[SensorRange, SensorRange]):
        for i in range(2):
            self._panels[panel.value]._sensors[i]._range.pad_range(ranges[i])

    @Slot(Readings)
    def pad_readings(self, readings: Readings):
        self._panels[readings.panel.value].pad_readings(readings)

    @Slot(int)
    def pad_serial(self, serial: int):
        self._serial = serial
        self.serial_changed.emit()

    @Slot(PanelId, Sensitivity)
    def pad_sensitivity(self, panel: PanelId, sensitivity: Sensitivity):
        self._panels[panel.value].pad_sensitivity(sensitivity)

    @Slot(str)
    def pad_error(self, error: str):
        self.message = error
