
import requests
import time
import hashlib
import json
import logging
from homeassistant.exceptions import HomeAssistantError
_LOGGER = logging.getLogger(__name__)

class LifeSmartSupBowlAPI:
    def __init__(self, appkey, apptoken, usertoken, userid, agt, me):
        self.appkey = appkey
        self.apptoken = apptoken
        self.usertoken = usertoken
        self.userid = userid
        self.agt = agt
        self.me = me
        self.svrurl = "https://api.ilifesmart.com/app/"

    def _sign(self, params: dict, method: str):
        ts = int(time.time())
        if method == "GetRemoteList":
            params_str=f"method:{method},agt:{self.agt}"
        elif method == "GetRemote":
            params_str=f"method:{method},agt:{self.agt},ai:{params['ai']},needKeys:{params['needKeys']}"
        elif method == "SendKeys":
            params_str=f"method:{method},agt:{self.agt},ai:{params['ai']},brand:{params['brand']},category:{params['category']},keys:{params['keys']},me:{self.me}"
        elif method == "SendACKeys":
            params_str=f"method:{method},agt:{self.agt},ai:{params['ai']},brand:{params['brand']},category:ac,key:{params['key']},me:{self.me},mode:{params['mode']},power:{params['power']},swing:{params['swing']},temp:{params['temp']},wind:{params['wind']}"
        elif method == "GetACRemoteState":
            params_str=f"method:{method},agt:{self.agt},ai:{params['ai']}"
        elif method == "GetACCodes":
            params_str=f"method:{method},brand:{params['brand']},category:{params['category']},idx:{params['idx']},key:{params['key']},mode:{params['mode']},power:{params['power']},swing:{params['swing']},temp:{params['temp']},wind:{params['wind']}"
        sign_str = f"{params_str},time:{ts},userid:{self.userid},usertoken:{self.usertoken},appkey:{self.appkey},apptoken:{self.apptoken}"
        #签名原始字符串
        return hashlib.md5(sign_str.encode()).hexdigest(), ts

    def _request(self, method, params=None, system_extend=None):
        sign, ts = self._sign(params or {}, method)
        payload = {
            "id": int(time.time()),
            "method": method,
            "params": params or {},
            "system": {
                "ver": "1.0",
                "lang": "en",
                "userid": self.userid,
                "appkey": self.appkey,
                "time": ts,
                "sign": sign,
            }
        }
        if system_extend:
            payload["system"].update(system_extend)
        res = requests.post(self.svrurl + "irapi." + method, json=payload, timeout=10)
        return res.json()

    def get_remote_list(self):
        # 获取超级碗下所有遥控器
        params = {"agt": self.agt}
        resp = self._request("GetRemoteList", params)
        return resp["message"] if resp["code"] == 0 else {}

    def get_remote_detail(self, ai, need_keys=2):
        # 获取遥控器详情和按键及码
        params = {"agt": self.agt, "ai": ai, "needKeys": need_keys}
        resp = self._request("GetRemote", params)
        return resp["message"] if resp["code"] == 0 else {}
    
    def get_ac_remote_state(self, ai):
        params = {"agt": self.agt, "ai": ai}
        resp = self._request("GetACRemoteState", params)
        return resp["message"] if resp["code"] == 0 else {}

    def send_keys(self, ai, category, brand, keys):
        params = {
            "agt": self.agt,
            "me": self.me,
            "ai": ai,
            "category": category,
            "brand": brand,
            "keys": json.dumps([keys]) if isinstance(keys, str) else json.dumps(keys),
        }
        resp = self._request("SendKeys", params)
        return resp["code"] == 0
    
    def get_ac_codes(self, category, brand, idx, key, power,mode,temp,wind,swing):
        params = {
            "category": category,
            "brand": brand,
            "idx": idx,
            "key": key,
            "power": power,
            "mode": mode,
            "temp": temp,
            "wind": wind,
            "swing": swing,
        }
        resp = self._request("GetACCodes", params)
        return resp["message"] if resp["code"] == 0 else {}

    def send_ac_keys(self, ai, category, brand, key, power, mode, temp, wind, swing):
        params = {
            "agt": self.agt,
            "me": self.me,
            "ai": ai,
            "category": category,
            "brand": brand,
            "key": key,
            "power": power,
            "mode": mode,
            "temp": temp,
            "wind": wind,
            "swing": swing,
        }
        resp = self._request("SendACKeys", params)
        if resp["message"] != "ok":
            raise Exception(f"SendACKeys failed: {resp['message']}")
            raise HomeAssistantError(f"空调控制失败：{resp['message']}")
        return resp["message"]

# 你可以添加更多API，如GetCustomKeys, GetACCodes等
