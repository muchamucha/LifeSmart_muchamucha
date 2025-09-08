"""Support for the LifeSmart climate devices."""
import logging
import time
from homeassistant.core import callback
from homeassistant.components.climate import ENTITY_ID_FORMAT, ClimateEntity
from homeassistant.components.climate.const import (
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_DRY,
    SUPPORT_FAN_MODE,
    SUPPORT_TARGET_TEMPERATURE,
    HVAC_MODE_OFF,
    SUPPORT_SWING_MODE
)

from homeassistant.const import (
    ATTR_TEMPERATURE,
    PRECISION_WHOLE,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)

from .entity import LifeSmartEntity
from .supbowl import LifeSmartSupBowlAPI
DOMAIN = "lifesmart_1"
_LOGGER = logging.getLogger(__name__)
DEVICE_TYPE = "climate"

LIFESMART_STATE_LIST = [HVAC_MODE_OFF,
HVAC_MODE_AUTO,
HVAC_MODE_FAN_ONLY,
HVAC_MODE_COOL,
HVAC_MODE_HEAT,
HVAC_MODE_DRY]

LIFESMART_STATE_LIST2 = [HVAC_MODE_OFF,
HVAC_MODE_HEAT]

SPEED_OFF = "Speed_Off"
SPEED_LOW = "Speed_Low"
SPEED_MEDIUM = "Speed_Medium"
SPEED_HIGH = "Speed_High"

FAN_MODES = [SPEED_LOW, SPEED_MEDIUM, SPEED_HIGH]
GET_FAN_SPEED = { SPEED_LOW:15, SPEED_MEDIUM:45, SPEED_HIGH:76 }

AIR_TYPES=["V_AIR_P"]

THER_TYPES = ["SL_CP_DN"]

LS_MODE_TO_HA = {0: HVAC_MODE_AUTO, 1: HVAC_MODE_COOL, 2: HVAC_MODE_DRY, 3: HVAC_MODE_FAN_ONLY, 4: HVAC_MODE_HEAT}
HA_MODE_TO_LS = {v: k for k, v in LS_MODE_TO_HA.items()}
HA_FAN_TO_WIND = {"auto": 0, "low": 1, "medium": 2, "high": 3}
WIND_TO_HA_FAN = {v: k for k, v in HA_FAN_TO_WIND.items()}
HA_SWING_TO_LS = {"auto": 0, "1": 1, "2": 2, "3": 3, "4": 4}
SWING_TO_HA = {v: k for k, v in HA_SWING_TO_LS.items()}

# def setup_platform(hass, config, add_entities, discovery_info=None):
#     """Set up LifeSmart Climate devices."""
#     breakpoint()
#     if discovery_info is None:
#         return
#     devices = []
#     dev = discovery_info.get("dev")
#     param = discovery_info.get("param")
#     devices = []
#     if "T" not in dev['data'] and "P3" not in dev['data']:
#         return
#     devices.append(LifeSmartClimateEntity(dev,"idx","0",param))
#     breakpoint()
#     add_entities(devices)

async def async_setup_entry(hass, config, async_add_entities):
    """Perform the setup for LifeSmart devices."""
    devices = []
    data = hass.data[DOMAIN][config.entry_id]
    dev_data = data.get('devices',None)
    param = data.get('config',None)
    remotes = data.get("remotes",None)
    api = data.get("supbowl_api",None)
    coord = data.get("coordinator",None)
    # 检查设备的 data 字段是否存在
    if not data:
        _LOGGER.error("Device data not found in dev: %s", data)
        return False
    for device in dev_data:
        if device['devtype'] in AIR_TYPES or device['devtype'] in THER_TYPES:
            if "T" not in device['data'] and "P3" not in device['data']:
                continue
            for idx in device['data']:
                devices.append(LifeSmartClimateEntity(device,idx,device['data'][idx],device['agt_ver'],param))
    for ai, info in remotes.items():
        if info.get("category") != "ac":
            continue
        remote_name = info.get("name") or f"AC-{ai}"
        brand = info.get("brand") or "unknown"
        state = await hass.async_add_executor_job(api.get_ac_remote_state, ai)
        devices.append(
            LifeSmartAcRemoteEntity(
                ai = ai,
                name = remote_name,
                brand = brand,
                api = api,
                init_state = state or {},
                coord = coord
            )
        )
    async_add_entities(devices)
    _LOGGER.debug("Total devices to add: %d", len(devices))
    _LOGGER.debug("Raw dev_data: %s", dev_data)
    _LOGGER.debug("Device data: %s", device)
    return True

