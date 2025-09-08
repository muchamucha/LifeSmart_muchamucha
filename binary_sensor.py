"""Support for LifeSmart binary sensors."""
import logging
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    ENTITY_ID_FORMAT,
)

from .entity import LifeSmartEntity
DOMAIN = "lifesmart_1"
_LOGGER = logging.getLogger(__name__)


GUARD_SENSOR = ["SL_SC_G",
"SL_SC_BG"]
MOTION_SENSOR = ["SL_SC_MHW",
"SL_SC_BM",
"SL_SC_CM"]
SMOKE_SENSOR = ["SL_P_A"]
# def setup_platform(hass, config, add_entities, discovery_info=None):
#     """Perform the setup for lifesmart devices."""
#     breakpoint()
#     if discovery_info is None:
#         return
#     dev = discovery_info.get("dev")
#     param = discovery_info.get("param")
#     devices = []
#     for idx in dev['data']:
#         if idx in ["M","G","B","AXS","P1"]:
#             devices.append(LifeSmartBinarySensor(dev,idx,dev['data'][idx],param))
#     breakpoint()
#     add_entities(devices)

async def async_setup_entry(hass, config, async_add_entities):
    """Perform the setup for LifeSmart devices."""
    devices = []
    data = hass.data[DOMAIN][config.entry_id]
    dev_data = data.get('devices',None)
    param = data.get('config',None)
    # 检查设备的 data 字段是否存在
    if not data:
        _LOGGER.error("Device data not found in dev: %s", data)
        return False

    for device in dev_data:
        for idx in device['data']:
            if idx in ["M","G","B","AXS","P1"]:
                devices.append(LifeSmartBinarySensor(device,idx,device['data'][idx],device['agt_ver'],param))
                _LOGGER.debug("Setting up device with devtype: %s, idx: %s", device['devtype'], idx)
    async_add_entities(devices)
    _LOGGER.debug("Total devices to add: %d", len(devices))

class LifeSmartBinarySensor(LifeSmartEntity, BinarySensorEntity):
    """Representation of LifeSmartBinarySensor."""

    def __init__(self, dev, idx, val, ver, param):
        super().__init__(dev, idx, val, ver, param)
        self.entity_id = ENTITY_ID_FORMAT.format(( dev['devtype'] + "_" + dev['agt'] + "_" + dev['me'] + "_" + idx).lower())
        self._ver = ver
        devtype = dev['devtype']
        if devtype in GUARD_SENSOR:
            self._device_class = "door"
        elif devtype in MOTION_SENSOR:
            self._device_class = "motion"
        else:
            self._device_class = "smoke"
        if (val['val'] == 1 and self._device_class != "door") or (val['val'] == 0 and self._device_class == "door"):
            self._state = True
        else:
            self._state = False

    @property
    def is_on(self):
        """Return true if sensor is on."""
        return self._state

    @property
    def device_class(self):
        """Return the class of binary sensor."""
        return self._device_class
    @property
    def unique_id(self):
        """Return a unique ID."""
        return self.entity_id
    
    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"{self._agt}_{self._me}")},
            "name": f"LifeSmart Device {self._name}",
            "manufacturer": "LifeSmart",
            "model": self._devtype,
            "sw_version": self._ver,
        }



