import os
import sys
from ctypes import (
    CDLL,
    POINTER,
    Structure,
    c_char,
    c_char_p,
    c_int,
    c_ssize_t,
    c_uint,
    c_uint8,
    c_uint16,
    c_void_p,
    c_voidp,
    create_string_buffer,
    pointer,
)
from datetime import timedelta
from typing import Sequence


class DeviceDescriptor(Structure):
    _fields_ = [
        ('bLength', c_uint8),
        ('bDescriptorType', c_uint8),
        ('bcdUSB', c_uint16),
        ('bDeviceClass', c_uint8),
        ('bDeviceSubClass', c_uint8),
        ('bDeviceProtocol', c_uint8),
        ('bMaxPacketSize0', c_uint8),
        ('idVendor', c_uint16),
        ('idProduct', c_uint16),
        ('bcdDevice', c_uint16),
        ('iManufacturer', c_uint8),
        ('iProduct', c_uint8),
        ('iSerialNumber', c_uint8),
        ('bNumConfigurations', c_uint8),
    ]


class Error(Exception):
    def __init__(self, *args):
        super().__init__(*args)

    @staticmethod
    def _from_code(libusb: CDLL, code: int):
        message = 'libusb: ' + libusb.libusb_strerror(code).decode('utf-8', errors='replace')
        cls = {
            -1: IOError,
            -2: InvalidParamError,
            -3: AccessError,
            -4: NoDeviceError,
            -5: NotFoundError,
            -6: BusyError,
            -7: TimeoutError,
            -8: OverflowError,
            -9: PipeError,
            -10: InterruptedError,
            -11: NoMemError,
            -12: NotSupportedError,
        }.get(code, OtherError)
        return cls(message)


# fmt: off
class IOError(Error): pass
class InvalidParamError(Error): pass
class AccessError(Error): pass
class NoDeviceError(Error): pass
class NotFoundError(Error): pass
class BusyError(Error): pass
class TimeoutError(Error): pass
class OverflowError(Error): pass
class PipeError(Error): pass
class InterruptedError(Error): pass
class NoMemError(Error): pass
class NotSupportedError(Error): pass
class OtherError(Error): pass
# fmt: on