class LifeSmartClimateEntity(LifeSmartEntity, ClimateEntity):
    """LifeSmart climate devices,include air conditioner,heater."""

    def __init__(self, dev, idx, val, ver, param):
        """Init LifeSmart cover device."""
        super().__init__(dev, idx, val, ver, param)
        # self._name = dev['name']
        # self._ver = ver
        # self._supbowl = hass.data.get(DOMAIN,{}).get("supbowl")
        # self._ai = dev.get("ai")
        # self._brand = dev.get("brand")
        # self._idx = dev.get("idx")
        # self._use_ir = bool(self._supbowl and self._ai and self._brand)

        cdata = dev['data']        #_LOGGER.info("climate.py_cdata: %s",str(cdata))
        self.entity_id = ENTITY_ID_FORMAT.format(( dev['devtype'] + "_" + dev['agt'] + "_" + dev['me']).lower().replace(":","_").replace("@","_"))
        if dev['devtype'] in AIR_TYPES:
            self._modes = LIFESMART_STATE_LIST
            if cdata['O']['type'] % 2 == 0:
                self._mode = LIFESMART_STATE_LIST[0]
            else:
                self._mode = LIFESMART_STATE_LIST[cdata['MODE']['val']]
            self._attributes.update({"last_mode": LIFESMART_STATE_LIST[cdata['MODE']['val']]})
            _LOGGER.info("climate.py_self._attributes: %s",str(self._attributes))
            self._current_temperature = cdata['T']['v']
            self._target_temperature = cdata['tT']['v']
            self._min_temp = 10
            self._max_temp = 35
            self._fanspeed = cdata['F']['val']
        else:
            self._modes = LIFESMART_STATE_LIST2
            if cdata['P1']['type'] % 2 == 0:
                self._mode = LIFESMART_STATE_LIST2[0]
            else:
                self._mode = LIFESMART_STATE_LIST2[1]
            if cdata['P2']['type'] % 2 == 0:
                self._attributes.setdefault('Heating',"false")
            else:
                self._attributes.setdefault('Heating',"true")
            self._current_temperature = cdata['P4']['val'] / 10
            self._target_temperature = cdata['P3']['val'] / 10
            self._min_temp = 5
            self._max_temp = 35

    @property
    def precision(self):
        """Return the precision of the system."""
        return PRECISION_WHOLE

    @property
    def temperature_unit(self):
        """Return the unit of measurement used by the platform."""
        return TEMP_CELSIUS

    @property
    def hvac_mode(self):
        """Return current operation ie. heat, cool, idle."""
        return self._mode

    @property
    def hvac_modes(self):
        """Return the list of available operation modes."""
        return self._modes

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._current_temperature

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return 1

    @property
    def fan_mode(self):
        """Return the fan setting."""
        fanmode = None
        if self._fanspeed < 30:
            fanmode = SPEED_LOW
        elif self._fanspeed < 65 and self._fanspeed >= 30:
            fanmode = SPEED_MEDIUM
        elif self._fanspeed >=65:
            fanmode = SPEED_HIGH
        return fanmode

    @property
    def fan_modes(self):
        """Return the list of available fan modes."""
        return FAN_MODES
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

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        new_temp = int(kwargs['temperature']*10)
        _LOGGER.info("set_temperature: %s",str(new_temp))
        if self._devtype in AIR_TYPES:
            super()._lifesmart_epset(self, "0x88", new_temp, "tT")
        else:
            super()._lifesmart_epset(self, "0x88", new_temp, "P3")

    def set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        super()._lifesmart_epset(self, "0xCE", GET_FAN_SPEED[fan_mode], "F")

    def set_hvac_mode(self, hvac_mode):
        """Set new target operation mode."""
        if self._devtype in AIR_TYPES:
            if hvac_mode == HVAC_MODE_OFF:
                super()._lifesmart_epset(self, "0x80", 0, "O")
                return
            if self._mode == HVAC_MODE_OFF:
                if super()._lifesmart_epset(self, "0x81", 1, "O") == 0:
                    time.sleep(2)
                else:
                    return
            super()._lifesmart_epset(self, "0xCE", LIFESMART_STATE_LIST.index(hvac_mode), "MODE")
        else:
            if hvac_mode == HVAC_MODE_OFF:
                super()._lifesmart_epset(self, "0x80", 0, "P1")
                time.sleep(1)
                super()._lifesmart_epset(self, "0x80", 0, "P2")
                return
            else:
                if super()._lifesmart_epset(self, "0x81", 1, "P1") == 0:
                    time.sleep(2)
                else:
                    return
            


    @property
    def supported_features(self):
        """Return the list of supported features."""
        if self._devtype in AIR_TYPES:
            return SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE
        else:
            return SUPPORT_TARGET_TEMPERATURE

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return self._min_temp

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return self._max_temp

