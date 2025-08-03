"""lifesmart by @skyzhishui"""
import subprocess
import urllib.request
import json
import time
import datetime
import hashlib
import logging
import threading
import websocket
import asyncio
import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .config_flow import LifeSmartConfigFlow
import logging
import pdb
from .supbowl import LifeSmartSupBowlAPI

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import discovery

_LOGGER = logging.getLogger(__name__)

from homeassistant.helpers.entity import Entity
from .entity import LifeSmartEntity

import voluptuous as vol
import sys
sys.setrecursionlimit(100000)

from homeassistant.const import (
    CONF_FRIENDLY_NAME,
)
from homeassistant.components.climate.const import (
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_DRY,
    SUPPORT_FAN_MODE,
    SUPPORT_TARGET_TEMPERATURE,
    HVAC_MODE_OFF,
)
from homeassistant.core import callback
from homeassistant.helpers import discovery
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.util.dt import utcnow

_LOGGER = logging.getLogger(__name__)
MAX_LOGIN_ATTEMPTS = 5  # 最大登录尝试次数
TOKEN_REFRESH_INTERVAL = 3600  # 每小时检查一次 Token 有效性

CONF_LIFESMART_APPKEY = "appkey"
CONF_LIFESMART_APPTOKEN = "apptoken"
CONF_LIFESMART_USERTOKEN = "usertoken"
CONF_LIFESMART_USERNAME = "username"
CONF_LIFESMART_PASSWORD = "password"
CONF_LIFESMART_USERID = "userid"
CONF_EXCLUDE_ITEMS = "exclude"
SWTICH_TYPES = ["SL_SF_RC",
"SL_SW_RC",
"SL_SW_IF3",
"SL_SF_IF3",
"SL_SW_CP3",
"SL_SW_RC3",
"SL_SW_IF2",
"SL_SF_IF2",
"SL_SW_CP2",
"SL_SW_FE2",
"SL_SW_RC2",
"SL_SW_ND2",
"SL_MC_ND2",
"SL_SW_IF1",
"SL_SF_IF1",
"SL_SW_CP1",
"SL_SW_FE1",
"SL_OL_W",
"SL_SW_RC1",
"SL_SW_ND1",
"SL_MC_ND1",
"SL_SW_ND3",
"SL_MC_ND3",
"SL_SW_ND2",
"SL_MC_ND2",
"SL_SW_ND1",
"SL_MC_ND1",
"SL_S",
"SL_SPWM",
"SL_P_SW",
"SL_SW_DM1",
"SL_SW_MJ2",
"SL_SW_MJ1",
"SL_OL",
"SL_OL_3C",
"SL_OL_DE",
"SL_OL_UK",
"SL_OL_UL",
"OD_WE_OT1",
"SL_NATURE"
]
LIGHT_SWITCH_TYPES = ["SL_OL_W",
"SL_SW_IF1",
"SL_SW_IF2",
"SL_SW_IF3",
]
QUANTUM_TYPES=["OD_WE_QUAN",
]

SPOT_TYPES = ["MSL_IRCTL",
"OD_WE_IRCTL",
"SL_SPOT"]
BINARY_SENSOR_TYPES = ["SL_SC_G",
"SL_SC_BG",
"SL_SC_MHW ",
"SL_SC_BM",
"SL_SC_CM",
"SL_P_A"]
COVER_TYPES = ["SL_DOOYA"]
GAS_SENSOR_TYPES = ["SL_SC_WA ",
"SL_SC_CH",
"SL_SC_CP",
"ELIQ_EM"]
EV_SENSOR_TYPES = ["SL_SC_THL",
"SL_SC_BE",
"SL_SC_CQ"]
OT_SENSOR_TYPES = ["SL_SC_MHW",
"SL_SC_BM",
"SL_SC_G",
"SL_SC_BG"]
LOCK_TYPES = ["SL_LK_LS",
"SL_LK_GTM",
"SL_LK_AG",
"SL_LK_SG",
"SL_LK_YL"]

SUPBOWL_TYPES = ["MSL_IRCTL",
"OD_WE_IRCTL",
"SL_SPOT",
"SL_P_IR"]

