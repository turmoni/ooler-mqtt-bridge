"""Constants to refer to the UUIDs for Ooler characteristics"""
from enum import Enum

TARGET_TEMP_F = "6aa46711-a29d-4f8a-88e2-044ca1fd03ff"
ACTUAL_TEMP_F = "e8ebded3-9dca-45c2-a2d8-ceffb901474d"
FAN_SPEED = "cafe2421-d04c-458f-b1c0-253c6c97e8e8"
POWER_STATUS = "7a2623ff-bd92-4c13-be9f-7023aa4ecb85"
WARM_WAKE_ENABLED = "7aa73db1-1c2d-4c8c-9195-36c0a4b6acb2"
RELATIVE_HUMIDITY = "654b8162-7090-4084-8d94-4eb33e917e9c"
AMBIENT_TEMPERATURE_F = "7c0ea228-2616-4765-a726-beb5f4a0fa71"
WATER_LEVEL = "8db5b9db-dbf6-47e6-a9dd-0612a1349a5b"
SERIAL_NUMBER = "136e24c6-c486-4a74-bb0a-d18b985970a6"
NAME = "00002a00-0000-1000-8000-00805f9b34fb"


class FanSpeed(Enum):
    Silent = 0
    Regular = 1
    Boost = 2
