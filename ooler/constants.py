"""Constants to refer to the UUIDs for Ooler characteristics"""
from enum import Enum
from bleak import uuids

TARGET_TEMP_F = "6aa46711-a29d-4f8a-88e2-044ca1fd03ff"
ACTUAL_TEMP = "e8ebded3-9dca-45c2-a2d8-ceffb901474d"
FAN_SPEED = "cafe2421-d04c-458f-b1c0-253c6c97e8e8"
POWER_STATUS = "7a2623ff-bd92-4c13-be9f-7023aa4ecb85"
WARM_WAKE_ENABLED = "7aa73db1-1c2d-4c8c-9195-36c0a4b6acb2"
RELATIVE_HUMIDITY = "654b8162-7090-4084-8d94-4eb33e917e9c"
AMBIENT_TEMPERATURE_F = "7c0ea228-2616-4765-a726-beb5f4a0fa71"
WATER_LEVEL = "8db5b9db-dbf6-47e6-a9dd-0612a1349a5b"
SERIAL_NUMBER = "136e24c6-c486-4a74-bb0a-d18b985970a6"
NAME = "00002a00-0000-1000-8000-00805f9b34fb"
CLEAN = "e9bf509a-b1c5-4243-9514-352ad2d851f6"
DEVICE_LOGS = "e6a505a4-9f0b-4755-b234-13243240da23"
PUMP_WATTS = "5a914d86-9b5e-4a35-ad3d-3e5936d485b2"
PUMP_VOLTS = "f30d875a-7297-43ac-9f5b-1d7eed4446eb"
POWER_RAIL = "acab07ec-fc95-451d-88e5-4565a364a806"
LIFETIME = "5d30781f-1d06-4790-bbb8-5e1d7da96383"
RUNTIME = "1a5c6dae-34de-4265-9fa6-0a59f7f683ee"
UV_RUNTIME = "0ab6ff00-8d1b-475e-bcfa-ed3467f1f890"
DISPLAY_TEMPERATURE_UNIT = "2c988613-fe15-4067-85bc-8e59d5e0b1e3"
LOCAL_TIME = uuids.normalize_uuid_str("2A0F")
CURRENT_TIME = uuids.normalize_uuid_str("2A2B")


class TemperatureUnit(Enum):
    Fahrenheit = 0
    Celsius = 1


class FanSpeed(Enum):
    Silent = 0
    Regular = 1
    Boost = 2
