"""Monitor and control an Ooler device via Bluetooth Low Energy"""
import logging
from ooler import constants
from bleak import BleakClient, BleakError


class Ooler:
    """Control an Ooler device via Bluetooth LE"""

    def __init__(self, address=None, stay_connected=True, max_connection_attempts=5):
        self.address = address
        self.stay_connected = stay_connected
        self.max_connection_attempts = max_connection_attempts
        self.client = None
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

    async def connect(self) -> None:
        """Attempt to connect to the Ooler"""
        if self.client and self.client.is_connected:
            return

        self.client = BleakClient(self.address)
        self.logger.info("Attempting to connect")
        await self.client.connect()
        self.logger.info(f"Connected to {self.address}")


        if not self.client.is_connected:
            raise ConnectionError(
                "Failed to connect to Ooler"
            )

    async def _request_characteristic(self, uuid: str) -> bytes:
        """Request a characteristic, handling connections and the like"""
        if not self.client.is_connected:
            await self.connect()

        value = await self.client.read_gatt_char(uuid)

        if not self.stay_connected:
            await self.disconnect()

        return value

    async def _write_characteristic(self, uuid: str, data: bytes) -> bytes:
        """Write a characteristic, handling connections and the like"""
        if not self.client.is_connected:
            self.connect()

        await self.client.write_gatt_char(uuid, data)

        if not self.stay_connected:
            self.disconnect()

    async def disconnect(self) -> None:
        """Disconnect from the Ooler"""
        await self.client.disconnect()

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

    async def get_actual_temperature_f(self) -> int:
        """Get the current tempterature in Fahrenheit"""
        return int.from_bytes(
            await self._request_characteristic(constants.ACTUAL_TEMP_F), byteorder="big"
        )

    async def get_actual_temperature_c(self) -> int:
        """Get the current tempterature in Celsius"""
        return self._f_to_c(await self.get_actual_temperature_f())

    async def get_desired_temperature_f(self) -> int:
        """Get the desired tempterature in Fahrenheit"""
        return int.from_bytes(
            await self._request_characteristic(constants.TARGET_TEMP_F), byteorder="big"
        )

    async def set_desired_temperature_f(self, deg_f: int) -> None:
        """Set the desired tempterature in Fahrenheit"""
        await self._write_characteristic(
            constants.TARGET_TEMP_F, deg_f.to_bytes(1, byteorder="big")
        )

    async def get_desired_temperature_c(self) -> int:
        """Get the desired tempterature in Celsius"""
        return self._f_to_c(await self.get_desired_temperature_f())

    async def set_desired_temperature_c(self, deg_c: int) -> None:
        """Set the desired tempterature in Celsius"""
        await self.set_desired_temperature_f(self._c_to_f(deg_c))

    async def powered_on(self) -> bool:
        """Return the power state of the Ooler"""
        return await self._request_characteristic(constants.POWER_STATUS) == b"\x01"

    async def set_power_state(self, value: bool) -> None:
        """Turn the Ooler on or off"""
        await self._write_characteristic(
            constants.POWER_STATUS, value.to_bytes(1, byteorder="big")
        )

    async def get_fan_speed(self) -> constants.FanSpeed:
        """Return the fan mode of the Ooler"""
        speed = await self._request_characteristic(constants.FAN_SPEED)
        return constants.FanSpeed(int.from_bytes(speed, byteorder="big"))

    async def set_fan_speed(self, speed: constants.FanSpeed) -> None:
        """Return the fan mode of the Ooler"""
        await self._write_characteristic(
            constants.FAN_SPEED, speed.value.to_bytes(1, byteorder="big")
        )

    async def get_water_level(self) -> int:
        """Return the water level of the Ooler"""
        return int.from_bytes(
            await self._request_characteristic(constants.WATER_LEVEL), byteorder="big"
        )

    async def get_pump_wattage(self) -> int:
        """Return the wattage of the pump"""
        return int.from_bytes(
            await self._request_characteristic(constants.PUMP_WATTS), byteorder="big"
        )

    async def get_pump_voltage(self) -> int:
        """Return the volttage of the pump"""
        return int.from_bytes(
            await self._request_characteristic(constants.PUMP_VOLTS), byteorder="big"
        )

    async def is_cleaning(self) -> bool:
        """Return whether the device is cleaning itself"""
        return await self._request_characteristic(constants.CLEAN) == b"\x01"

    async def set_cleaning(self, value: bool) -> None:
        """Tell the device to clean"""
        await self._write_characteristic(constants.CLEAN, value.to_bytes(1, byteorder="big"))

    async def get_name(self) -> str:
        """Get the name of the Ooler"""
        return (await self._request_characteristic(constants.NAME)).decode(encoding="ascii")