SPEED_OFF = "Speed_Off"
SPEED_LOW = "Speed_Low"
SPEED_MEDIUM = "Speed_Medium"
SPEED_HIGH = "Speed_High"

LIFESMART_STATE_LIST = [HVAC_MODE_OFF,
HVAC_MODE_AUTO,
HVAC_MODE_FAN_ONLY,
HVAC_MODE_COOL,
HVAC_MODE_HEAT,
HVAC_MODE_DRY]

CLIMATE_TYPES = ["V_AIR_P",
"SL_CP_DN"]

ENTITYID = 'entity_id'
DOMAIN = 'lifesmart_1'

LifeSmart_STATE_MANAGER = 'lifesmart_wss'

# from .const import (
#     CONF_LIFESMART_APPKEY,
#     CONF_LIFESMART_APPTOKEN,
#     CONF_LIFESMART_USERNAME,
#     CONF_LIFESMART_PASSWORD,
#     DOMAIN,
# )

# @config_entries.HOME_ASSISTANT_CORE
# class LifeSmartConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
#     """Handle a config flow for LifeSmart."""

#     VERSION = 1

#     async def async_step_user(self, user_input=None):
#         """Handle the initial step."""
#         if user_input is None:
#             return self.async_show_form(
#                 step_id="user",
#                 data_schema=vol.Schema(
#                     {
#                         vol.Required(CONF_LIFESMART_APPKEY): str,
#                         vol.Required(CONF_LIFESMART_APPTOKEN): str,
#                         vol.Required(CONF_LIFESMART_USERNAME): str,
#                         vol.Required(CONF_LIFESMART_PASSWORD): str,
#                     }
#                 ),
#             )

#         # Check if the configuration is valid
#         return self.async_create_entry(
#             title="LifeSmart Integration",
#             data=user_input,
#         )

async def lifesmart_refreshToken(hass: HomeAssistant, entry: ConfigEntry):
    userid = entry.data.get("userid")
    appkey = entry.data.get("appkey")
    url = "https://api.ilifesmart.com/app/auth.refreshtoken"
    tick = int(time.time())
    sdata = "method:refreshtoken,time:"+str(tick)+",userid:"+userid+",appkey:"+appkey
    sign = hashlib.md5(sdata.encode(encoding='UTF-8')).hexdigest()
    send_values ={
      "id": 1,
      "method": "refreshtoken",
      "system": {
      "ver": "1.0",
      "lang": "en",
      "userid": userid,
      "appkey": appkey,
      "time": tick,
      "sign": sign
      }
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=send_values) as response:
                data = await response.json()
                if data['code'] == 0:
                    hass.config_entries.async_update_entry(
                        entry,
                        data={
                            **entry.data,
                            "usertoken": data['usertoken'],
                            "expiredtime": data['expiredtime']
                        } 
                    )
                    return True
                else:
                    logging.error("Token validation failed: %s", data.get("message"))
                    return False
    except Exception as e:
        logging.error("Request error: %s", e)
        return False

async def lifesmart_EpGetAll(appkey,apptoken,usertoken,userid):
    url = "https://api.ilifesmart.com/app/api.EpGetAll"
    tick = int(time.time())
    sdata = "method:EpGetAll,time:"+str(tick)+",userid:"+userid+",usertoken:"+usertoken+",appkey:"+appkey+",apptoken:"+apptoken
    sign = hashlib.md5(sdata.encode(encoding='UTF-8')).hexdigest()
    send_values ={
      "id": 1,
      "method": "EpGetAll",
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
    # send_data = json.dumps(send_values)
    # req = urllib.request.Request(url=url, data=send_data.encode('utf-8'), headers=header, method='POST')
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=send_values, headers=header) as response:
                data = await response.json()
                if data['code'] == 0:
                    return data['message']
                else:
                    logging.error("Token validation failed: %s", data.get("message"))
                    return False
    except Exception as e:
        logging.error("Request errorh: %s", e)
        return False
    # response = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
    