class LifeSmartAcRemoteEntity(ClimateEntity):
    _attr_temperature_unit = TEMP_CELSIUS
    _attr_target_temperature_step = 1
    def __init__(self, ai, name, brand, api, init_state: dict, coord):
        self._attr_name = name
        self._attr_unique_id = f"{ai}-climate"
        self._ai = ai
        self._brand = brand
        self._api = api
        self.coord = coord
        # IR 全码缓存（先用回读值初始化，缺省兜底）
        st = coord.data.get(ai, {}) or {}
        self._power = int(st.get("power", 1))
        self._mode  = int(st.get("mode",  1))
        self._temp  = int(st.get("temp",  26))
        self._wind  = int(st.get("wind",  0))
        self._swing = int(st.get("swing", 0))
        

        # 支持能力：温度必开；风速/摆风先给默认，后续你可在 async_added_to_hass 里探测再调
        self._attr_supported_features = SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE | SUPPORT_SWING_MODE
        self._attr_hvac_modes = [HVAC_MODE_OFF, HVAC_MODE_AUTO, HVAC_MODE_COOL, HVAC_MODE_HEAT, HVAC_MODE_DRY, HVAC_MODE_FAN_ONLY]
        self._attr_fan_modes = list(HA_FAN_TO_WIND.keys())
        self._attr_swing_modes = list(HA_SWING_TO_LS.keys())
    # 只读属性映射
    @property
    def hvac_mode(self):
        if self._power == 0:
            return HVAC_MODE_OFF
        return LS_MODE_TO_HA.get(self._mode, HVAC_MODE_AUTO)

    @property
    def target_temperature(self):
        return self._temp

    @property
    def fan_mode(self):
        return WIND_TO_HA_FAN.get(self._wind, "auto")

    @property
    def swing_mode(self):
        return SWING_TO_HA.get(self._swing, "auto")
    
    async def async_added_to_hass(self):
        self.async_on_remove(self.coord.async_add_listener(self._handle_coordinator_update))
    
    @callback
    def _handle_coordinator_update(self):
        st = self.coord.data.get(self._ai) or {}
        if st:
            self._power = int(st.get("power", self._power))
            self._mode  = int(st.get("mode",  self._mode))
            self._temp  = int(st.get("temp",  self._temp))
            self._wind  = int(st.get("wind",  self._wind))
            self._swing = int(st.get("swing", self._swing))
            self.async_write_ha_state()
            
    async def _apply(self, key_hint: str):
        if not self._api:
            # 兼容旧逻辑：沿用你现有的 _lifesmart_epset
            # 假设你已有方法：await self._lifesmart_epset({...})
            await self._lifesmart_epset({
                "key": key_hint,
                "power": self._power, "mode": self._mode,
                "temp": self._temp, "wind": self._wind, "swing": self._swing,
            })
            return

        # IR 路径（requests → 线程池执行）
        ok = await self.hass.async_add_executor_job(
            self._api.send_ac_keys,
            self._ai, "ac", self._brand, key_hint,
            int(self._power), int(self._mode), int(self._temp), int(self._wind), int(self._swing),
        )
        if not ok:
            # 回滚并强制同步，避免 UI 与实物不一致
            await self.coord.async_request_refresh()
            # 这里可按你项目风格 raise/日志
    
    async def async_set_hvac_mode(self, hvac_mode):
        if hvac_mode == HVAC_MODE_OFF:
            self._power = 0
            return await self._apply("power")
        self._power = 1
        self._mode = HA_MODE_TO_LS.get(hvac_mode, 0)
        await self._apply("mode")

    async def async_set_temperature(self, **kwargs):
        t = kwargs.get("temperature")
        if t is None:
            return
        self._temp = int(t)
        await self._apply("temp")

    async def async_set_fan_mode(self, fan_mode):
        self._wind = HA_FAN_TO_WIND.get(fan_mode, 0)
        await self._apply("wind")

    async def async_set_swing_mode(self, swing_mode):
        self._swing = HA_SWING_TO_LS.get(swing_mode, 0)
        await self._apply("swing")

    async def async_update(self):
        if not self._api:
            # 你的原有获取状态逻辑
            return
        state = await self.hass.async_add_executor_job(self._api.get_ac_remote_state, self._ai)
        if not state:
            return
        self._power = int(state.get("power", self._power))
        self._mode  = int(state.get("mode",  self._mode))
        self._temp  = int(state.get("temp",  self._temp))
        self._wind  = int(state.get("wind",  self._wind))
        self._swing = int(state.get("swing", self._swing))
    
