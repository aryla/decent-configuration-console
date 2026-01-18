# Decent Configuration Console

Unofficial configuration app for the BlueCombo Halfpad.
Runs on Linux and Windows.

Features:
- Display sensor values
- Change panel sensitivity
- Change sensor ranges
- Edit threshold curve
- Change hysteresis band width
- Switch profiles
- Change pad HID mode (joystick/keyboard/hidden)
- Change pad alias

Requires pad firmware version 0.0.4.
This app does not support upgrading pad firmware.

## Linux setup

1. Install `uv` and `libusb` with your distribution's package manager
2. Download or clone the repository
3. Copy [`71-bluecombo-halfpad.rules`](./71-bluecombo-halfpad.rules) to
   `/etc/udev/rules.d`
4. Run `uv run build.py`
5. Run `uv run main.py`

## Windows setup

1. Install
   [uv](https://docs.astral.sh/uv/getting-started/installation/)
2. Install [Zadig](https://zadig.akeo.ie/)
3. Use Zadig to replace the driver for "BlueCombo (Interface 1)" with
   WinUSB.

   **WARNING: BlueCombo Console will not recognize the pad anymore after
   this.**
5. Download or clone the repository
6. Download [libusb](https://github.com/libusb/libusb/releases) and
   place `libusb-1.0.dll` in the root of the repository
7. Run `uv run build.py`
8. Run `uv run main.py`
