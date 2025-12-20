import sys

from PySide6.QtCore import QMetaObject, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

import rc_resources  # noqa: F401
from model import Model
from pad import Pad
from util import Throttle


def main():
    app = QGuiApplication(sys.argv)

    pad = Pad()
    model = Model()

    pad.alias.connect(model.pad_alias)
    pad.band.connect(model.pad_band)
    pad.changes.connect(model.pad_changes)
    pad.connected.connect(model.pad_connected)
    pad.curve.connect(model.pad_curve)
    pad.disconnected.connect(model.pad_disconnected)
    pad.error.connect(model.pad_error)
    pad.hidmode.connect(model.pad_hidmode)
    pad.profile.connect(model.pad_profile)
    pad.ranges.connect(model.pad_ranges)
    pad.readings.connect(model.pad_readings)
    pad.sensitivity.connect(model.pad_sensitivity)
    pad.serial.connect(model.pad_serial)

    throttle = Throttle(pad)
    model.alias_set.connect(throttle.set_alias)
    model.changes_reverted.connect(throttle.revert_changes)
    model.changes_saved.connect(throttle.save_changes)
    model.curve_band_set.connect(throttle.set_band)
    model.curve_point_added.connect(throttle.add_curve_point)
    model.curve_point_moved.connect(throttle.set_curve_point)
    model.curve_reset.connect(throttle.reset_curve)
    model.curve_set.connect(throttle.set_curve)
    model.do_connect.connect(throttle.connect)
    model.do_disconnect.connect(throttle.disconnect)
    model.hidmode_set.connect(throttle.set_hidmode)
    model.profile_set.connect(throttle.set_profile)
    model.range_set.connect(throttle.set_ranges)
    model.sensitivity_set.connect(throttle.set_sensitivity)

    engine = QQmlApplicationEngine()
    engine.setInitialProperties({'model': model})
    engine.load(':/ui/Main.qml')
    if not engine.rootObjects():
        return -1

    QMetaObject.invokeMethod(pad, 'connect', Qt.ConnectionType.QueuedConnection)  # pyright: ignore[reportCallIssue, reportArgumentType]

    try:
        return app.exec()
    finally:
        QMetaObject.invokeMethod(pad, 'quit', Qt.ConnectionType.QueuedConnection)  # pyright: ignore[reportCallIssue, reportArgumentType]
        del engine


if __name__ == '__main__':
    sys.exit(main())
