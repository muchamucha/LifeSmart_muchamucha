"""Support for LifeSmart covers."""
from homeassistant.components.cover import (
    ENTITY_ID_FORMAT,
    ATTR_POSITION,
    CoverEntity,
)
import logging

from .entity import LifeSmartEntity
DOMAIN = "lifesmart_1"
_LOGGER = logging.getLogger(__name__)

# def setup_platform(hass, config, add_entities, discovery_info=None):
#     """Set up lifesmart dooya cover devices."""
#     breakpoint()
#     if discovery_info is None:
#         return
#     dev = discovery_info.get("dev")
#     param = discovery_info.get("param")
#     devices = []
#     idx = "P1"
#     devices.append(LifeSmartCover(dev,idx,dev['data'][idx],param))
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
            if idx == "P1":
                devices.append(LifeSmartCover(device,idx,device['data'][idx],device['agt_ver'],param))
                _LOGGER.debug("Setting up device with devtype: %s, idx: %s", device['devtype'], idx)
    async_add_entities(devices)
    _LOGGER.debug("Total devices to add: %d", len(devices))
    _LOGGER.debug("Raw dev_data: %s", dev_data)
    _LOGGER.debug("Device data: %s", device)
    return True


class LifeSmartCover(LifeSmartEntity, CoverEntity):
    """LifeSmart cover devices."""

    def __init__(self, dev, idx, val, ver, param):
        """Init LifeSmart cover device."""
        super().__init__(dev, idx, val, ver, param)
        self._name = dev['name']
        self.entity_id = ENTITY_ID_FORMAT.format(( dev['devtype'] + "_" + dev['agt'] + "_" + dev['me']).lower())
        self._pos = val['val']
        self._device_class = "curtain"

    @property
    def current_cover_position(self):
        """Return the current position of the cover."""
        return self._pos

    @property
    def is_closed(self):
        """Return if the cover is closed."""
        return self.current_cover_position <= 0

    def close_cover(self, **kwargs):
        """Close the cover."""
        super()._lifesmart_epset(self, "0xCF", 0, "P2")

    def open_cover(self, **kwargs):
        """Open the cover."""
        super()._lifesmart_epset(self, "0xCF", 100, "P2")

    def stop_cover(self, **kwargs):
        """Stop the cover."""
        super()._lifesmart_epset(self, "0xCE", 0x80, "P2")

    def set_cover_position(self, **kwargs):
        """Move the cover to a specific position."""
        position = kwargs.get(ATTR_POSITION)
        super()._lifesmart_epset(self, "0xCE", position, "P2")

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


