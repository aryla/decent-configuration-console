import sys

from PySide6.QtCore import QObject, QThread, QTimer, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

import rc_resources  # noqa: F401
from model import Model  # noqa: F401
from util import SlotProxy


class Pad(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(1000)
        self.poll_timer.timeout.connect(self._poll)

        self._thread = QThread(self)
        self._thread.setObjectName('Pad thread')
        self._thread.finished.connect(self.deleteLater)
        self.moveToThread(self._thread)
        self._thread.start()

    @Slot()
    def start_polling(self):
        print('start polling on ', QThread.currentThread().objectName())
        self.poll_timer.start()

    @Slot()
    def stop_polling(self):
        print('stop polling on ', QThread.currentThread().objectName())
        self.poll_timer.stop()

    @Slot()
    def stop(self):
        print('stop on ', QThread.currentThread().objectName())
        self._thread.quit()

    def _poll(self):
        print('poll on ', QThread.currentThread().objectName())
        print('Hello from pad')


def main():
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    engine.load(':/ui/Main.qml')

    if not engine.rootObjects():
        sys.exit(-1)

    pad = Pad()
    proxy = SlotProxy(pad)
    proxy.start_polling()
    try:
        return app.exec()
    finally:
        proxy.stop()


if __name__ == '__main__':
    sys.exit(main())
