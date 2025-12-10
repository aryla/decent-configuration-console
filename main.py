import sys
from typing import List

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

import rc_resources  # noqa: F401
from model import Model  # noqa: F401


def main():
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    engine.load(':/ui/Main.qml')

    if not engine.rootObjects():
        sys.exit(-1)

    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
