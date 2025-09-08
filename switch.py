"""lifesmart switch @skyzhishui"""
import subprocess
import urllib.request
import json
import time
import hashlib
import logging

from homeassistant.components.switch import (
    SwitchEntity,
    ENTITY_ID_FORMAT,
)

from .entity import LifeSmartEntity
DOMAIN = "lifesmart_1"
ENTITY_ID_FORMAT = DOMAIN + ".{}"

_LOGGER = logging.getLogger(__name__)


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
            if idx in ["L1","L2","L3","P1","P2","P3"]:
                devices.append(LifeSmartSwitch(device,idx,device['data'][idx],device['agt_ver'],param))
                _LOGGER.debug("Setting up device with devtype: %s, idx: %s", device['devtype'], idx)
        # if idx in ["L1","L2","L3","P1","P2","P3"]:
        #     devices.append(LifeSmartSwitch(dev,idx,dev['data'][idx],param))
        #     _LOGGER.debug("Setting up device with devtype: %s, idx: %s", dev['devtype'], idx)
    async_add_entities(devices)
    _LOGGER.debug("Total devices to add: %d", len(devices))
    _LOGGER.debug("Raw dev_data: %s", dev_data)
    _LOGGER.debug("Device data: %s", device)
    _LOGGER.debug("IDX loop: %s", list(device['data'].keys()))
    return True

# async def async_setup_entry(hass, entry, async_add_entities):
#     """Set up LifeSmart sensors based on a config entry."""
#     breakpoint()
#     # devices = hass.data[DOMAIN][entry.entry_id]["devices"]
#     devices = hass.data["switch"]
#     sensor_entities = []
#     for dev in devices:
#         sensor = LifeSmartSwitch(hass, entry, dev)
#         sensor_entities.append(sensor)
    
#     async_add_entities(sensor_entities)
#     return True

class LifeSmartSwitch(LifeSmartEntity, SwitchEntity):
    

    def __init__(self, dev, idx, val, ver, param):
        """Initialize the switch."""
        super().__init__(dev, idx, val, ver, param)
        self.entity_id = ENTITY_ID_FORMAT.format(( dev['devtype'] + "_" + dev['agt'] + "_" + dev['me'] + "_" + idx).lower())
        self._ver = ver
        if val['type'] %2 == 1:
            self._state = True
        else:
            self._state = False

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    async def async_added_to_hass(self):
        """Call when entity is added to hass."""

    def _get_state(self):
        """get lifesmart switch state."""
        return self._state

    def turn_on(self, **kwargs):
        """Turn the device on."""
        if super()._lifesmart_epset(self, "0x81", 1, self._idx) == 0:
            self._state = True
            self.schedule_update_ha_state()
        else:
            _LOGGER.warning("Failed to turn on switch %s", self.entity_id)

    def turn_off(self, **kwargs):
        """Turn the device off."""
        if super()._lifesmart_epset(self, "0x80", 0, self._idx) == 0:
            self._state = False
            self.schedule_update_ha_state()
        else:
            _LOGGER.warning("Failed to turn off switch %s", self.entity_id)
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
        
    @property
    def assumed_state(self):
        return False

