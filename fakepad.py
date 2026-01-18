import random

from PySide6.QtCore import QObject, QThread, QTimer, Signal, Slot

import pad
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
from util import throttle_key


class FakePanel:
    def __init__(self, id: PanelId):
        self.id = id
        self.sensitivity = Sensitivity(random.randint(200, 800))
        self.band = CurveBand(
            random.uniform(0.0, 0.150),
            random.uniform(0.0, 0.150),
        )
        self.points = [
            CurvePoint(
                random.uniform(-1.0, -0.8),
                random.uniform(0.1, 0.5),
            ),
            CurvePoint(
                random.uniform(-0.3, 0.3),
                random.uniform(0.1, 0.5),
            ),
            CurvePoint(
                random.uniform(0.8, 1.0),
                random.uniform(0.1, 0.5),
            ),
        ]
        self.sensors = [
            SensorRange(
                random.randint(0, 1000),
                random.randint(3895, 4095),
            ),
            SensorRange(
                random.randint(0, 1000),
                random.randint(3895, 4095),
            ),
        ]
        self.readings = Readings(
            self.id,
            False,
            random.uniform(-1.0, 0.0),
            random.uniform(1.0, 0.0),
            (random.randint(0, 4095), random.randint(0, 4095)),
        )


class FakeProfile:
    def __init__(self):
        self.panels = (
            FakePanel(PanelId.Left),
            FakePanel(PanelId.Down),
            FakePanel(PanelId.Up),
            FakePanel(PanelId.Right),
        )


