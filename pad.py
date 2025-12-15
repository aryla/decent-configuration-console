import functools
import itertools
import struct

from PySide6.QtCore import QObject, QThread, QTimer, Signal, Slot

import usb
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


def handle_errors(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            func(self, *args, **kwargs)
        except usb.NoDeviceError as e:
            print(str(e))
            self.error.emit(str(e))
            self.disconnect()
        except usb.Error as e:
            print(str(e))
            self.error.emit(str(e))

    return wrapper


class Pad(QObject):
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
        self.usb = usb.Usb()

        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(100)
        self.poll_timer.timeout.connect(self._poll)

        self._thread = QThread()
        self._thread.setObjectName('Pad thread')
        self._thread.finished.connect(self.deleteLater)
        self.moveToThread(self._thread)
        self._thread.start()

    def __del__(self):
        del self.usb

    @Slot()
    @handle_errors
    def connect(self):
        try:
            self.stop_polling()
            self.usb.connect()
            self.connected.emit()
            self._refresh()
            self.start_polling()
        except usb.NoDeviceError:
            self.disconnect()
        except:
            self.disconnect()
            raise

    @Slot()
    def disconnect(self):
        self.stop_polling()
        self.usb.disconnect()
        self.disconnected.emit()

    @Slot()
    @handle_errors
    def get_info(self):
        response = self.usb.send(struct.pack('< B', 0x00))
        (serial,) = struct.unpack('< x xx I 25x', response)
        self.serial.emit(serial)

    @Slot()
    @handle_errors
    def get_alias(self):
        response = self.usb.send(struct.pack('< B', 0x10))
        (alias,) = struct.unpack('< x 30s x', response)
        alias = alias.decode('utf-8', errors='replace').strip('\x00')
        self.alias.emit(alias)

    @Slot()
    @handle_errors
    def set_alias(self, alias: str):
        alias_bytes = alias.encode('utf-8')
        if len(alias_bytes) > 30:
            raise ValueError('alias must be at most 30 bytes')
        if len(alias_bytes) == 0:
            alias_bytes = b'Unnamed'
        self.usb.send(struct.pack('< B 30s', 0x11, alias_bytes))
        self.alias.emit(alias)

    @Slot()
    @handle_errors
    def get_changes(self):
        response = self.usb.send(struct.pack('< B', 0x30))
        (flags,) = struct.unpack('< x B 30x', response)
        self.changes.emit(Changes(flags))

    @Slot()
    @throttle_key(lambda changes: changes)
    @handle_errors
    def save_changes(self, changes: Changes):
        self.usb.send(struct.pack('< BB', 0x31, changes.value))
        self.changes.emit(Changes(0))

    @Slot()
    @throttle_key(lambda changes: changes)
    @handle_errors
    def revert_changes(self, changes: Changes):
        self.usb.send(struct.pack('< BB', 0x32, changes.value))
        self.changes.emit(Changes(0))
        if changes & Changes.Alias:
            self.get_alias()
        if changes & Changes.HidMode:
            self.get_hidmode()
        if changes & Changes.Profile:
            self.get_profile()
            for panel in PanelId:
                self.get_sensitivity(panel)
                self.get_ranges(panel)
                self.get_curve(panel)

    @Slot()
    @handle_errors
    def get_hidmode(self):
        response = self.usb.send(struct.pack('< B', 0x50))
        (hidmode,) = struct.unpack('< x B 30x', response)
        self.hidmode.emit(HidMode(hidmode))

    @Slot(HidMode)
    @throttle_key(lambda mode: mode)
    @handle_errors
    def set_hidmode(self, mode: HidMode):
        self.usb.send(struct.pack('< BB', 0x51, mode.value))
        self.hidmode.emit(mode)

    @Slot()
    @handle_errors
    def get_profile(self):
        response = self.usb.send(struct.pack('< B', 0x80))
        (profile,) = struct.unpack('< x B 30x', response)
        self.profile.emit(ProfileId(profile))

    @Slot(ProfileId)
    @throttle_key(lambda profile: profile)
    @handle_errors
    def set_profile(self, profile: ProfileId):
        self.usb.send(struct.pack('< BB', 0x81, profile.value))
        self.profile.emit(ProfileId(profile))
        for panel in PanelId:
            self.get_sensitivity(panel)
            self.get_ranges(panel)
            self.get_curve(panel)

    @Slot()
    @throttle_key(lambda panel: panel)
    @handle_errors
    def get_curve(self, panel: PanelId):
        response = self.usb.send(struct.pack('< BB', 0x86, panel.value))
        below, above, num_points = struct.unpack('< xx ffB', response[:11])
        span = response[11:][: (2 * num_points * 4)]
        coords = struct.unpack(f'< {2 * num_points}f', span)
        points = [CurvePoint(x, y) for x, y in itertools.batched(coords, n=2)]
        self.curve.emit(panel, Curve(CurveBand(below, above), points))

    @Slot(PanelId)
    @throttle_key(lambda panel: panel)
    @handle_errors
    def get_readings(self, panel: PanelId):
        response = self.usb.send(struct.pack('< BB', 0x87, panel.value))
        pressed, x, y, left, right = struct.unpack('< x BffHH 18x', response)
        self.readings.emit(Readings(panel, pressed != 0, x, y, (left, right)))

    @Slot(PanelId, int, CurvePoint)
    @throttle_key(lambda *args: args)
    @handle_errors
    def add_curve_point(self, panel: PanelId, index: int, p: CurvePoint):
        self.usb.send(struct.pack('< BBBff', 0x88, panel.value, index, p.x, p.y))

    @Slot(PanelId, Curve)
    @throttle_key(lambda panel: panel)
    @handle_errors
    def set_curve_point(self, panel: PanelId, index: int, p: CurvePoint):
        self.usb.send(struct.pack('< BBBff', 0x8A, panel.value, index, p.x, p.y))

    @Slot(PanelId)
    @throttle_key(lambda panel: panel)
    @handle_errors
    def reset_curve(self, panel: PanelId):
        self.usb.send(struct.pack('< BB', 0x8B, panel.value))
        self.get_curve(panel)

    @Slot()
    @throttle_key(lambda panel: panel)
    @handle_errors
    def get_sensitivity(self, panel: PanelId):
        response = self.usb.send(struct.pack('< BB', 0x90, panel.value))
        (sensitivity,) = struct.unpack('< x H 29x', response)
        self.sensitivity.emit(panel, Sensitivity(sensitivity))

    @Slot(PanelId, Sensitivity)
    @throttle_key(lambda panel, _: panel)
    @handle_errors
    def set_sensitivity(self, panel: PanelId, sensitivity: Sensitivity):
        self.usb.send(struct.pack('< BBH', 0x91, panel.value, sensitivity.sensitivity))

    @Slot(PanelId)
    @throttle_key(lambda panel, _: panel)
    @handle_errors
    def get_band(self, panel: PanelId):
        response = self.usb.send(struct.pack('< BB', 0x92, panel.value))
        below, above = struct.unpack('< x ff 15x', response)
        self.band.emit(panel, CurveBand(below, above))

    @Slot(PanelId, Sensitivity)
    @throttle_key(lambda panel, _: panel)
    @handle_errors
    def set_band(self, panel: PanelId, below: float, above: float):
        self.usb.send(struct.pack('< BBff', 0x93, panel.value, below, above))

    @Slot()
    @throttle_key(lambda panel: panel)
    @handle_errors
    def get_ranges(self, panel: PanelId):
        response = self.usb.send(struct.pack('< BB', 0x94, panel.value))
        lmin, lmax, rmin, rmax = struct.unpack('< x HHHH 23x', response)
        self.ranges.emit(panel, (SensorRange(lmin, lmax), SensorRange(rmin, rmax)))

    @Slot(PanelId, tuple)
    @throttle_key(lambda panel, _: panel)
    @handle_errors
    def set_ranges(self, panel: PanelId, ranges: tuple[SensorRange, SensorRange]):
        self.usb.send(
            struct.pack(
                '< BBHHHH',
                0x95,
                panel.value,
                ranges[0].min,
                ranges[0].max,
                ranges[1].min,
                ranges[1].max,
            )
        )

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