def lifesmart_Sendkeys(appkey,apptoken,usertoken,userid,agt,ai,me,category,brand,keys):
    url = "https://api.ilifesmart.com/app/irapi.SendKeys"
    tick = int(time.time())
    #keys = str(keys)
    sdata = "method:SendKeys,agt:"+agt+",ai:"+ai+",brand:"+brand+",category:"+category+",keys:"+keys+",me:"+me+",time:"+str(tick)+",userid:"+userid+",usertoken:"+usertoken+",appkey:"+appkey+",apptoken:"+apptoken
    sign = hashlib.md5(sdata.encode(encoding='UTF-8')).hexdigest()
    _LOGGER.debug("sendkey: %s",str(sdata))
    send_values ={
      "id": 1,
      "method": "SendKeys",
      "params": {
          "agt": agt,
          "me": me,
          "category": category,
          "brand": brand,
          "ai": ai,
          "keys": keys
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
    _LOGGER.debug("sendkey_res: %s",str(response))
    return response
def lifesmart_Sendackeys(appkey,apptoken,usertoken,userid,agt,ai,me,category,brand,keys,power,mode,temp,wind,swing):                                                                             
    url = "https://api.ilifesmart.com/app/irapi.SendACKeys"                                                                                                        
    tick = int(time.time())       
    #keys = str(keys)
    sdata = "method:SendACKeys,agt:"+agt+",ai:"+ai+",brand:"+brand+",category:"+category+",keys:"+keys+",me:"+me+",mode:"+str(mode)+",power:"+str(power)+",swing:"+str(swing)+",temp:"+str(temp)+",wind:"+str(wind)+",time:"+str(tick)+",userid:"+userid+",usertoken:"+usertoken+",appkey:"+appkey+",apptoken:"+apptoken
    sign = hashlib.md5(sdata.encode(encoding='UTF-8')).hexdigest()     
    _LOGGER.debug("sendackey: %s",str(sdata))
    send_values ={                                                                                                                                                                                                 
      "id": 1,                                                                                                                                                                                                     
      "method": "SendACKeys",                                                                                                                                                                                        
      "params": {                                                                                                                                                                                                  
          "agt": agt,                                                                                                                                                                                              
          "me": me,                                                                                                                                                                                                
          "category": category,                                                                                                                                                                                    
          "brand": brand,                                                                                                                                                                                          
          "ai": ai,                                                                                                                                                                                                
          "keys": keys,
          "power": power,
          "mode": mode,
          "temp": temp,
          "wind": wind,
          "swing": swing                                                                                                                                                                                            
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
    _LOGGER.debug("sendackey_res: %s",str(response))
    return response 

def lifesmart_Login(uid,pwd,appkey):
    url = "https://api.ilifesmart.com/app/auth.login"
    login_data = {
      "uid": uid,
      "pwd": pwd,
      "appkey": appkey
    }
    header = {'Content-Type': 'application/json'}
    req = urllib.request.Request(url=url, data=json.dumps(login_data).encode('utf-8'),headers=header, method='POST')
    response = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
    return response

def lifesmart_doAuth(userid,token,appkey):
    url = "https://api.ilifesmart.com/app/auth.do_auth"
    auth_data = {
      "userid": userid,
      "token": token,
      "appkey": appkey,
      "rgn": "cn"
    }
    header = {'Content-Type': 'application/json'}
    req = urllib.request.Request(url=url, data=json.dumps(auth_data).encode('utf-8'),headers=header, method='POST')
    response = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
    return response

def store_device_info(hass, entry, dev):
    """Store device information to hass.data."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(entry.entry_id, {})
    hass.data[DOMAIN][entry.entry_id].setdefault("devices", [])
    hass.data[DOMAIN][entry.entry_id]["devices"].append(dev)

def lifesmart_timetick_comparer(tick):
    """Compare current time with tick."""
    current_time = int(time.time())
    if current_time > tick:
        return True
    
    

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up LifeSmart integration from a config entry."""
    # 获取配置信息
    hass.data.setdefault(DOMAIN, {})
    param = entry.data
    # _LOGGER.error("entry.data in async_setup_entry: %s", entry.data)
    appkey = param['appkey']
    apptoken = param['apptoken']
    userid = param['userid']
    login_attempts = 0 
    while login_attempts < MAX_LOGIN_ATTEMPTS:
        try:
            # 尝试登录并获取设备列表s
            lifesmart_config_flow = LifeSmartConfigFlow()
            response_login = await lifesmart_config_flow.lifesmart_Login(entry.data['username'], entry.data['password'], entry.data['appkey'])
            if response_login:
                userid = response_login['userid']
                token = response_login['token']
                response_auth = await lifesmart_config_flow.lifesmart_doAuth(userid, token, appkey)
                if response_auth:
                    usertoken = response_auth['usertoken']
                    expiredtime = response_auth['expiredtime']
                    hass.config_entries.async_update_entry(
                        entry,
                        data={
                            **entry.data,
                            "usertoken": usertoken,
                            "expiredtime": expiredtime
                        }    
                    )
                    break
                else:
                    _LOGGER.error("Failed to authenticate with the token.")
                    login_attempts += 1
            else:
                _LOGGER.error("Failed to log in.")
                login_attempts +=1
        except Exception as e:
            _LOGGER.error(f"Error during setup: {e}")
            login_attempts +=1
    if login_attempts >= MAX_LOGIN_ATTEMPTS:
        _LOGGER.error("Failed to set up after multiple attempts.")
        return False
    #刷新usertoken和expiredtime
    param = entry.data
    usertoken = param['usertoken']
    expiredtime = param['expiredtime']
    
    # 获取设备列表
    devices = await lifesmart_EpGetAll(appkey, apptoken, usertoken, userid)
    if not devices:
        _LOGGER.error("Failed to get device list.")
        return False
    # 存储设备信息
    hass.data[DOMAIN][entry.entry_id] = {
        "devices": devices,
        "config": param
    }
    
    ''' compare the time now with expiredtime, then if the time now newer than expiredtime, refresh the usertoken'''
    if lifesmart_timetick_comparer(param["expiredtime"]):
        logging.info("Token expired, refreshing...")
        #刷新Token
        refreshResult = lifesmart_refreshToken(hass, entry)
        # 刷新 token 成功后，更新配置条目
        usertoken = refreshResult['usertoken']
        expiredtime = refreshResult['expiredtime']
        if not refreshResult :
            logging.error("Token refresh failed.Please Check your config and reset integration.")
            return False
    
    exclude_items = entry.data.get('exclude', [])

    PLATFORMS = ["switch", "binary_sensor", "cover", "light", "climate", "sensor"]

    # 存储 devices 到 hass.data
    hass.data[DOMAIN][entry.entry_id] = {
        "devices": devices,
        "config": param
    }

    # 一次性加载每个平台（不再按设备类型判断）
    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )
    #添加超级碗
    devices = hass.data[DOMAIN][entry.entry_id].get("devices",None)
    for device in devices:
        # pdb.set_trace()
        if device.get('devtype',None) in SUPBOWL_TYPES:
            supbowl_api = LifeSmartSupBowlAPI(
                appkey=entry.data["appkey"],
                apptoken=entry.data["apptoken"],
                usertoken=entry.data["usertoken"],
                userid=entry.data["userid"],
                agt=device.get('agt',None),
                me=device.get('me',None),
            )
            remotes = await hass.async_add_executor_job(supbowl_api.get_remote_list)
            
            remote_buttons = {}
            for ai, info in remotes.items():
                detail = await hass.async_add_executor_job(supbowl_api.get_remote_detail, ai)
                # detail.keys 例：["POWER", "MUTE", ...]  detail.codes: 每个键的红外码
                remote_buttons[ai] = detail.get("keys", [])
            # pdb.set_trace()
    # 缓存
    hass.data[DOMAIN][entry.entry_id]["supbowl_api"] = supbowl_api
    hass.data[DOMAIN][entry.entry_id]["remotes"] = remotes
    hass.data[DOMAIN][entry.entry_id]["remote_buttons"] = remote_buttons

    # 转发到button.py
    await hass.config_entries.async_forward_entry_setup(entry, "button")

    

    def send_keys(call):
        """Handle the service call."""
        agt = call.data['agt']
        me = call.data['me']
        ai = call.data['ai']
        category = call.data['category']
        brand = call.data['brand']
        keys = call.data['keys']
        restkey = lifesmart_Sendkeys(param['appkey'],param['apptoken'],param['usertoken'],param['userid'],agt,ai,me,category,brand,keys)
        _LOGGER.debug("sendkey: %s",str(restkey))
    def send_ackeys(call):
        """Handle the service call."""
        agt = call.data['agt']
        me = call.data['me']
        ai = call.data['ai']
        category = call.data['category']
        brand = call.data['brand']
        keys = call.data['keys']
        power = call.data['power']
        mode = call.data['mode']
        temp = call.data['temp']
        wind = call.data['wind']
        swing = call.data['swing']
        restackey = lifesmart_Sendackeys(param['appkey'],param['apptoken'],param['usertoken'],param['userid'],agt,ai,me,category,brand,keys,power,mode,temp,wind,swing)
        _LOGGER.debug("sendkey: %s",str(restackey))
    
    def get_fan_mode(_fanspeed):
        fanmode = None
        if _fanspeed < 30:
            fanmode = SPEED_LOW
        elif _fanspeed < 65 and _fanspeed >= 30:
            fanmode = SPEED_MEDIUM
        elif _fanspeed >=65:
            fanmode = SPEED_HIGH
        return fanmode
    
    def safe_update_state(hass, enid, new_state=None, patch_attrs=None, logger=None):
        """安全地更新 HA 的状态，不会因实体未注册而抛出异常。"""
        entity = hass.states.get(enid)
        if entity is None:
            if logger:
                logger.warning("Entity not found, skip update: %s", enid)
            return
        attrs = dict(entity.attributes)
        if patch_attrs:
            attrs.update(patch_attrs)
        hass.states.set(enid, new_state or entity.state, attrs)

    
    async def set_Event(msg):
        if msg['msg']['idx'] != "s" and msg['msg']['me'] not in exclude_items:
            devtype = msg['msg']['devtype']
            agt = msg['msg']['agt'].replace("_","")
            me = msg['msg']['me']
            idx = msg['msg']['idx']
            enid = None
            if devtype in SWTICH_TYPES and idx in ["L1","L2","L3","P1","P2","P3"]:
                enid = "switch."+(devtype + "_" + agt + "_" + me + "_" + idx).lower()
                attrs = hass.states.get(enid).attributes
                if msg['msg']['type'] % 2 == 1:
                    state = 'on'
                    # hass.states.set(enid, 'on',attrs)
                else:
                    state = 'off'
                    # hass.states.set(enid, 'off',attrs)
                safe_update_state(hass, enid, state, logger=_LOGGER)
            elif devtype in BINARY_SENSOR_TYPES and idx in ["M","G","B","AXS","P1"]:
                enid = "binary_sensor."+(devtype + "_" + agt + "_" + me + "_" + idx).lower()
                attrs = hass.states.get(enid).attributes
                if msg['msg']['val'] == 1:
                    # hass.states.set(enid, 'on',attrs)
                    state = 'on'
                else:
                    state = 'off'
                    # hass.states.set(enid, 'off',attrs)
                safe_update_state(hass, enid, state, logger=_LOGGER)
            elif devtype in COVER_TYPES and idx == "P1":
                enid = "cover."+(devtype + "_" + agt + "_" + me).lower()
                attrs = dict(hass.states.get(enid).attributes)
                nval = msg['msg']['val']
                ntype = msg['msg']['type']
                attrs['current_position'] = nval & 0x7F
                _LOGGER.debug("websocket_cover_attrs: %s",str(attrs))
                nstat = None
                if ntype % 2 == 0:
                    if nval > 0:
                        nstat = "open"
                    else:
                        nstat = "closed"
                else:
                    if nval & 0x80 == 0x80:
                        nstat = "opening"
                    else:
                        nstat = "closing"
                safe_update_state(hass, enid, nstat, attrs['current_position'], logger=_LOGGER)
                # hass.states.set(enid, nstat, attrs)
            elif devtype in EV_SENSOR_TYPES:
                enid = "sensor."+(devtype + "_" + agt + "_" + me + "_" + idx).lower()
                # attrs = hass.states.get(enid).attributes
                # hass.states.set(enid, msg['msg']['v'], attrs)
                safe_update_state(hass, enid, msg['msg']['v'], logger=_LOGGER)
            elif devtype in GAS_SENSOR_TYPES and msg['msg']['val'] > 0:
                enid = "sensor."+(devtype + "_" + agt + "_" + me + "_" + idx).lower()
                # attrs = hass.states.get(enid).attributes
                # hass.states.set(enid, msg['msg']['val'], attrs)
                safe_update_state(hass, enid, msg['msg']['val'], logger=_LOGGER)
            elif devtype in SPOT_TYPES or devtype in LIGHT_SWITCH_TYPES:
                enid = "light."+(devtype + "_" + agt + "_" + me + "_" + idx).lower()
                attrs = hass.states.get(enid).attributes
                if msg['msg']['type'] % 2 == 1:
                    # hass.states.set(enid, 'on',attrs)
                    state = 'on'
                else:
                    hass.states.set(enid, 'off',attrs)
                    state = 'off'
                safe_update_state(hass, enid, state, logger=_LOGGER)
                
            #elif devtype in QUANTUM_TYPES and idx == "P1":
            #    enid = "light."+(devtype + "_" + agt + "_" + me + "_P1").lower()
            #    attrs = hass.states.get(enid).attributes
            #    hass.states.set(enid, msg['msg']['val'], attrs)
            elif devtype in CLIMATE_TYPES:
                enid = "climate."+(devtype + "_" + agt + "_" + me).lower().replace(":","_").replace("@","_")
                #climate.v_air_p_a3yaaabbaegdrzcznti3mg_8ae5_1_2_1
                _idx = idx
                attrs = dict(hass.states.get(enid).attributes)
                nstat = hass.states.get(enid).state
                _LOGGER.info("enid: %s",str(enid))
                _LOGGER.info("_idx: %s",str(_idx))
                _LOGGER.info("attrs: %s",str(attrs))
                _LOGGER.info("nstat: %s",str(nstat))
                if _idx == "O":
                  if msg['msg']['type'] % 2 == 1:
                    nstat = attrs['last_mode']
                    # hass.states.set(enid, nstat, attrs)
                  else:
                    nstat = HVAC_MODE_OFF
                    # hass.states.set(enid, nstat, attrs)
                  safe_update_state(hass, enid, nstat, logger=_LOGGER)
                if _idx == "P1":
                  if msg['msg']['type'] % 2 == 1:
                    nstat = HVAC_MODE_HEAT
                    # hass.states.set(enid, nstat, attrs)
                  else:
                    nstat = HVAC_MODE_OFF
                    # hass.states.set(enid, nstat, attrs)
                  safe_update_state(hass, enid, nstat, logger=_LOGGER)
                if _idx == "P2":
                  if msg['msg']['type'] % 2 == 1:
                    attrs['Heating'] = "true"
                    # hass.states.set(enid, nstat, attrs)
                  else:
                    attrs['Heating'] = "false"
                    # hass.states.set(enid, nstat, attrs)
                  safe_update_state(hass, enid, nstat, attrs, logger=_LOGGER)
                elif _idx == "MODE":
                  if msg['msg']['type'] == 206:
                    if nstat != HVAC_MODE_OFF:
                      nstat = LIFESMART_STATE_LIST[msg['msg']['val']]
                    attrs['last_mode'] = LIFESMART_STATE_LIST[msg['msg']['val']]
                    # hass.states.set(enid, nstat, attrs)
                    safe_update_state(hass, enid, nstat, attrs, logger=_LOGGER)
                elif _idx == "F":
                  if msg['msg']['type'] == 206:
                    attrs['fan_mode'] = get_fan_mode(msg['msg']['val'])
                    # hass.states.set(enid, nstat, attrs)
                    safe_update_state(hass, enid, nstat, attrs, logger=_LOGGER)
                elif _idx == "tT" or _idx == "P3":
                  if msg['msg']['type'] == 136:
                    attrs['temperature'] = msg['msg']['v']
                    # hass.states.set(enid, nstat, attrs)
                    safe_update_state(hass, enid, nstat, attrs, logger=_LOGGER)
                elif _idx == "T" or _idx == "P4":
                  if msg['msg']['type'] == 8 or msg['msg']['type'] == 9:
                    attrs['current_temperature'] = msg['msg']['v']
                    # hass.states.set(enid, nstat, attrs)
                    safe_update_state(hass, enid, nstat, attrs, logger=_LOGGER)
            elif devtype in LOCK_TYPES:
                if idx == "BAT":
                    enid = "sensor."+(devtype + "_" + agt + "_" + me + "_" + idx).lower()
                    attrs = hass.states.get(enid).attributes
                    # hass.states.set(enid, msg['msg']['val'], attrs)
                    safe_update_state(hass, enid, msg['msg']['val'], attrs, logger=_LOGGER)
                elif idx == "EVTLO":
                    enid = "binary_sensor."+(devtype + "_" + agt + "_" + me + "_" + idx).lower()
                    val = msg['msg']['val']
                    ulk_way = val >> 12
                    ulk_user = val & 0xfff
                    ulk_success = True
                    if ulk_user == 0:
                        ulk_success = False
                    attrs = {"unlocking_way": ulk_way,"unlocking_user": ulk_user,"devtype": devtype,"unlocking_success": ulk_success,"last_time": datetime.datetime.fromtimestamp(msg['msg']['ts']/1000).strftime("%Y-%m-%d %H:%M:%S") }
                    if msg['msg']['type'] % 2 == 1:
                        # hass.states.set(enid, 'on',attrs)
                        state = 'on'
                    else:
                        hass.states.set(enid, 'off',attrs)
                        state = 'off'
                    safe_update_state(hass, enid, state, logger=_LOGGER)
            if devtype in OT_SENSOR_TYPES and idx in ["Z","V","P3","P4"]:
                enid = "sensor."+(devtype + "_" + agt + "_" + me + "_" + idx).lower()
                attrs = hass.states.get(enid).attributes
                # hass.states.set(enid, msg['msg']['v'], attrs)
                safe_update_state(hass, enid, msg['msg']['v'], attrs, logger=_LOGGER)
    def on_message(ws, message):
        _LOGGER.warning("websocket_msg: %s",str(message))
        msg = json.loads(message)
        if 'type' not in msg:
            return
        if msg['type'] != "io":
            return
        asyncio.run(set_Event(msg))

    def on_error(ws, error):
        _LOGGER.debug("websocket_error: %s",str(error))

    def on_close(ws):
        _LOGGER.debug("lifesmart websocket closed...")
        
    def on_open(ws):
        tick = int(time.time())
        sdata = "method:WbAuth,time:"+str(tick)+",userid:"+param['userid']+",usertoken:"+param['usertoken']+",appkey:"+param['appkey']+",apptoken:"+param['apptoken']
        sign = hashlib.md5(sdata.encode(encoding='UTF-8')).hexdigest()
        send_values ={
        "id": 1,
        "method": "WbAuth",
        "system": {
        "ver": "1.0",
        "lang": "en",
        "userid": param['userid'],
        "appkey": param['appkey'],
        "time": tick,
        "sign": sign
        }
        }
        header = {'Content-Type': 'application/json'}
        send_data = json.dumps(send_values)
        ws.send(send_data)
        _LOGGER.debug("lifesmart websocket sending_data...")

    # hass.services.register(DOMAIN, 'send_keys', send_keys)
    # hass.services.register(DOMAIN, 'send_ackeys', send_ackeys)
    ws = websocket.WebSocketApp("wss://api.ilifesmart.com:8443/wsapp/",
                          on_message = on_message,
                          on_error = on_error,
                          on_close = on_close)
    ws.on_open = on_open
    hass.data[LifeSmart_STATE_MANAGER] = LifeSmartStatesManager(ws = ws)
    hass.data[LifeSmart_STATE_MANAGER].start_keep_alive()
    return True

# class LifeSmartEntity(Entity):
#     """LifeSmart base device."""

#     def __init__(self, dev, idx, val, ver, param):
#         """Initialize the switch."""
#         self._name = dev['name'] + "_" + idx
#         self._appkey = param['appkey']
#         self._apptoken = param['apptoken']
#         self._usertoken = param['usertoken']
#         self._userid = param['userid']
#         self._agt = dev['agt']
#         self._me = dev['me']
#         self._idx = idx
#         self._devtype = dev['devtype']
#         attrs = {"agt": self._agt,"me": self._me,"idx": self._idx,"devtype": self._devtype }
#         self._attributes = attrs
#         self._ver = ver
        

#     @property
#     def object_id(self):
#         """Return LifeSmart device id."""
#         return self.entity_id

#     @property
#     def state_attrs(self):
#         """Return the state attributes."""
#         return self._attributes

#     @property
#     def extra_state_attributes(self):
#         """Return the extra state attributes of the device."""
#         return self._attributes

#     @property
#     def name(self):
#         """Return LifeSmart device name."""
#         return self._name

#     @property
#     def assumed_state(self):
#         """Return true if we do optimistic updates."""
#         return False

#     @property
#     def should_poll(self):
#         """check with the entity for an updated state."""
#         return False


#     @staticmethod
#     def _lifesmart_epset(self, type, val, idx):
#         #self._tick = int(time.time())
#         url = "https://api.ilifesmart.com/app/api.EpSet"
#         tick = int(time.time())
#         appkey = self._appkey
#         apptoken = self._apptoken
#         userid = self._userid
#         usertoken = self._usertoken
#         agt = self._agt
#         me = self._me
#         sdata = "method:EpSet,agt:"+ agt +",idx:"+idx+",me:"+me+",type:"+type+",val:"+str(val)+",time:"+str(tick)+",userid:"+userid+",usertoken:"+usertoken+",appkey:"+appkey+",apptoken:"+apptoken
#         sign = hashlib.md5(sdata.encode(encoding='UTF-8')).hexdigest()
#         send_values = {
#           "id": 1,
#           "method": "EpSet",
#           "system": {
#           "ver": "1.0",
#           "lang": "en",
#           "userid": userid,
#           "appkey": appkey,
#           "time": tick,
#           "sign": sign
#           },
#           "params": {
#           "agt": agt,
#           "me": me,
#           "idx": idx,
#           "type": type,
#           "val": val
#           }
#         }
#         header = {'Content-Type': 'application/json'}
#         send_data = json.dumps(send_values)
#         req = urllib.request.Request(url=url, data=send_data.encode('utf-8'), headers=header, method='POST')
#         response = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
#         _LOGGER.info("epset_send: %s",str(send_data))
#         _LOGGER.info("epset_res: %s",str(response))
#         return response['code']

#     @staticmethod
#     def _lifesmart_epget(self):
#         url = "https://api.ilifesmart.com/app/api.EpGet"
#         tick = int(time.time())
#         appkey = self._appkey
#         apptoken = self._apptoken
#         userid = self._userid
#         usertoken = self._usertoken
#         agt = self._agt
#         me = self._me
#         sdata = "method:EpGet,agt:"+ agt +",me:"+ me +",time:"+str(tick)+",userid:"+userid+",usertoken:"+usertoken+",appkey:"+appkey+",apptoken:"+apptoken
#         sign = hashlib.md5(sdata.encode(encoding='UTF-8')).hexdigest()
#         send_values = {
#           "id": 1,
#           "method": "EpGet",
#           "system": {
#           "ver": "1.0",
#           "lang": "en",
#           "userid": userid,
#           "appkey": appkey,
#           "time": tick,
#           "sign": sign
#           },
#           "params": {
#           "agt": agt,
#           "me": me
#           }
#         }
#         header = {'Content-Type': 'application/json'}
#         send_data = json.dumps(send_values)
#         req = urllib.request.Request(url=url, data=send_data.encode('utf-8'), headers=header, method='POST')
#         response = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
#         return response['message']['data']

class LifeSmartStatesManager(threading.Thread):


    def __init__(self, ws):
        """Init LifeSmart Update Manager."""
        threading.Thread.__init__(self)
        self._run = False
        self._lock = threading.Lock()
        self._ws = ws

    def run(self):
        while self._run:
            _LOGGER.debug('lifesmart: starting wss...')
            self._ws.run_forever()
            _LOGGER.debug('lifesmart: restart wss...')
            time.sleep(10)

    def start_keep_alive(self):
        """Start keep alive mechanism."""
        with self._lock:
            self._run = True
            threading.Thread.start(self)

    def stop_keep_alive(self):
        """Stop keep alive mechanism."""
        with self._lock:
            self._run = False
            self.join()
