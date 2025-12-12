import sys

from PySide6.QtCore import QMetaObject, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

import rc_resources  # noqa: F401
from datatypes import PanelId
from model import Model
from pad import Pad
from usb import Usb


def main():
    app = QGuiApplication(sys.argv)

    pad = Pad()
    model = Model()  # pyright: ignore[reportCallIssue]

    pad.alias.connect(model.pad_alias)
    pad.connected.connect(model.pad_connected)
    pad.disconnected.connect(model.pad_disconnected)
    pad.hidmode.connect(model.pad_hidmode)
    pad.profile.connect(model.pad_profile)
    pad.readings.connect(model.pad_readings)
    pad.ranges.connect(model.pad_ranges)

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