class _FakePad(QObject):
    alias = Signal(str)
    band = Signal(PanelId, CurveBand)
    changes = Signal(Changes)
    connected = Signal()
    curve = Signal(PanelId, Curve)
    disconnected = Signal()
    error = Signal(str)
    hidmode = Signal(HidMode)
    profile = Signal(ProfileId)
    ranges = Signal(PanelId, tuple)
    readings = Signal(Readings)
    sensitivity = Signal(PanelId, Sensitivity)
    serial = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._alias = 'Unnamed'
        self._changes = Changes(0)
        self._hidmode = HidMode.Joystick
        self._profile = ProfileId.Profile1
        self._profiles = [FakeProfile() for _ in range(4)]

        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(100)
        self.poll_timer.timeout.connect(self._poll)

        self._thread = QThread()
        self._thread.setObjectName('Pad thread')
        self._thread.finished.connect(self.deleteLater)
        self.moveToThread(self._thread)
        self._thread.start()

    @Slot()
    def connect(self):
        self.connected.emit()
        self._refresh()
        self.start_polling()

    @Slot()
    def disconnect(self):
        self.stop_polling()
        self.disconnected.emit()

    @Slot()
    def get_info(self):
        self.serial.emit(123456)

    @Slot()
    def get_alias(self):
        self.alias.emit(self._alias)

    @Slot(str)
    def set_alias(self, alias: str):
        self._alias = alias
        self.alias.emit(alias)

    @Slot()
    def get_changes(self):
        self.changes.emit(self._changes)

    @Slot()
    @throttle_key(lambda changes: changes)
    def save_changes(self, changes: Changes):
        self._changes = Changes(0)
        self.changes.emit(self._changes)

    @Slot()
    @throttle_key(lambda changes: changes)
    def revert_changes(self, changes: Changes):
        self._changes = Changes(0)
        self.changes.emit(self._changes)
        self._alias = 'Unnamed'
        self._hidmode = HidMode.Joystick
        self._profile = ProfileId.Profile1
        self._profiles = [FakeProfile() for _ in range(4)]
        self.get_alias()
        self.get_hidmode()
        self.get_profile()
        for panel in PanelId:
            self.get_sensitivity(panel)
            self.get_ranges(panel)
            self.get_curve(panel)

    @Slot()
    def get_hidmode(self):
        self.hidmode.emit(self._hidmode)

    @Slot(HidMode)
    @throttle_key(lambda mode: mode)
    def set_hidmode(self, mode: HidMode):
        self._hidmode = mode
        self.hidmode.emit(self._hidmode)

    @Slot()
    def get_profile(self):
        self.profile.emit(self._profile)

    @Slot(ProfileId)
    @throttle_key(lambda profile: profile)
    def set_profile(self, profile: ProfileId):
        self._profile = profile
        self.profile.emit(self._profile)
        for panel in PanelId:
            self.get_sensitivity(panel)
            self.get_ranges(panel)
            self.get_curve(panel)

    @Slot()
    @throttle_key(lambda panel: panel)
    def get_curve(self, panel: PanelId):
        fake_panel = self._profiles[self._profile.value].panels[panel.value]
        self.curve.emit(panel, Curve(fake_panel.band, fake_panel.points))

    @Slot(PanelId)
    @throttle_key(lambda panel: panel)
    def get_readings(self, panel: PanelId):
        fake_panel = self._profiles[self._profile.value].panels[panel.value]
        current = fake_panel.readings
        fake_panel.readings = Readings(
            current.panel,
            (not current.pressed if random.randint(0, 20) == 0 else current.pressed),
            max(-1.0, min(1.0, current.x + random.uniform(-0.02, 0.02))),
            max(0.0, min(1.0, current.y + random.uniform(-0.02, 0.02))),
            (
                max(0, min(4095, current.sensors[0] + random.randint(-10, 10))),
                max(0, min(4095, current.sensors[1] + random.randint(-10, 10))),
            ),
        )
        self.readings.emit(fake_panel.readings)

    @Slot(PanelId, int, CurvePoint)
    @throttle_key(lambda panel, index, p: (panel, index, p))
    def add_curve_point(self, panel: PanelId, index: int, p: CurvePoint):
        fake_panel = self._profiles[self._profile.value].panels[panel.value]
        fake_panel.points.insert(index, p)

    @Slot(PanelId, int)
    @throttle_key(lambda panel, index: (panel, index))
    def delete_curve_point(self, panel: PanelId, index: int):
        fake_panel = self._profiles[self._profile.value].panels[panel.value]
        fake_panel.points.pop(index)

    @Slot(PanelId, Curve)
    @throttle_key(lambda panel, index, _: (panel, index))
    def set_curve_point(self, panel: PanelId, index: int, p: CurvePoint):
        fake_panel = self._profiles[self._profile.value].panels[panel.value]
        fake_panel.points[index] = p

    @Slot(PanelId)
    @throttle_key(lambda panel: panel)
    def reset_curve(self, panel: PanelId):
        fake_panel = self._profiles[self._profile.value].panels[panel.value]
        default = Curve.default()
        fake_panel.band = default.band
        fake_panel.points = list(default.points)
        self.get_curve(panel)

    @Slot(PanelId, Curve)
    @throttle_key(lambda panel, _: panel)
    def set_curve(self, panel: PanelId, curve: Curve):
        fake_panel = self._profiles[self._profile.value].panels[panel.value]
        fake_panel.band = curve.band
        fake_panel.points = list(curve.points)
        self.get_curve(panel)

    @Slot()
    @throttle_key(lambda panel: panel)
    def get_sensitivity(self, panel: PanelId):
        fake_panel = self._profiles[self._profile.value].panels[panel.value]
        self.sensitivity.emit(panel, fake_panel.sensitivity)

    @Slot(PanelId, Sensitivity)
    @throttle_key(lambda panel, _: panel)
    def set_sensitivity(self, panel: PanelId, sensitivity: Sensitivity):
        fake_panel = self._profiles[self._profile.value].panels[panel.value]
        fake_panel.sensitivity = sensitivity

    @Slot(PanelId)
    @throttle_key(lambda panel: panel)
    def get_band(self, panel: PanelId):
        fake_panel = self._profiles[self._profile.value].panels[panel.value]
        self.band.emit(panel, fake_panel.band)

    @Slot(PanelId, CurveBand)
    @throttle_key(lambda panel, _: panel)
    def set_band(self, panel: PanelId, band: CurveBand):
        fake_panel = self._profiles[self._profile.value].panels[panel.value]
        fake_panel.band = band

    @Slot()
    @throttle_key(lambda panel: panel)
    def get_ranges(self, panel: PanelId):
        fake_panel = self._profiles[self._profile.value].panels[panel.value]
        self.ranges.emit(panel, (fake_panel.sensors[0], fake_panel.sensors[1]))

    @Slot(PanelId, tuple)
    @throttle_key(lambda panel, _: panel)
    def set_ranges(self, panel: PanelId, ranges: tuple[SensorRange, SensorRange]):
        fake_panel = self._profiles[self._profile.value].panels[panel.value]
        fake_panel.sensors[0] = ranges[0]
        fake_panel.sensors[1] = ranges[1]

    @Slot()
    def start_polling(self):
        self.poll_timer.start()

    @Slot()
    def stop_polling(self):
        self.poll_timer.stop()

    @Slot()
    def _poll(self):
        for panel in PanelId:
            self.get_readings(panel)

    def _refresh(self):
        self.get_info()
        self.get_alias()
        self.get_profile()
        self.get_hidmode()
        for panel in PanelId:
            self.get_sensitivity(panel)
            self.get_ranges(panel)
            self.get_curve(panel)
        self.get_changes()

    @Slot()
    def quit(self):
        self._thread.quit()


def FakePad(parent: QObject | None = None) -> pad.Pad:
    return _FakePad(parent)  # pyright: ignore[reportReturnType]
