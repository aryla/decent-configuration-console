import random
import struct
import time

from PySide6.QtCore import QObject, QThread, QTimer, Signal, Slot

import usb
from datatypes import HidMode, PanelId, ProfileId, Readings, Sensitivity, SensorRange, SensorRanges


class Pad(QObject):
    alias = Signal(str)
    connected = Signal()
    disconnected = Signal()
    hidmode = Signal(HidMode)
    profile = Signal(ProfileId)
    readings = Signal(Readings)
    ranges = Signal(SensorRanges)
    error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.usb = None

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
    def connect(self):
        if self.usb is None:
            self.usb = usb.Usb()

        try:
            self.usb.connect()
            self.connected.emit()
            self.usb.send(struct.pack('< B 30x', 0x00))
            self.get_alias()
            self.start_polling()
        except usb.Error as e:
            self.error.emit(str(e))
            self.usb.disconnect()
            self.disconnected.emit()
            return

    @Slot()
    def revert(self):
        pass

    @Slot()
    def save(self):
        pass

    @Slot()
    def get_alias(self):
        alias = (
            self.usb.send(struct.pack('< B 30x', 0x10))[1:-1]
            .decode('utf-8', errors='replace')
            .strip('\x00')
        )
        self.alias.emit(alias)

    @Slot()
    def get_hidmode(self):
        pass

    @Slot(HidMode)
    def set_hidmode(self, mode: HidMode):
        pass

    @Slot(ProfileId)
    def set_profile(self, profile: ProfileId):
        time.sleep(1)

    @Slot(PanelId, tuple)
    def set_range(self, panel: PanelId, ranges: tuple[SensorRange, SensorRange]):
        time.sleep(1)

    @Slot(PanelId, Sensitivity)
    def set_sensitivity(self, panel: PanelId, sensitivity: Sensitivity):
        time.sleep(1)

    @Slot()
    def start_polling(self):
        self.poll_timer.start()

    @Slot()
    def stop_polling(self):
        self.poll_timer.stop()

    def _poll(self):
        print('Polling pad')
        for panel in PanelId:
            response = self.usb.send(struct.pack('< BB 29x', 0x87, panel.value))
            pressed, x, y, left, right = struct.unpack('< x BffHH 18x', response)
            self.readings.emit(Readings(panel, pressed != 0, x, y, (left, right)))

    @Slot()
    def quit(self):
        self._thread.quit()
