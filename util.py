import functools
from typing import Any, Callable

from PySide6.QtCore import QObject, QTimer, Slot


def throttle_key(key_selector: Callable):
    def decorator[T](func: T) -> T:
        func._throttle_key = key_selector  # pyright: ignore[reportAttributeAccessIssue]
        return func

    return decorator


class Throttle(QObject):
    _queue: list[tuple[Callable, Any, list[Any]]]

    def __init__(self, target: QObject, parent: QObject | None = None):
        super().__init__(parent)
        self._queue = []

        def make_slot_wrapper(slot):
            if hasattr(slot, '_throttle_key'):

                @functools.wraps(slot)
                def wrapper(*args):
                    self._queue.append((slot, slot._throttle_key(*args), list(args)))
                    QTimer.singleShot(10, self._process_queue)

                return wrapper

            else:

                @functools.wraps(slot)
                def wrapper(*args):
                    self._queue.append((slot, None, list(args)))
                    QTimer.singleShot(10, self._process_queue)

                return wrapper

        for name in dir(target):
            value = getattr(target, name)
            if callable(value) and hasattr(value, '_slots'):
                wrapper = make_slot_wrapper(value)
                wrapper_slot = Slot()(wrapper)
                setattr(self, name, wrapper_slot)

        self.moveToThread(target.thread())

    @Slot()
    def _process_queue(self):
        queue, self._queue = self._queue, []
        for i, (slot, key, args) in enumerate(queue):
            if i + 1 >= len(queue) or queue[i + 1][1] != key:
                slot(*args)
