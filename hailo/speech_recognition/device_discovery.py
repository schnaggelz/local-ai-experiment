import logging

log = logging.getLogger(__name__)


class DeviceDiscovery:
    def __init__(self, pa):
        self._pa = pa

    def list_devices(self):
        log.info("Available Audio Devices:")
        for i in range(self._pa.get_device_count()):
            info = self._pa.get_device_info_by_index(i)
            log.info(f"  [{i}] {info['name']} (Inputs: {info['maxInputChannels']}, Outputs: {info['maxOutputChannels']})")

    def resolve_input_device(self, index=None):
        """Return a validated input device index, auto-detecting the default if index is None."""
        try:
            if index is None:
                info = self._pa.get_default_input_device_info()
                index = int(info['index'])
            else:
                info = self._pa.get_device_info_by_index(index)
                if info['maxInputChannels'] < 1:
                    raise ValueError(f"Device [{index}] '{info['name']}' has no input channels.")
        except OSError:
            msg = ("No default input device available." if index is None
                   else f"Input device [{index}] is not available.")
            raise RuntimeError(f"{msg} Use --list-devices to see available devices.")
        log.info(f"Using input device [{index}]: {info['name']}")
        return index

    def resolve_output_device(self, index=None):
        """Return a validated output device index, auto-detecting the default if index is None."""
        try:
            if index is None:
                info = self._pa.get_default_output_device_info()
                index = int(info['index'])
            else:
                info = self._pa.get_device_info_by_index(index)
                if info['maxOutputChannels'] < 1:
                    raise ValueError(f"Device [{index}] '{info['name']}' has no output channels.")
        except OSError:
            raise RuntimeError(f"Output device [{index}] is not available. Use --list-devices to see available devices.")
        log.info(f"Using output device [{index}]: {info['name']}")
        return index
