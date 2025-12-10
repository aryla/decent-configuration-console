import functools

from PySide6.QtCore import QMetaObject, Qt


def SlotProxy[T](target: T) -> T:
    class SlotProxy:
        def __init__(self, target):
            for key in dir(target):
                value = getattr(target, key)
                if callable(value) and hasattr(value, '_slots'):

                    def helper(key):
                        def wrapper(*args, **kwargs):
                            return QMetaObject.invokeMethod(
                                target, key, Qt.ConnectionType.QueuedConnection, *args, **kwargs
                            )

                        return wrapper

                    wrapper = helper(key)
                    functools.update_wrapper(wrapper, value)
                    setattr(self, key, wrapper)

    return SlotProxy(target)  # pyright: ignore[reportReturnType]
