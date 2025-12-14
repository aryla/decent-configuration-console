import functools
import struct

from PySide6.QtCore import QObject, QThread, QTimer, Signal, Slot

import usb
from datatypes import HidMode, PanelId, ProfileId, Readings, Sensitivity, SensorRange
from util import throttle_key


def handle_errors(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            func(self, *args, **kwargs)
        except usb.Error as e:
            print(str(e))
            self.error.emit(str(e))

    return wrapper


class Pad(QObject):
    alias = Signal(str)
    connected = Signal()
    disconnected = Signal()
    hidmode = Signal(HidMode)
    profile = Signal(ProfileId)
    readings = Signal(Readings)
    ranges = Signal(PanelId, tuple)
    sensitivity = Signal(PanelId, Sensitivity)
    error = Signal(str)

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
            self.usb.connect()
            self.connected.emit()
            self.usb.send(struct.pack('< B', 0x00))
            self.get_alias()
            for panel in PanelId:
                self.get_sensitivity(panel)
                self.get_ranges(panel)
            self.start_polling()
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
    def revert(self):
        pass

    @Slot()
    @handle_errors
    def save(self):
        pass

    @Slot()
    @handle_errors
    def get_alias(self):
        response = self.usb.send(struct.pack('< B', 0x10))
        (alias,) = struct.unpack('< x 30s x', response)
        alias = alias.decode('utf-8', errors='replace').strip('\x00')
        self.alias.emit(alias)

    @Slot()
    @handle_errors
    def get_hidmode(self):
        _response = self.usb.send(struct.pack('< B', 0x50))
        # TODO

    @Slot()
    @throttle_key(lambda panel: panel)
    @handle_errors
    def get_ranges(self, panel):
        response = self.usb.send(struct.pack('< BB', 0x94, panel.value))
        lmin, lmax, rmin, rmax = struct.unpack('< x HHHH 23x', response)
        self.ranges.emit(panel, (SensorRange(lmin, lmax), SensorRange(rmin, rmax)))

    @Slot()
    @throttle_key(lambda panel: panel)
    @handle_errors
    def get_sensitivity(self, panel):
        response = self.usb.send(struct.pack('< BB', 0x90, panel.value))
        (sensitivity,) = struct.unpack('< x H 29x', response)
        self.sensitivity.emit(panel, Sensitivity(sensitivity))

    @Slot(HidMode)
    @throttle_key(lambda mode: mode)
    @handle_errors
    def set_hidmode(self, mode: HidMode):
        self.usb.send(struct.pack('< BB', 0x51, mode.value))

    @Slot(ProfileId)
    @throttle_key(lambda profile: profile)
    @handle_errors
    def set_profile(self, profile: ProfileId):
        self.usb.send(struct.pack('< BB', 0x81, profile.value))

    @Slot(PanelId, tuple)
    @throttle_key(lambda panel, _: panel)
    @handle_errors
    def set_range(self, panel: PanelId, ranges: tuple[SensorRange, SensorRange]):
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

    @Slot(PanelId, Sensitivity)
    @throttle_key(lambda panel, _: panel)
    @handle_errors
    def set_sensitivity(self, panel: PanelId, sensitivity: Sensitivity):
        self.usb.send(struct.pack('< BBH', 0x91, panel.value, sensitivity.sensitivity))

    @Slot()
    def start_polling(self):
        self.poll_timer.start()

    @Slot()
    def stop_polling(self):
        self.poll_timer.stop()

    def _poll(self):
        print('Polling pad')
        for panel in PanelId:
            response = self.usb.send(struct.pack('< BB', 0x87, panel.value))
            pressed, x, y, left, right = struct.unpack('< x BffHH 18x', response)
            self.readings.emit(Readings(panel, pressed != 0, x, y, (left, right)))

    @Slot()
    def quit(self):
        self._thread.quit()
