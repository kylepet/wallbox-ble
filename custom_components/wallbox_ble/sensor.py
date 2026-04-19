from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
)

from .const import DOMAIN, LOGGER
from .coordinator import WallboxBLEDataUpdateCoordinator
from .entity import WallboxBLEEntity

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="wallbox_ble",
        name="Status",
    ),
    SensorEntityDescription(
        key="wallbox_ble_grid_power_l1",
        name="Grid power L1",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
    SensorEntityDescription(
        key="wallbox_ble_grid_power_l2",
        name="Grid power L2",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
    SensorEntityDescription(
        key="wallbox_ble_grid_power_l3",
        name="Grid power L3",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
    SensorEntityDescription(
        key="wallbox_ble_grid_voltage_l1",
        name="Grid voltage L1",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
    ),
    SensorEntityDescription(
        key="wallbox_ble_grid_voltage_l2",
        name="Grid voltage L2",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
    ),
    SensorEntityDescription(
        key="wallbox_ble_grid_voltage_l3",
        name="Grid voltage L3",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
    ),
    SensorEntityDescription(
        key="wallbox_ble_grid_current_l1",
        name="Grid current L1",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
    ),
    SensorEntityDescription(
        key="wallbox_ble_grid_current_l2",
        name="Grid current L2",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
    ),
    SensorEntityDescription(
        key="wallbox_ble_grid_current_l3",
        name="Grid current L3",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
    ),
    SensorEntityDescription(
        key="wallbox_ble_grid_energy",
        name="Grid energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
    ),
)


async def async_setup_entry(hass, entry, async_add_devices):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices(
        WallboxBLESensor(
            coordinator=coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


SENSOR_VALUE_MAP = {
    "wallbox_ble": lambda c: c.status,
    "wallbox_ble_grid_power_l1": lambda c: c.grid_power_l1,
    "wallbox_ble_grid_power_l2": lambda c: c.grid_power_l2,
    "wallbox_ble_grid_power_l3": lambda c: c.grid_power_l3,
    "wallbox_ble_grid_voltage_l1": lambda c: c.grid_voltage_l1,
    "wallbox_ble_grid_voltage_l2": lambda c: c.grid_voltage_l2,
    "wallbox_ble_grid_voltage_l3": lambda c: c.grid_voltage_l3,
    "wallbox_ble_grid_current_l1": lambda c: c.grid_current_l1,
    "wallbox_ble_grid_current_l2": lambda c: c.grid_current_l2,
    "wallbox_ble_grid_current_l3": lambda c: c.grid_current_l3,
    "wallbox_ble_grid_energy": lambda c: c.grid_energy,
}


class WallboxBLESensor(WallboxBLEEntity, SensorEntity):
    def __init__(
        self,
        coordinator: WallboxBLEDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{entity_description.key}"

    @property
    def available(self):
        return self.coordinator.available

    @property
    def native_value(self):
        getter = SENSOR_VALUE_MAP.get(self.entity_description.key)
        if getter:
            return getter(self.coordinator)
        return None
