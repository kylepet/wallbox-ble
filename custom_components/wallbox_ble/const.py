"""Constants for wallbox_ble."""
from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

NAME = "Wallbox BLE"
DOMAIN = "wallbox_ble"
VERSION = "0.0.1"
CONF_PASSCODE = "passcode"
CONF_UPDATE_INTERVAL = "update_interval"
DEFAULT_UPDATE_INTERVAL = 10
