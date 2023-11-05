"""Monitor and control an Ooler device via Bluetooth Low Energy"""
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from ooler import constants
from bleak import BleakClient, BleakError
import asyncio


class Ooler:
    """Control an Ooler device via Bluetooth LE"""

    def __init__(self, address=None, stay_connected=True, max_connection_attempts=30, connection_retry_interval=1):
        self.address = address
        self.stay_connected = stay_connected
        self.max_connection_attempts = max_connection_attempts
        self.connection_retry_interval = connection_retry_interval
        self.client = BleakClient(self.address)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.device_temperature_unit = None
        self.connection_lock = asyncio.Lock()

    async def connect(self) -> None:
        """Attempt to connect to the Ooler"""
        if self.client and self.client.is_connected:
            return

        async with self.connection_lock:
            # Check if someone else connected already
            if self.client and self.client.is_connected:
                return

            attempt = 0
            self.client = BleakClient(self.address)
            while not self.client.is_connected and attempt < self.max_connection_attempts:
                self.logger.info(f"Attempting to connect number {attempt}")
                try:
                    await self.client.connect()
                    self.logger.info(f"Connected to {self.address}")
                except BleakError as exc:
                    self.logger.warning(f"Failed to connect on attempt {attempt}, got {exc}")
                    await asyncio.sleep(self.connection_retry_interval)
                attempt = attempt + 1

            if not self.client.is_connected:
                raise ConnectionError("Failed to connect to Ooler")

    async def _request_characteristic(self, uuid: str) -> bytes:
        """Request a characteristic, handling connections and the like"""
        for attempt in range(self.max_connection_attempts):
            try:
                if not self.client.is_connected:
                    await self.connect()

                value = await self.client.read_gatt_char(uuid)
                break
            except EOFError as exc:
                self.logger.warning(f"Got EOFError {exc}. Attempt number {attempt}.")
                await asyncio.sleep(self.connection_retry_interval)

        if not self.stay_connected:
            await self.disconnect()

        return value

    async def _write_characteristic(self, uuid: str, data: bytes) -> bytes:
        """Write a characteristic, handling connections and the like"""
        for attempt in range(self.max_connection_attempts):
            try:
                if not self.client.is_connected:
                    await self.connect()

                await self.client.write_gatt_char(uuid, data)
                break
            except EOFError as exc:
                self.logger.warning(f"Got EOFError {exc}. Attempt number {attempt}.")
                await asyncio.sleep(self.connection_retry_interval)

        if not self.stay_connected:
            await self.disconnect()

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

    async def set_current_time(self, tz: str) -> None:
        """Set the current time and time zone offset on the Ooler"""
        # Documentation for these characteristics is weirdly hard to find for some
        # reason, unless that's just me, but I'll document them here
        curtime = datetime.now(tz=ZoneInfo(tz))

        # First the Current Time Service, which is fairly self-explanatory from the code
        time_data = bytearray()
        time_data.extend(curtime.year.to_bytes(2, byteorder="little"))
        time_data.append(curtime.month)
        time_data.append(curtime.day)
        time_data.append(curtime.hour)
        time_data.append(curtime.minute)
        time_data.append(curtime.second)
        time_data.append(curtime.isoweekday())
        # This is meant to be 256ths of a second, but I think we really don't care
        time_data.append(0)
        # And now we lie in our reason why we're updating; this is a bitfield:
        # - Manual time update?
        # - External reference time update?
        # - Time zone change?
        # - DST change:
        # We'll just say it's a reference time update and nothing else.
        time_data.append(2)
        await self._write_characteristic(constants.CURRENT_TIME, time_data)

        # Next is Local Time Information, which is a bit weirder.
        local_data = bytearray()
        # Offsets are in multiples of 15 minutes
        offset = int(curtime.utcoffset().seconds/60/15)
        if curtime.utcoffset().days == -1:
            offset = (24 * 4) - offset
        local_data.append(offset)
        # And finally the DST offset, which is also calculated in 15 minute intervals
        local_data.append(int(curtime.dst().seconds/60/15))
        await self._write_characteristic(constants.LOCAL_TIME, local_data)

    async def get_actual_temperature_raw(self) -> int:
        """Get the current tempterature in whatever the Ooler is configured for"""
        return int.from_bytes(
            await self._request_characteristic(constants.ACTUAL_TEMP), byteorder="big"
        )

    async def get_actual_temperature_f(self) -> int:
        """Get the current tempterature in Fahrenheit"""
        if await self.get_temperature_unit() == constants.TemperatureUnit.Celsius:
            return self._c_to_f(await self.get_actual_temperature_raw())
        return await self.get_actual_temperature_raw()

    async def get_actual_temperature_c(self) -> int:
        """Get the current tempterature in Celsius"""
        if await self.get_temperature_unit() == constants.TemperatureUnit.Fahrenheit:
            return self._f_to_c(await self.get_actual_temperature_raw())
        return await self.get_actual_temperature_raw()

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

    async def get_temperature_unit(self) -> constants.TemperatureUnit:
        """Return the temperature unit of the Ooler"""
        if self.device_temperature_unit is None:
            unit = await self._request_characteristic(constants.DISPLAY_TEMPERATURE_UNIT)
            self.device_temperature_unit = constants.TemperatureUnit(
                int.from_bytes(unit, byteorder="big")
            )
        return self.device_temperature_unit

    async def set_temperature_unit(self, unit: constants.TemperatureUnit):
        await self._write_characteristic(
            constants.DISPLAY_TEMPERATURE_UNIT, unit.value.to_bytes(1, byteorder="big"))
        # Refresh the cached value
        self.device_temperature_unit = None
        await self.get_temperature_unit()

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
        await self._write_characteristic(
            constants.CLEAN, value.to_bytes(1, byteorder="big")
        )

    async def get_name(self) -> str:
        """Get the name of the Ooler"""
        return (await self._request_characteristic(constants.NAME)).decode(
            encoding="ascii"
        )
