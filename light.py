"""Support for LifeSmart Gateway Light."""
import binascii
import logging
import struct
import urllib.request
import json
import time
import hashlib
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_HS_COLOR,
    SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR,
    LightEntity,
	ENTITY_ID_FORMAT,
)
import homeassistant.util.color as color_util

from .entity import LifeSmartEntity

DOMAIN = "lifesmart_1"
_LOGGER = logging.getLogger(__name__)



# def setup_platform(hass, config, add_entities, discovery_info=None):
#     """Perform the setup for LifeSmart devices."""
#     breakpoint()
#     if discovery_info is None:
#         return
#     dev = discovery_info.get("dev")
#     param = discovery_info.get("param")
#     devices = []
#     for idx in dev['data']:
#         if idx in ["RGB","RGBW"]:
#             devices.append(LifeSmartLight(dev,idx,dev['data'][idx],param))
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
            if idx in ["RGB","RGBW"]:
                devices.append(LifeSmartLight(device,idx,device['data'][idx],device['agt_ver'],param))
                _LOGGER.debug("Setting up device with devtype: %s, idx: %s", device['devtype'], idx)
    async_add_entities(devices)
    _LOGGER.debug("Total devices to add: %d", len(devices))
    _LOGGER.debug("Raw dev_data: %s", dev_data)
    _LOGGER.debug("Device data: %s", device)
    return True
    

class LifeSmartLight(LifeSmartEntity, LightEntity):
    """Representation of a LifeSmartLight."""

    def __init__(self, dev, idx, val, ver, param):
        """Initialize the LifeSmartLight."""
        super().__init__(dev, idx, val, ver, param)
        self.entity_id = ENTITY_ID_FORMAT.format(( dev['devtype'] + "_" + dev['agt'] + "_" + dev['me'] + "_" + idx).lower())
        self._ver = ver
        if val['type'] % 2 == 1:
            self._state = True
        else:
            self._state = False
        value = val['val']
        if value == 0:
            self._hs = None
        else:
            rgbhexstr = "%x" % value
            rgbhexstr = rgbhexstr.zfill(8)
            rgbhex = bytes.fromhex(rgbhexstr)
            rgba = struct.unpack("BBBB", rgbhex)
            rgb = rgba[1:]
            self._hs = color_util.color_RGB_to_hs(*rgb)
            _LOGGER.info("hs_rgb: %s",str(self._hs))


    async def async_added_to_hass(self):
        rmdata = {}
        rmlist = await self.hass.async_add_executor_job(LifeSmartLight._lifesmart_GetRemoteList,self)
        for ai in rmlist:
            rms = await self.hass.async_add_executor_job(LifeSmartLight._lifesmart_GetRemotes,self,ai)
            rms['category'] = rmlist[ai]['category']
            rms['brand'] = rmlist[ai]['brand']
            rmdata[ai] = rms
        self._attributes.setdefault('remotelist',rmdata)
    @property
    def is_on(self):
        """Return true if it is on."""
        return self._state

    @property
    def hs_color(self):
        """Return the hs color value."""
        return self._hs

    @property
    def supported_features(self):
        """Return the supported features."""
        return SUPPORT_COLOR
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

    def turn_on(self, **kwargs):
        """Turn the light on."""
        if ATTR_HS_COLOR in kwargs:
            self._hs = kwargs[ATTR_HS_COLOR]

        rgb = color_util.color_hs_to_RGB(*self._hs)
        rgba = (0,) + rgb
        rgbhex = binascii.hexlify(struct.pack("BBBB", *rgba)).decode("ASCII")
        rgbhex = int(rgbhex, 16)

        if super()._lifesmart_epset(self, "0xff", rgbhex, self._idx) == 0:
            self._state = True
            self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        """Turn the light off."""
        if super()._lifesmart_epset(self, "0x80", 0, self._idx) == 0:
            self._state = False
            self.schedule_update_ha_state()
    @staticmethod
    def _lifesmart_GetRemoteList(self):
        appkey = self._appkey
        apptoken = self._apptoken
        usertoken = self._usertoken
        userid = self._userid
        agt = self._agt
        url = "https://api.ilifesmart.com/app/irapi.GetRemoteList"
        tick = int(time.time())
        sdata = "method:GetRemoteList,agt:"+agt+",time:"+str(tick)+",userid:"+userid+",usertoken:"+usertoken+",appkey:"+appkey+",apptoken:"+apptoken
        sign = hashlib.md5(sdata.encode(encoding='UTF-8')).hexdigest()
        send_values ={
          "id": 957,
          "method": "GetRemoteList",
          "params": {
              "agt": agt
          }, 
          "system": {
          "ver": "1.0",
          "lang": "en",
          "userid": userid,
          "appkey": appkey,
          "time": tick,
          "sign": sign
          }
        }
        header = {'Content-Type': 'application/json'}
        send_data = json.dumps(send_values)
        req = urllib.request.Request(url=url, data=send_data.encode('utf-8'), headers=header, method='POST')
        response = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
        return response['message']

    @staticmethod
    def _lifesmart_GetRemotes(self,ai):
        appkey = self._appkey
        apptoken = self._apptoken
        usertoken = self._usertoken
        userid = self._userid
        agt = self._agt
        url = "https://api.ilifesmart.com/app/irapi.GetRemote"
        tick = int(time.time())
        sdata = "method:GetRemote,agt:"+agt+",ai:"+ai+",needKeys:2,time:"+str(tick)+",userid:"+userid+",usertoken:"+usertoken+",appkey:"+appkey+",apptoken:"+apptoken
        sign = hashlib.md5(sdata.encode(encoding='UTF-8')).hexdigest()
        send_values ={
          "id": 957,
          "method": "GetRemote",
          "params": {
              "agt": agt,
              "ai": ai,
              "needKeys": 2
          },
          "system": {
          "ver": "1.0",
          "lang": "en",
          "userid": userid,
          "appkey": appkey,
          "time": tick,
          "sign": sign
          }
        }
        header = {'Content-Type': 'application/json'}
        send_data = json.dumps(send_values)
        req = urllib.request.Request(url=url, data=send_data.encode('utf-8'), headers=header, method='POST')
        response = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
        message = response.get('message')
        if isinstance(message, dict) and 'codes' in message:
            return message['codes']
        else:
            _LOGGER.warning("未返回 codes 字段，message 内容为：%s", message)
            return []
        return response['message']['codes']
