from unittest.mock import MagicMock, call, mock_open, patch

import usbHidKeyboard

MOCK_HID_PATH = "/dev/mock_hidg0"


def test_send_to_gadget_writes_press_and_release_reports():
    mocked_open = mock_open()

    with patch("usbHidKeyboard.open", mocked_open):
        usbHidKeyboard.send_to_gadget(MOCK_HID_PATH, reserved_code=16, control_code=2, keyboard_code=0x28)

    handle = mocked_open()
    assert handle.write.call_args_list == [
        call(bytearray([2, 16, 0x28, 0, 0, 0, 0, 0])),
        call(bytearray([0, 0, 0, 0, 0, 0, 0, 0])),
    ]


def test_send_calls_expected_sequence(monkeypatch):
    send_mock = MagicMock()
    sleep_mock = MagicMock()

    monkeypatch.setattr(usbHidKeyboard, "send_to_gadget", send_mock)
    monkeypatch.setattr(usbHidKeyboard.time, "sleep", sleep_mock)

    usbHidKeyboard.send("MUTE", MOCK_HID_PATH)

    mute_cfg = usbHidKeyboard.KEYS_ALLOWED["MUTE"]
    send_mock.assert_has_calls(
        [
            call(
                MOCK_HID_PATH,
                reserved_code=mute_cfg["rsvd"],
                control_code=mute_cfg["ctrl"],
                keyboard_code=mute_cfg["kbd"],
            ),
            call(MOCK_HID_PATH, reserved_code=0, control_code=mute_cfg["ctrl"]),
        ]
    )
    sleep_mock.assert_called_once_with(mute_cfg["delay"])
