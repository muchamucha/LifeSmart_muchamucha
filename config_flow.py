import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
import logging
import aiohttp
import time
import hashlib
import json
import pdb


_LOGGER = logging.getLogger(__name__)

# 在此处直接定义配置项，而不使用 const.py
CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required("username"): str,
        vol.Required("password"): str,
        vol.Required("appkey"): str,
        vol.Required("apptoken"): str,
        vol.Required("exclude"): str,
    },
    extra=vol.ALLOW_EXTRA,
)

class LifeSmartConfigFlow(config_entries.ConfigFlow, domain="lifesmart_1"):
    """处理 LifeSmart 的配置流"""

    VERSION = 1

    def __init__(self):
        """初始化配置流"""
        self._username = None
        self._password = None
        self._appkey = None
        self._apptoken = None
        self._exclude = None
        self._userid = None
        self._usertoken = None
        self._expiredtime = None

    async def async_step_user(self, user_input=None):
        """处理用户输入"""
        if user_input is not None:
            # 获取用户输入的配置
            self._username = user_input["username"]
            self._password = user_input["password"]
            self._appkey = user_input["appkey"]
            self._apptoken = user_input["apptoken"]
            self._exclude = user_input["exclude"]
            self._userid = ""
            self._usertoken = ""
            self._expiredtime = ""
            # 验证用户的登录信息
            response_login = await self.lifesmart_Login(self._username, self._password, self._appkey)

            try:
                self._userid = response_login['userid']
                self._usertoken = response_login['token']    
            except:
                return self.async_show_form(
                    step_id="user",
                    data_schema=CONFIG_SCHEMA,
                    errors={"base": "Login failed: %s"%response_login['message']},
                )

            
            # 授权用户登录
            response_auth =await self.lifesmart_doAuth(self._userid, self._usertoken, self._appkey)

            try:
                self._usertoken = response_auth['usertoken']
                self._expiredtime = response_auth['expiredtime']
            except:
                return self.async_show_form(
                    step_id="user",
                    data_schema=CONFIG_SCHEMA,
                    errors={"base": "Auth failed: %s"%response_auth['message']},
                )
            

            ''' 获取设备列表并为每个设备添加唯一标识符 '''
            # devices = await self._get_devices()
            
            # unique_ids = [self._generate_unique_id(dev) for dev in devices]
            
            # breakpoint()
            # self._create_device_entries(devices, unique_ids)

            return self.async_create_entry(
                title="LifeSmart Integration",
                data={
                    "username": self._username,
                    "password": self._password,
                    "appkey": self._appkey,
                    "apptoken": self._apptoken,
                    "exclude": self._exclude,
                    "userid": self._userid,
                    "usertoken": self._usertoken,
                    "expiredtime": self._expiredtime,
                },
            )

        # 如果没有用户输入，显示表单供用户填写
        return self.async_show_form(
            step_id="user", data_schema=CONFIG_SCHEMA, errors={}
        )

    async def lifesmart_Login(self,uid,pwd,appkey):
        import pdb
        url = "https://api.ilifesmart.com/app/auth.login"
        login_data = {
        "uid": uid,
        "pwd": pwd,
        "appkey": appkey
        }
    
        # header = {'Content-Type': 'application/json'}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=login_data) as response:
                return await response.json()


    async def lifesmart_doAuth(self,userid,token,appkey):
        url = "https://api.ilifesmart.com/app/auth.do_auth"
        auth_data = {
        "userid": userid,
        "token": token,
        "appkey": appkey,
        "rgn": "cn"
        }
        header = {'Content-Type': 'application/json'}
        # req = urllib.request.Request(url=url, data=json.dumps(auth_data).encode('utf-8'),headers=header, method='POST')
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=auth_data, headers=header) as response:
                return await response.json()
        return await response.json()
    # async def _validate_credentials(self, username, password):
    #     """验证用户的 LifeSmart 登录信息"""
    #     url = "https://api.ilifesmart.com/app/auth.login"
    #     payload = {
    #         "uid": username,
    #         "pwd": password,
    #         "appkey": self._appkey,
    #     }
    #     headers = {"Content-Type": "application/json"}

    #     try:
    #         async with aiohttp.ClientSession() as session:
    #             async with session.post(url, json=payload, headers=headers) as response:
    #                 data = await response.json()
    #                 if data.get("code") == "success":
    #                     self._userid = data["userid"]
    #                     return True
    #                 else:
    #                     _LOGGER.error("登录失败: %s", data.get("message"))
    #                     return False
    #     except Exception as e:
    #         _LOGGER.error("请求错误: %s", e)
    #         return False

    # async def _get_devices(self):
    #     """获取 LifeSmart 设备列表"""
    #     url = "https://api.ilifesmart.com/app/api.EpGetAll"
    #     tick = int(time.time())
    #     sdata = f"method:EpGetAll,time:{tick},userid:{self._userid},usertoken:{self._usertoken},appkey:{self._appkey},apptoken:{self._apptoken}"
    #     sign = hashlib.md5(sdata.encode(encoding="UTF-8")).hexdigest()

    #     payload = {
    #         "id": 1,
    #         "method": "EpGetAll",
    #         "system": {
    #             "ver": "1.0",
    #             "lang": "en",
    #             "userid": self._userid,
    #             "appkey": self._appkey,
    #             "time": tick,
    #             "sign": sign,
    #         },
    #     }

    #     try:
    #         async with aiohttp.ClientSession() as session:
    #             async with session.post(url, json=payload) as response:
    #                 data = await response.json()
    #                 if data['code'] == 0:
    #                     return data['message']
    #                 else:
    #                     _LOGGER.error("无法获取设备列表: %s", data.get("message"))
    #                     return []
    #     except Exception as e:
    #         _LOGGER.error("获取设备列表时出现错误: %s", e)
    #         return []

    # def _generate_unique_id(self, device):
    #     """为每个设备生成一个唯一标识符"""
    #     return f"{device['devtype']}_{device['agt']}_{device['me']}"

    # def _create_device_entries(self, devices, unique_ids):
    #     """为每个设备创建一个配置条目"""
    #     for device, unique_id in zip(devices, unique_ids):
    #         # 添加每个设备的唯一标识符
    #         _LOGGER.info("为设备 %s 创建唯一标识符: %s", device['name'], unique_id)
    #         # 在这里您可以为每个设备添加其他配置（例如加载平台）
