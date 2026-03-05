#!/usr/bin/env python3

"""
Touchscreen calibration helper for piMacroScreen.

This script reads raw EV_ABS events from an evdev touchscreen device and
computes calibration endpoints compatible with macroKeys.py:

    tftOrig = (x_min, y_max)
    tftEnd  = (x_max, y_min)

Why this format?
- macroKeys.py expects one axis may be inverted depending on hardware/rotation.
- Using the measured extrema lets existing mapping logic keep working.

Usage:
    sudo python3 touchscreen_calibrate.py
    sudo python3 touchscreen_calibrate.py --device /dev/input/event2 --samples 8

Workflow:
1) Touch and hold near top-left when prompted.
2) Touch and hold near top-right.
3) Touch and hold near bottom-left.
4) Touch and hold near bottom-right.

At the end it prints suggested values for:
- tftOrig
- tftEnd
"""

import argparse
import sys
import time
from statistics import median

import evdev


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calibrate touchscreen raw ranges for macroKeys.py")
    parser.add_argument(
        "--device",
        default="/dev/input/touchscreen",
        help="Input device path (default: /dev/input/touchscreen)",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=10,
        help="Number of pressed samples to collect per corner (default: 10)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="Seconds to wait for each corner before failing (default: 20)",
    )
    return parser.parse_args()


def read_corner_samples(device: evdev.InputDevice, label: str, sample_target: int, timeout: float):
    print(f"\nTouch and hold: {label}")
    print("Press Enter when ready...")
    input()

    start = time.time()
    x_values = []
    y_values = []

    # Keep latest values from EV_ABS until touch press/release frames come in.
    current_x = None
    current_y = None
    touching = False

    print("Collecting samples...", end=" ", flush=True)

    while len(x_values) < sample_target:
        if time.time() - start > timeout:
            raise TimeoutError(f"Timed out while collecting samples for {label}")

        for event in device.read_loop():
            if event.type == evdev.ecodes.EV_ABS:
                if event.code in (0, evdev.ecodes.ABS_X):
                    current_x = event.value
                elif event.code in (1, evdev.ecodes.ABS_Y):
                    current_y = event.value

            elif event.type == evdev.ecodes.EV_KEY and event.code == 330:  # BTN_TOUCH
                touching = event.value == 1

            elif event.type == evdev.ecodes.EV_SYN:
                # Record only when finger is down and we have both coordinates.
                if touching and current_x is not None and current_y is not None:
                    x_values.append(current_x)
                    y_values.append(current_y)
                    if len(x_values) % 2 == 0:
                        print(f"{len(x_values)}/{sample_target}", end=" ", flush=True)
                    if len(x_values) >= sample_target:
                        break

        if len(x_values) >= sample_target:
            break

    print("done")

    # Median is robust against jitter while holding finger.
    return int(median(x_values)), int(median(y_values))


def main() -> int:
    args = parse_args()

    if args.samples < 3:
        print("--samples must be >= 3", file=sys.stderr)
        return 2

    try:
        device = evdev.InputDevice(args.device)
    except Exception as exc:
        print(f"Failed to open device {args.device}: {exc}", file=sys.stderr)
        return 1

    print(f"Using device: {device.path}")
    print(device)

    corners = [
        "top-left",
        "top-right",
        "bottom-left",
        "bottom-right",
    ]

    try:
        device.grab()
    except Exception:
        pass

    measured = {}

    try:
        for corner in corners:
            x, y = read_corner_samples(device, corner, args.samples, args.timeout)
            measured[corner] = (x, y)
            print(f"{corner:12s} -> raw ({x}, {y})")
    finally:
        try:
            device.ungrab()
        except Exception:
            pass

    xs = [pt[0] for pt in measured.values()]
    ys = [pt[1] for pt in measured.values()]

    x_min = min(xs)
    x_max = max(xs)
    y_min = min(ys)
    y_max = max(ys)

    print("\nCalibration summary")
    print("-------------------")
    print(f"x range: min={x_min}, max={x_max}")
    print(f"y range: min={y_min}, max={y_max}")

    print("\nSuggested values for macroKeys.py")
    print("---------------------------------")
    print(f"tftOrig = ({x_min}, {y_max})")
    print(f"tftEnd = ({x_max}, {y_min})")

    print("\nIf touches are mirrored on one axis, swap that axis endpoints manually.")
    print("Example: mirrored X -> tftOrig = (x_max, y_max), tftEnd = (x_min, y_min)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