class Usb:
    context: c_voidp
    device: c_voidp
    libusb: CDLL

    CONFIGURATION = 1
    INTERFACE = 2
    ENDPOINT_IN = c_uint8(0x83)
    ENDPOINT_OUT = c_uint8(0x03)
    VENDOR_ID = 0x0483
    PRODUCT_ID = 0x571B

    def __init__(self):
        self.context = c_void_p()
        self.device = c_void_p()
        if sys.platform == 'win32':
            self.libusb = CDLL(os.path.dirname(__file__) + '\\libusb-1.0.dll')
        else:
            self.libusb = CDLL('libusb-1.0.so.0')
        Usb._setup_types(self.libusb)

    def connect(self):
        self.disconnect()
        self.libusb.libusb_init(pointer(self.context))

        device_list = POINTER(c_voidp)()
        num_devices = self.libusb.libusb_get_device_list(None, pointer(device_list))
        if num_devices < 0:
            raise OtherError('Error enumerating devices.')

        try:
            for i in range(num_devices):
                descriptor = DeviceDescriptor()
                self.libusb.libusb_get_device_descriptor(device_list[i], pointer(descriptor))
                if (
                    descriptor.idVendor == self.VENDOR_ID
                    and descriptor.idProduct == self.PRODUCT_ID
                ):
                    self.libusb.libusb_open(device_list[i], pointer(self.device))
                    break
            else:
                raise NoDeviceError('No pad connected.')
        finally:
            self.libusb.libusb_free_device_list(device_list, 1)

        active_config = c_int(-1)
        self.libusb.libusb_get_configuration(self.device, pointer(active_config))
        if active_config.value != self.CONFIGURATION:
            self.libusb.libusb_set_configuration(self.device, self.CONFIGURATION)

        try:
            # Raises a NotFoundError if the kernel driver is already detached.
            # Raises a NotSupportedError on Windows.
            self.libusb.libusb_detach_kernel_driver(self.device, self.INTERFACE)
        except (NotFoundError, NotSupportedError):
            pass

        # Check configuration after claiming the interface.
        # https://libusb.sourceforge.io/api-1.0/libusb_caveats.html
        self.libusb.libusb_claim_interface(self.device, self.INTERFACE)
        self.libusb.libusb_get_configuration(self.device, pointer(active_config))
        if active_config.value != self.CONFIGURATION:
            raise OtherError('Wrong configuration after claiming interface.')

    def disconnect(self):
        if self.device:
            try:
                self.libusb.libusb_release_interface(self.device, self.INTERFACE)
            except Error:
                pass
            self.libusb.libusb_close(self.device)
            self.device = c_void_p()

        if self.context:
            self.libusb.libusb_exit(self.context)
            self.context = c_void_p()

    def bulk_write(self, data: bytes, timeout: timedelta | None = None) -> None:
        if len(data) > 31:
            raise InvalidParamError('Request too long.')
        if not self.device:
            raise NoDeviceError('No pad connected.')
        buffer = create_string_buffer(data, 32)
        buffer[-1] = self._checksum(buffer[:-1])
        timeout_ms = 0 if timeout is None else int(1000 * timeout.total_seconds())
        transferred = c_int(-1)
        self.libusb.libusb_bulk_transfer(
            self.device,
            self.ENDPOINT_OUT,
            buffer,
            len(buffer),
            pointer(transferred),
            c_uint(timeout_ms),
        )
        if transferred.value != len(buffer):
            raise IOError('Partial write.')

    def bulk_read(self, timeout: timedelta | None = None) -> bytes:
        if not self.device:
            raise NoDeviceError('No pad connected.')
        timeout_ms = 0 if timeout is None else int(1000 * timeout.total_seconds())
        transferred = c_int(-1)
        buffer = create_string_buffer(32)
        self.libusb.libusb_bulk_transfer(
            self.device,
            self.ENDPOINT_IN,
            buffer,
            len(buffer),
            pointer(transferred),
            c_uint(timeout_ms),
        )
        if transferred.value != len(buffer):
            raise IOError('Partial read.')
        if int.from_bytes(buffer[-1]) != self._checksum(buffer[:-1]):
            raise IOError('Checksum failure.')
        return bytes(buffer)

    def send(self, request: bytes, timeout: timedelta | None = None) -> bytes:
        self.bulk_write(request, timeout)
        buffer = self.bulk_read(timeout)

        if buffer[0] == 0x41:
            return buffer
        elif buffer[0] == 0x45:
            response = bytearray(buffer[:-1])
            num_packets = buffer[1]
            if num_packets > 2:
                raise OtherError('Unexpected data received.')
            for packet_number in range(1, num_packets):
                buffer = self.bulk_read(timeout)
                if buffer[0] != packet_number:
                    raise OtherError('Unexpected data received.')
                response += buffer[1:-1]
            return bytes(response)
        elif buffer[0] == 0x4E:
            raise OtherError('Pad responded with an error.')
        else:
            raise OtherError('Unexpected data received.')

    def __del__(self):
        self.disconnect()
        del self.libusb

    @staticmethod
    def _checksum(data: Sequence[int]) -> int:
        result = 0xFFFFFFFF
        for b in data:
            result ^= b
            for _ in range(32):
                if result & 0x80000000 == 0:
                    result = (result << 1) & 0xFFFFFFFF
                else:
                    result = ((result << 1) ^ 0x04C11DB7) & 0xFFFFFFFF
        return result & 0xFF

    @staticmethod
    def _setup_types(libusb):
        def LibusbResult(value: int):
            if value != 0:
                raise Error._from_code(libusb, value)
            return None

        libusb.libusb_init.restype = LibusbResult
        libusb.libusb_init.argtypes = [POINTER(c_voidp)]
        libusb.libusb_exit.restype = None
        libusb.libusb_exit.argtypes = [c_voidp]
        libusb.libusb_strerror.restype = c_char_p
        libusb.libusb_strerror.argtypes = [c_int]
        libusb.libusb_get_device_list.restype = c_ssize_t
        libusb.libusb_get_device_list.argtypes = [c_voidp, c_voidp]
        libusb.libusb_free_device_list.restype = None
        libusb.libusb_free_device_list.argtypes = [c_voidp, c_int]
        libusb.libusb_get_configuration.restype = LibusbResult
        libusb.libusb_get_configuration.argtypes = [c_voidp, c_voidp]
        libusb.libusb_get_device_descriptor.restype = LibusbResult
        libusb.libusb_get_device_descriptor.argtypes = [c_voidp, c_voidp]
        libusb.libusb_open.restype = LibusbResult
        libusb.libusb_open.argtypes = [c_voidp, c_voidp]
        libusb.libusb_close.restype = None
        libusb.libusb_close.argtypes = [c_voidp]
        libusb.libusb_set_configuration.restype = LibusbResult
        libusb.libusb_set_configuration.argtypes = [c_voidp, c_int]
        libusb.libusb_claim_interface.restype = LibusbResult
        libusb.libusb_claim_interface.argtypes = [c_voidp, c_int]
        libusb.libusb_release_interface.restype = LibusbResult
        libusb.libusb_release_interface.argtypes = [c_voidp, c_int]
        libusb.libusb_detach_kernel_driver.restype = LibusbResult
        libusb.libusb_detach_kernel_driver.argtypes = [c_voidp, c_int]
        libusb.libusb_bulk_transfer.restype = LibusbResult
        libusb.libusb_bulk_transfer.argtypes = [
            c_voidp,
            c_uint8,
            POINTER(c_char),
            c_int,
            POINTER(c_int),
            c_uint,
        ]
