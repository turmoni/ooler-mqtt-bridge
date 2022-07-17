"""Monitor and control an Ooler device via Bluetooth Low Energy"""
import logging
import ooler.constants as constants
from gattlib import GATTRequester, BTIOException


class Ooler:
    """Control an Ooler device via Bluetooth LE"""

    def __init__(self, address=None, stay_connected=True, max_connection_attempts=5):
        self.address = address
        self.stay_connected = stay_connected
        self.max_connection_attempts = max_connection_attempts
        self.requester = GATTRequester(address, False)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        if self.stay_connected:
            self.connect()

    def connect(self) -> None:
        """Attempt to connect to the Ooler"""
        if self.requester.is_connected():
            return

        for attempt in range(self.max_connection_attempts):
            try:
                self.logger.debug(f"Attempting to connect, attempt {attempt}")
                self.requester.connect(True)
                self.logger.info(f"Connected to {self.address}")
                break
            except BTIOException as exc:
                self.logger.warning(
                    f"Failed to connect on attempt {attempt}, got {exc}"
                )
                self.requester.disconnect()

        if not self.requester.is_connected():
            raise ConnectionError(
                f"Failed to connect after {self.max_connection_attempts} goes"
            )

        self.requester.exchange_mtu(512)
        self.uuid_map = self._get_uuid_map()

    def _get_uuid_map(self) -> dict:
        """
        Get a mapping of UUIDs to handles - this shouldn't be needed, but the
        UUID-related functions don't seem to work for me with the Ooler
        """
        characteristics = self.requester.discover_characteristics()
        return {v["uuid"]: v["value_handle"] for v in characteristics}

    def _request_characteristic(self, uuid: str) -> bytes:
        """Request a characteristic, handling connections and the like"""
        if not self.requester.is_connected():
            self.connect()

        value = self.requester.read_by_handle(self.uuid_map[uuid])[0]

        if not self.stay_connected:
            self.disconnect()

        return value

    def _write_characteristic(self, uuid: str, data: bytes) -> bytes:
        """Write a characteristic, handling connections and the like"""
        if not self.requester.is_connected():
            self.connect()

        self.requester.write_by_handle(self.uuid_map[uuid], data)

        if not self.stay_connected:
            self.disconnect()

    def disconnect(self) -> None:
        """Disconnect from the Ooler"""
        self.requester.disconnect()

    @staticmethod
    def _f_to_c(deg_f: int) -> int:
        """Convert Fahrenheit to Celsius, integer"""
        c_float = (deg_f - 32) / 1.8
        return round(c_float)

    @staticmethod
    def _c_to_f(deg_c: int) -> int:
        """Convert Celsius to Fahrenheit, integer"""
        f_float = (deg_c * 1.8) + 32
        return round(f_float)

    @property
    def actual_temperature_f(self) -> int:
        """Get the current tempterature in Fahrenheit"""
        return int.from_bytes(
            self._request_characteristic(constants.ACTUAL_TEMP_F), byteorder="big"
        )

    @property
    def actual_temperature_c(self) -> int:
        """Get the current tempterature in Celsius"""
        return self._f_to_c(self.actual_temperature_f)

    @property
    def desired_temperature_f(self) -> int:
        """Get the desired tempterature in Fahrenheit"""
        return int.from_bytes(
            self._request_characteristic(constants.TARGET_TEMP_F), byteorder="big"
        )

    @desired_temperature_f.setter
    def desired_temperature_f(self, deg_f: int) -> None:
        """Set the desired tempterature in Fahrenheit"""
        self._write_characteristic(
            constants.TARGET_TEMP_F, deg_f.to_bytes(1, byteorder="big")
        )

    @property
    def desired_temperature_c(self) -> int:
        """Get the desired tempterature in Celsius"""
        return self._f_to_c(self.desired_temperature_f)

    @desired_temperature_c.setter
    def desired_temperature_c(self, deg_c: int) -> None:
        """Set the desired tempterature in Celsius"""
        self.desired_temperature_f = self._c_to_f(deg_c)

    @property
    def powered_on(self) -> bool:
        """Return the power state of the Ooler"""
        return self._request_characteristic(constants.POWER_STATUS) == b"\x01"

    @powered_on.setter
    def powered_on(self, value: bool) -> None:
        """Turn the Ooler on or off"""
        self._write_characteristic(
            constants.POWER_STATUS, value.to_bytes(1, byteorder="big")
        )

    @property
    def fan_speed(self) -> constants.FanSpeed:
        """Return the fan mode of the Ooler"""
        speed = self._request_characteristic(constants.FAN_SPEED)
        return constants.FanSpeed(int.from_bytes(speed, byteorder="big"))

    @fan_speed.setter
    def fan_speed(self, speed: constants.FanSpeed) -> None:
        """Return the fan mode of the Ooler"""
        self._write_characteristic(
            constants.FAN_SPEED, speed.value.to_bytes(1, byteorder="big")
        )

    @property
    def water_level(self) -> int:
        """Return the water level of the Ooler"""
        return int.from_bytes(
            self._request_characteristic(constants.WATER_LEVEL), byteorder="big"
        )

    @property
    def pump_wattage(self) -> int:
        """Return the wattage of the pump"""
        return int.from_bytes(
            self._request_characteristic(constants.PUMP_WATTS), byteorder="big"
        )

    @property
    def pump_voltage(self) -> int:
        """Return the volttage of the pump"""
        return int.from_bytes(
            self._request_characteristic(constants.PUMP_VOLTS), byteorder="big"
        )

    @property
    def cleaning(self) -> bool:
        """Return whether the device is cleaning itself"""
        return self._request_characteristic(constants.CLEAN) == b"\x01"

    @cleaning.setter
    def cleaning(self, value: bool) -> None:
        """Tell the device to clean"""
        self._write_characteristic(constants.CLEAN, value.to_bytes(1, byteorder="big"))

    @property
    def name(self) -> str:
        """Get the name of the Ooler"""
        return self._request_characteristic(constants.NAME).decode(encoding="ascii")
