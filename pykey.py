import usb_hid

# These are the default devices, so you don't need to write
# this explicitly if the default is what you want.
usb_hid.enable((usb_hid.Device.KEYBOARD,)) 