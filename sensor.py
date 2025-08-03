"""Support for lifesmart sensors."""
import logging
import json

from homeassistant.const import (
    TEMP_CELSIUS,
)
DOMAIN = "lifesmart_1"
ENTITY_ID_FORMAT = DOMAIN + ".{}"

from . import  LifeSmartEntity

_LOGGER = logging.getLogger(__name__)

GAS_SENSOR_TYPES = ["SL_SC_WA ",
"SL_SC_CH",
"SL_SC_CP",
"ELIQ_EM"]

OT_SENSOR_TYPES = ["SL_SC_MHW",
"SL_SC_BM",
"SL_SC_G",
"SL_SC_BG"]

EV_SENSOR_TYPES = ["SL_SC_THL",
"SL_SC_BE",
"SL_SC_CQ"]

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
        if device['devtype'] in OT_SENSOR_TYPES:
            for idx in device['data']:
                # breakpoint()
                if idx in ["Z","V","P3","P4"]:
                    devices.append(LifeSmartSensor(device,idx,device['data'][idx],device['agt_ver'],param))
                    _LOGGER.debug("Setting up device with devtype: %s, idx: %s", device['devtype'], idx)
                else:
                    devices.append(LifeSmartSensor(device,idx,device['data'][idx],device['agt_ver'],param))
                    _LOGGER.debug("Setting up device with devtype: %s, idx: %s", device['devtype'], idx)
    _LOGGER.debug("Total devices to add: %d", len(devices))
    _LOGGER.debug("Raw dev_data: %s", dev_data)
    _LOGGER.debug("Device data: %s", device)
    _LOGGER.debug("IDX loop: %s", list(device['data'].keys()))
    async_add_entities(devices)
    return True
    



class LifeSmartSensor(LifeSmartEntity):
    """Representation of a LifeSmartSensor."""

    def __init__(self, dev, idx, val, ver, param):
        """Initialize the LifeSmartSensor."""
        super().__init__(dev, idx, val, ver, param)
        self.entity_id = ENTITY_ID_FORMAT.format(( dev['devtype'] + "_" + dev['agt'] + "_" + dev['me'] + "_" + idx).lower())
        self._ver =  ver
        devtype = dev['devtype']
        if devtype in GAS_SENSOR_TYPES:
            self._unit = "None"
            self._device_class = "None"
            self._state = val['val']
        else:
            if idx == "T" or idx == "P1":
                self._device_class = "temperature"
                self._unit = TEMP_CELSIUS
            elif idx == "H" or idx == "P2":
                self._device_class = "humidity"
                self._unit = "%"
            elif idx == "Z":
                self._device_class = "illuminance"
                self._unit = "lx"
            elif idx == "V":
                self._device_class = "battery"
                self._unit = "%"
            elif idx == "P3":
                self._device_class = "None"
                self._unit = "ppm"
            elif idx == "P4":
                self._device_class = "None"
                self._unit = "mg/m3"
            else:
                self._unit = "None"
                self._device_class = "None"
            self._state = val['v']
            if idx == "G" or idx == "B" or idx == "AXS":
                self._state = not val['val']

    # @property
    # def name(self):
    #     """Return the name of the sensor."""
    #     return self.entity_id
    
    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit

    @property
    def device_class(self):
        """Return the device class of this entity."""
        # breakpoint()
        return self._device_class

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state
    
    @property
    def unique_id(self):
        """Return a unique ID."""
        return self.entity_id
    
    @property
    def device_info(self):
        # breakpoint()
        return {
            "identifiers": {(DOMAIN, f"{self._agt}_{self._me}")},
            "name": f"LifeSmart Device {self._name}",
            "manufacturer": "LifeSmart",
            "model": self._devtype,
            "sw_version": self._ver,
        }
    
    @property
    def assumed_state(self):
        return False


