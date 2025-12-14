from ctypes import (
    CDLL,
    POINTER,
    c_char,
    c_char_p,
    c_int,
    c_size_t,
    c_ssize_t,
    c_uint,
    c_uint8,
    c_uint16,
    c_uint32,
    c_void_p,
    c_voidp,
    create_string_buffer,
    pointer,
)
from datetime import timedelta
from typing import Sequence


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
    context: c_voidp | None
    device: c_voidp | None
    libusb: CDLL

    CONFIGURATION = 1
    INTERFACE = 2
    ENDPOINT_IN = c_uint8(0x83)
    ENDPOINT_OUT = c_uint8(0x03)

    def __init__(self):
        self.context = c_void_p()
        self.device = None
        self.libusb = CDLL('libusb-1.0.so.0')
        Usb._setup_types(self.libusb)
        self.libusb.libusb_init(pointer(self.context))

    def connect(self):
        self.disconnect()
        self.device = self.libusb.libusb_open_device_with_vid_pid(self.context, 0x0483, 0x571B)
        if self.device is None:
            raise NoDeviceError('No pad connected.')

        active_config = c_int(-1)
        self.libusb.libusb_get_configuration(self.device, pointer(active_config))
        if active_config.value != self.CONFIGURATION:
            self.libusb.libusb_set_configuration(self.device, self.CONFIGURATION)

        try:
            self.libusb.libusb_detach_kernel_driver(self.device, self.INTERFACE)
        except NotFoundError:
            pass

        # Check configuration after claiming the interface.
        # https://libusb.sourceforge.io/api-1.0/libusb_caveats.html
        self.libusb.libusb_claim_interface(self.device, self.INTERFACE)
        self.libusb.libusb_get_configuration(self.device, pointer(active_config))
        if active_config.value != self.CONFIGURATION:
            raise OtherError('Wrong configuration after claiming interface.')

    def disconnect(self):
        if self.device is None:
            return
        try:
            self.libusb.libusb_release_interface(self.device, self.INTERFACE)
        except Error:
            pass
        self.libusb.libusb_close(self.device)
        self.device = None

    def bulk_write(self, data: bytes, timeout: timedelta | None = None) -> None:
        if len(data) > 31:
            raise InvalidParamError('Request too long.')
        if self.device is None:
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
        if self.device is None:
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
        self.libusb.libusb_exit(self.context)
        self.context = None
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

        def Bool(value: int):
            return value != 0

        libusb.libusb_init.restype = LibusbResult
        libusb.libusb_init.argtypes = [POINTER(c_voidp)]
        libusb.libusb_init_context.restype = LibusbResult
        libusb.libusb_init_context.argtypes = [POINTER(c_voidp), c_voidp, c_int]
        libusb.libusb_exit.restype = None
        libusb.libusb_exit.argtypes = [c_voidp]
        libusb.libusb_set_debug.restype = None
        libusb.libusb_set_debug.argtypes = [c_voidp, c_int]
        libusb.libusb_set_log_cb.restype = None
        # libusb.libusb_set_log_cb.argtypes = [c_voidp, libusb_log_cb cb, c_int]
        libusb.libusb_get_version.restype = c_voidp
        libusb.libusb_get_version.argtypes = []
        libusb.libusb_has_capability.restype = Bool
        libusb.libusb_has_capability.argtypes = [c_uint32]
        libusb.libusb_error_name.restype = c_char_p
        libusb.libusb_error_name.argtypes = [c_int]
        libusb.libusb_setlocale.restype = LibusbResult
        libusb.libusb_setlocale.argtypes = [c_char_p]
        libusb.libusb_strerror.restype = c_char_p
        libusb.libusb_strerror.argtypes = [c_int]
        libusb.libusb_get_device_list.restype = c_ssize_t
        libusb.libusb_get_device_list.argtypes = [c_voidp, c_voidp]
        libusb.libusb_free_device_list.restype = None
        libusb.libusb_free_device_list.argtypes = [c_voidp, c_int]
        libusb.libusb_ref_device.restype = c_voidp
        libusb.libusb_ref_device.argtypes = [c_voidp]
        libusb.libusb_unref_device.restype = None
        libusb.libusb_unref_device.argtypes = [c_voidp]
        libusb.libusb_get_configuration.restype = LibusbResult
        libusb.libusb_get_configuration.argtypes = [c_voidp, c_voidp]
        libusb.libusb_get_device_descriptor.restype = LibusbResult
        libusb.libusb_get_device_descriptor.argtypes = [c_voidp, c_voidp]
        libusb.libusb_get_active_config_descriptor.restype = LibusbResult
        libusb.libusb_get_active_config_descriptor.argtypes = [c_voidp, c_voidp]
        libusb.libusb_get_config_descriptor.restype = LibusbResult
        libusb.libusb_get_config_descriptor.argtypes = [c_voidp, c_uint8, c_voidp]
        libusb.libusb_get_config_descriptor_by_value.restype = LibusbResult
        libusb.libusb_get_config_descriptor_by_value.argtypes = [c_voidp, c_uint8, c_voidp]
        libusb.libusb_free_config_descriptor.restype = None
        libusb.libusb_free_config_descriptor.argtypes = [c_voidp]
        libusb.libusb_get_ss_endpoint_companion_descriptor.restype = LibusbResult
        libusb.libusb_get_ss_endpoint_companion_descriptor.argtypes = [
            c_voidp,
            c_voidp,
            c_voidp,
        ]
        libusb.libusb_free_ss_endpoint_companion_descriptor.restype = None
        libusb.libusb_free_ss_endpoint_companion_descriptor.argtypes = [c_voidp]
        libusb.libusb_get_bos_descriptor.restype = LibusbResult
        libusb.libusb_get_bos_descriptor.argtypes = [c_voidp, c_voidp]
        libusb.libusb_free_bos_descriptor.restype = None
        libusb.libusb_free_bos_descriptor.argtypes = [c_voidp]
        libusb.libusb_get_usb_2_0_extension_descriptor.restype = LibusbResult
        libusb.libusb_get_usb_2_0_extension_descriptor.argtypes = [c_voidp, c_voidp, c_voidp]
        libusb.libusb_free_usb_2_0_extension_descriptor.restype = None
        libusb.libusb_free_usb_2_0_extension_descriptor.argtypes = [c_voidp]
        libusb.libusb_get_ss_usb_device_capability_descriptor.restype = LibusbResult
        libusb.libusb_get_ss_usb_device_capability_descriptor.argtypes = [
            c_voidp,
            c_voidp,
            c_voidp,
        ]
        libusb.libusb_free_ss_usb_device_capability_descriptor.restype = None
        libusb.libusb_free_ss_usb_device_capability_descriptor.argtypes = [c_voidp]
        libusb.libusb_get_ssplus_usb_device_capability_descriptor.restype = LibusbResult
        libusb.libusb_get_ssplus_usb_device_capability_descriptor.argtypes = [
            c_voidp,
            c_voidp,
            c_voidp,
        ]
        libusb.libusb_free_ssplus_usb_device_capability_descriptor.restype = None
        libusb.libusb_free_ssplus_usb_device_capability_descriptor.argtypes = [c_voidp]
        libusb.libusb_get_container_id_descriptor.restype = LibusbResult
        libusb.libusb_get_container_id_descriptor.argtypes = [c_voidp, c_voidp, c_voidp]
        libusb.libusb_free_container_id_descriptor.restype = None
        libusb.libusb_free_container_id_descriptor.argtypes = [c_voidp]
        libusb.libusb_get_platform_descriptor.restype = LibusbResult
        libusb.libusb_get_platform_descriptor.argtypes = [c_voidp, c_voidp, c_voidp]
        libusb.libusb_free_platform_descriptor.restype = None
        libusb.libusb_free_platform_descriptor.argtypes = [c_voidp]
        libusb.libusb_get_bus_number.restype = c_uint8
        libusb.libusb_get_bus_number.argtypes = [c_voidp]
        libusb.libusb_get_port_number.restype = c_uint8
        libusb.libusb_get_port_number.argtypes = [c_voidp]
        libusb.libusb_get_port_numbers.restype = LibusbResult
        libusb.libusb_get_port_numbers.argtypes = [c_voidp, POINTER(c_char), c_int]
        libusb.libusb_get_port_path.restype = LibusbResult
        libusb.libusb_get_port_path.argtypes = [c_voidp, c_voidp, POINTER(c_char), c_uint8]
        libusb.libusb_get_parent.restype = c_voidp
        libusb.libusb_get_parent.argtypes = [c_voidp]
        libusb.libusb_get_device_address.restype = c_uint8
        libusb.libusb_get_device_address.argtypes = [c_voidp]
        libusb.libusb_get_device_speed.restype = LibusbResult
        libusb.libusb_get_device_speed.argtypes = [c_voidp]
        libusb.libusb_get_max_packet_size.restype = LibusbResult
        libusb.libusb_get_max_packet_size.argtypes = [c_voidp, c_uint8]
        libusb.libusb_get_max_iso_packet_size.restype = LibusbResult
        libusb.libusb_get_max_iso_packet_size.argtypes = [c_voidp, c_uint8]
        libusb.libusb_get_max_alt_packet_size.restype = LibusbResult
        libusb.libusb_get_max_alt_packet_size.argtypes = [c_voidp, c_int, c_int, c_uint8]
        libusb.libusb_get_interface_association_descriptors.restype = LibusbResult
        libusb.libusb_get_interface_association_descriptors.argtypes = [
            c_voidp,
            c_uint8,
            c_voidp,
        ]
        libusb.libusb_get_active_interface_association_descriptors.restype = LibusbResult
        libusb.libusb_get_active_interface_association_descriptors.argtypes = [
            c_voidp,
            c_voidp,
        ]
        libusb.libusb_free_interface_association_descriptors.restype = None
        libusb.libusb_free_interface_association_descriptors.argtypes = [c_voidp]
        libusb.libusb_wrap_sys_device.restype = LibusbResult
        libusb.libusb_wrap_sys_device.argtypes = [c_voidp, c_voidp, c_voidp]
        libusb.libusb_open.restype = LibusbResult
        libusb.libusb_open.argtypes = [c_voidp, c_voidp]
        libusb.libusb_close.restype = None
        libusb.libusb_close.argtypes = [c_voidp]
        libusb.libusb_get_device.restype = c_voidp
        libusb.libusb_get_device.argtypes = [c_voidp]
        libusb.libusb_set_configuration.restype = LibusbResult
        libusb.libusb_set_configuration.argtypes = [c_voidp, c_int]
        libusb.libusb_claim_interface.restype = LibusbResult
        libusb.libusb_claim_interface.argtypes = [c_voidp, c_int]
        libusb.libusb_release_interface.restype = LibusbResult
        libusb.libusb_release_interface.argtypes = [c_voidp, c_int]
        libusb.libusb_open_device_with_vid_pid.restype = c_voidp
        libusb.libusb_open_device_with_vid_pid.argtypes = [c_voidp, c_uint16, c_uint16]
        libusb.libusb_set_interface_alt_setting.restype = LibusbResult
        libusb.libusb_set_interface_alt_setting.argtypes = [c_voidp, c_int, c_int]
        libusb.libusb_clear_halt.restype = LibusbResult
        libusb.libusb_clear_halt.argtypes = [c_voidp, c_uint8]
        libusb.libusb_reset_device.restype = LibusbResult
        libusb.libusb_reset_device.argtypes = [c_voidp]
        libusb.libusb_alloc_streams.restype = LibusbResult
        libusb.libusb_alloc_streams.argtypes = [c_voidp, c_uint32, POINTER(c_char), c_int]
        libusb.libusb_free_streams.restype = LibusbResult
        libusb.libusb_free_streams.argtypes = [c_voidp, POINTER(c_char), c_int]
        libusb.libusb_dev_mem_alloc.restype = POINTER(c_char)
        libusb.libusb_dev_mem_alloc.argtypes = [c_voidp, c_size_t]
        libusb.libusb_dev_mem_free.restype = LibusbResult
        libusb.libusb_dev_mem_free.argtypes = [c_voidp, POINTER(c_char), c_size_t]
        libusb.libusb_kernel_driver_active.restype = LibusbResult
        libusb.libusb_kernel_driver_active.argtypes = [c_voidp, c_int]
        libusb.libusb_detach_kernel_driver.restype = LibusbResult
        libusb.libusb_detach_kernel_driver.argtypes = [c_voidp, c_int]
        libusb.libusb_attach_kernel_driver.restype = LibusbResult
        libusb.libusb_attach_kernel_driver.argtypes = [c_voidp, c_int]
        libusb.libusb_set_auto_detach_kernel_driver.restype = LibusbResult
        libusb.libusb_set_auto_detach_kernel_driver.argtypes = [c_voidp, c_int]
        libusb.libusb_submit_transfer.restype = LibusbResult
        libusb.libusb_submit_transfer.argtypes = [c_voidp]
        libusb.libusb_cancel_transfer.restype = LibusbResult
        libusb.libusb_cancel_transfer.argtypes = [c_voidp]
        libusb.libusb_free_transfer.restype = None
        libusb.libusb_free_transfer.argtypes = [c_voidp]
        libusb.libusb_transfer_set_stream_id.restype = None
        libusb.libusb_transfer_set_stream_id.argtypes = [c_voidp, c_uint32]
        libusb.libusb_transfer_get_stream_id.restype = c_uint32
        libusb.libusb_transfer_get_stream_id.argtypes = [c_voidp]
        libusb.libusb_control_transfer.restype = LibusbResult
        libusb.libusb_control_transfer.argtypes = [
            c_voidp,
            c_uint8,
            c_uint8,
            c_uint16,
            c_uint16,
            POINTER(c_char),
            c_uint16,
            c_uint,
        ]
        libusb.libusb_bulk_transfer.restype = LibusbResult
        libusb.libusb_bulk_transfer.argtypes = [
            c_voidp,
            c_uint8,
            POINTER(c_char),
            c_int,
            POINTER(c_int),
            c_uint,
        ]
        libusb.libusb_interrupt_transfer.restype = LibusbResult
        libusb.libusb_interrupt_transfer.argtypes = [
            c_voidp,
            c_uint8,
            POINTER(c_char),
            c_int,
            POINTER(c_int),
            c_uint,
        ]
        libusb.libusb_get_string_descriptor_ascii.restype = LibusbResult
        libusb.libusb_get_string_descriptor_ascii.argtypes = [
            c_voidp,
            c_uint8,
            POINTER(c_char),
            c_int,
        ]
        libusb.libusb_try_lock_events.restype = LibusbResult
        libusb.libusb_try_lock_events.argtypes = [c_voidp]
        libusb.libusb_lock_events.restype = None
        libusb.libusb_lock_events.argtypes = [c_voidp]
        libusb.libusb_unlock_events.restype = None
        libusb.libusb_unlock_events.argtypes = [c_voidp]
        libusb.libusb_event_handling_ok.restype = LibusbResult
        libusb.libusb_event_handling_ok.argtypes = [c_voidp]
        libusb.libusb_event_handler_active.restype = LibusbResult
        libusb.libusb_event_handler_active.argtypes = [c_voidp]
        libusb.libusb_interrupt_event_handler.restype = None
        libusb.libusb_interrupt_event_handler.argtypes = [c_voidp]
        libusb.libusb_lock_event_waiters.restype = None
        libusb.libusb_lock_event_waiters.argtypes = [c_voidp]
        libusb.libusb_unlock_event_waiters.restype = None
        libusb.libusb_unlock_event_waiters.argtypes = [c_voidp]
        libusb.libusb_wait_for_event.restype = LibusbResult
        libusb.libusb_wait_for_event.argtypes = [c_voidp, c_voidp]
        libusb.libusb_handle_events_timeout.restype = LibusbResult
        libusb.libusb_handle_events_timeout.argtypes = [c_voidp, c_voidp]
        libusb.libusb_handle_events_timeout_completed.restype = LibusbResult
        libusb.libusb_handle_events_timeout_completed.argtypes = [
            c_voidp,
            c_voidp,
            POINTER(c_int),
        ]
        libusb.libusb_handle_events.restype = LibusbResult
        libusb.libusb_handle_events.argtypes = [c_voidp]
        libusb.libusb_handle_events_completed.restype = LibusbResult
        libusb.libusb_handle_events_completed.argtypes = [c_voidp, POINTER(c_int)]
        libusb.libusb_handle_events_locked.restype = LibusbResult
        libusb.libusb_handle_events_locked.argtypes = [c_voidp, c_voidp]
        libusb.libusb_pollfds_handle_timeouts.restype = LibusbResult
        libusb.libusb_pollfds_handle_timeouts.argtypes = [c_voidp]
        libusb.libusb_get_next_timeout.restype = LibusbResult
        libusb.libusb_get_next_timeout.argtypes = [c_voidp, c_voidp]
        libusb.libusb_get_pollfds.restype = c_voidp
        libusb.libusb_get_pollfds.argtypes = [c_voidp]
        libusb.libusb_free_pollfds.restype = None
        libusb.libusb_free_pollfds.argtypes = [c_voidp]
        libusb.libusb_set_pollfd_notifiers.restype = None
        # libusb.libusb_set_pollfd_notifiers.argtypes = [c_voidp, libusb_pollfd_added_cb added_cb, libusb_pollfd_removed_cb removed_cb, c_voidp]
        libusb.libusb_hotplug_register_callback.restype = LibusbResult
        # libusb.libusb_hotplug_register_callback.argtypes = [c_voidp, c_int, c_int, c_int, c_int, c_int, libusb_hotplug_callback_fn cb_fn, c_voidp, c_voidp]
        libusb.libusb_hotplug_deregister_callback.restype = None
        # libusb.libusb_hotplug_deregister_callback.argtypes = [c_voidp, libusb_hotplug_callback_handle callback_handle]
        libusb.libusb_hotplug_get_user_data.restype = c_voidp
        # libusb.libusb_hotplug_get_user_data.argtypes = [c_voidp, libusb_hotplug_callback_handle callback_handle]
        libusb.libusb_set_option.restype = LibusbResult
        # self.libusb.libusb_set_option.argtypes = [c_voidp, enum libusb_option option, ...]
