import logging
import os
from proxy_ip import pop_prxy_pikpak
import enum
import hashlib
import uuid
import time

import requests
import config.config as config

from mail.mail import create_one_mail
from .PikPakAPI.pikpakapi import PikPakApi
from typing import Any, Dict, List, Optional

# logger = logging.getLogger(os.path.splitext(os.path.split(__file__)[1])[0])

logger = logging.getLogger("pikpak")


class PikPak:
    pikpakapi: PikPakApi = None
    client_secret = "dbw2OtmVEeuUvIptb1Coyg"
    mail = ""
    pd = ""
    client_id = "YNxT9w7GMdWvEOKa"
    client_id2 = "Y2nMmh6fgvmLA_wM"
    device_id = None
    device_id2 = None
    captcha_token = ""
    verification_id = ''
    mail_code = ""
    proxies = None
    user_id = None
    authorization = None
    __activation_code = 0

    country = "US"
    language = "zh-TW"
    captcha_action = "POST:/v1/auth/verification"

    client_version = "1.42.8"
    # 手机型号
    phone_model = "SM-G988N"
    # 手机品牌
    phone_name = "Samsung"
    # 是否已经注册
    isReqMail = None

    # 是否成功填写邀请码
    isInvise = False

    inviseError = None

    pass_code_token = None

    vip_day_num = None

    def __req_url(
            self,
            method,
            url,
            params=None,
            data=None,
            headers=None,
            cookies=None,
            files=None,
            auth=None,
            timeout=None,
            allow_redirects=True,
            proxies=None,
            hooks=None,
            stream=None,
            verify=None,
            cert=None,
            json=None,
    ):

        for index in range(0, config.requests_retry):
            try:
                logger.debug(f"当前的代理是：{proxies}")
                resp = requests.request(method=method, url=url, params=params, data=data, headers=headers,
                                        cookies=cookies,
                                        files=files, auth=auth, timeout=config.requests_timeout,
                                        allow_redirects=allow_redirects,
                                        proxies=proxies,
                                        hooks=hooks, stream=stream, verify=verify or False, cert=cert, json=json)
                return resp
            except Exception as e:
                logger.debug(f"__req_url error:{e}")
            time.sleep(1)

        raise Exception(f"url:{url}\n请求失败")

    # 仿制captcha_sign
    def __get_sign(self, time_str):
        begin_str = self.client_id + \
            f"{self.client_version}com.pikcloud.pikpak" + \
            self.device_id + time_str
        salts = [
            {'alg': 'md5', 'salt': 'Nw9cvH5q2DqkDTJG73'},
            {'alg': 'md5', 'salt': 'o+N/zglOE4td/6kmjQldcaT'},
            {'alg': 'md5', 'salt': 'SynqV'},
            {'alg': 'md5', 'salt': 'rObDr4xQLmbbk3K7YLn7nsNOlLmTS9h/zQNw+OjNNC'},
            {'alg': 'md5', 'salt': 'SD+x7W8CNeCIepTTUeENi0cPTRkQlYZuXeMHiu8KdMWs0R'},
            {'alg': 'md5', 'salt': 'd5bw'},
            {'alg': 'md5', 'salt': 'qS2pNvzAm3nkoIhK16fKVYp2yHLGwS4M'},
            {'alg': 'md5', 'salt': 'WKMmTWHMFLMhZxb2Nh'},
            {'alg': 'md5', 'salt': 'z7aRh'},
            {'alg': 'md5', 'salt': 'Y5qN0kxE3O'},
            {'alg': 'md5', 'salt': 'rpJq4'},
            {'alg': 'md5', 'salt': 'Lfdm3aGbd'},
            {'alg': 'md5', 'salt': 'X6dfcJrGemgMFLKN85ZcIl0arX3h'},
            {'alg': 'md5', 'salt': 'u2b'}
        ]
        hex_str = begin_str
        for index in range(len(salts)):
            optJSONObject = salts[index]
            if optJSONObject is not None:
                optString = optJSONObject.get("alg", "")
                optString2 = optJSONObject.get("salt", "")
                if optString == "md5":
                    # 使用md5算法对字符串进行加密
                    hex_str = hashlib.md5(
                        (hex_str + optString2).encode()).hexdigest()
        return hex_str

    def set_proxy(self, proxy_ip, type="http"):
        # if not proxy.startswith("http://"):
        if not proxy_ip:
            self.proxies = None
            return
        proxy = f"{type}://{proxy_ip}"
        self.proxies = {
            "http": proxy,
            "https": proxy,
        }

    def __user_agent(self):
        # 创建随机UA
        t = time.time()
        ua = f"ANDROID-com.pikcloud.pikpak/{self.client_version} accessmode/ devicename/{self.phone_name.title()}_{self.phone_model.title()} appname/android-com.pikcloud.pikpak appid/ action_type/ clientid/{self.client_id} deviceid/{self.device_id} refresh_token/ grant_type/ devicemodel/{self.phone_model} networktype/WIFI accesstype/ sessionid/ osversion/7.1.2 datetime/{int(round(t * 1000))} protocolversion/200 sdkversion/2.0.1.200200 clientversion/{self.client_version} providername/NONE clientip/ session_origin/ devicesign/div101.{self.device_id}{self.device_id2} platformversion/10 usrno/"
        return ua

    def __init__(self, mail: str = None, pd: str = None,):
        self.mail = mail
        self.pd = pd
        self.device_id = str(uuid.uuid4()).replace("-", "")
        self.device_id2 = str(uuid.uuid4()).replace("-", "")
        self.pikpakapi = PikPakApi(username=self.mail, password=self.pd)

    captcha_time = time.time()
    captcha_sleep_min_time = 1 * 60
    captcha_action_old = ""

    def __initCaptcha(self):
        captcha_time = time.time()
        if captcha_time - self.captcha_time < self.captcha_sleep_min_time and self.captcha_action_old == self.captcha_action:
            time.sleep(self.captcha_sleep_min_time)
        self.captcha_time = time.time()
        url = "https://user.mypikpak.com/v1/shield/captcha/init"
        time_str = str(round(time.time() * 1000))

        payload = {
            "client_id": self.client_id,
            "action": self.captcha_action,
            "device_id": self.device_id,
            "captcha_token": self.captcha_token,
            "redirect_uri": "xlaccsdk01://xunlei.com/callback?state=dharbor",
            "meta": {
                "timestamp": time_str,
                "email": self.mail,
                "user_id": self.user_id or "",
                "client_version": self.client_version,
                "package_name": "com.pikcloud.pikpak",
                "captcha_sign": "1." + self.__get_sign(time_str),
            }
        }
        # if self.captcha_action != "POST:/v1/auth/verification":
        #     payload["meta"]["captcha_sign"] = "1." + self.__get_sign(time_str)
        headers = {
            "x-device-id": self.device_id,
            "accept-language": self.language,
            "User-Agent": self.__user_agent(),
            "content-type": "application/json; charset=utf-8",

            "Accept-Encoding": "deflate, gzip"
        }
        response = self.__req_url(
            "POST", url, json=payload, headers=headers, proxies=self.proxies)
        res_json = response.json()
        logger.debug(f"__initCaptcha\n{res_json}")
        if res_json.get("url"):
            # logger.debug("打开这个网址手动去执行验证 并获取的token复制到此\n")
            # token = input()
            # logger.debug(f"输入的token\n{token}")
            self.captcha_token = config.get_captcha_callback()(res_json.get("url"))
            logger.info(f"获取的到Token是:{self.captcha_token}")
        else:
            error = res_json.get("error")
            if error:
                if error == "captcha_invalid":
                    # self.__initCaptcha()
                    return
                else:
                    raise Exception(error)
            self.captcha_token = res_json.get("captcha_token")
        self.captcha_action_old = self.captcha_action

    def __input_captcha_token(self, url):
        logger.debug("需要打开网页去验证 并输入返回的 captcha_token")
        logger.debug(url)
        captcha_token = input("请输入captcha_token:\n")
        logger.debug(f"您输入的 captcha_token 是:\n{captcha_token}")
        return captcha_token

    def __input_mail_code(self, mail):
        code = str(input(f"请输入邮箱{mail}中收到的验证码:\n"))
        logger.debug(f"您输入的验证码是:\n{code}")
        return code

    def __send_code(self):
        url = f"https://user.mypikpak.com/v1/auth/verification"
        payload = {
            "client_id": self.client_id,
            "captcha_token": self.captcha_token,
            "email": self.mail,
            "locale": self.language,
            "target": "ANY",
        }
        headers = {
            "x-device-id": self.device_id,
            "accept-language": self.language,
            "User-Agent": self.__user_agent(),
            "content-type": "application/json; charset=utf-8",

            "Accept-Encoding": "deflate, gzip"
        }

        response = self.__req_url(
            "POST", url, json=payload, headers=headers, proxies=self.proxies)
        res_json = response.json()
        if response.status_code != 200:
            logger.debug(f"发送验证消息到邮箱 ERROR:\n{res_json}")
            if res_json.get("error") == "captcha_required":
                self.captcha_token = ''
                self.captcha_action = "POST:/v1/auth/verification"
                self.__initCaptcha()
                self.__send_code()
            else:
                self.inviseError = res_json.get("error")
                raise Exception(self.inviseError)
        else:
            self.verification_id = res_json.get("verification_id")
            logger.debug(f"发送验证消息到邮箱:\n{res_json}")

    # 设置获取的邮箱的验证码
    def __set_mail_2_code(self):
        code = config.get_email_verification_code_callback()(self.mail)
        url = "https://user.mypikpak.com/v1/auth/verification/verify"
        payload = {
            "client_id": self.client_id,
            "verification_id": self.verification_id,
            "verification_code": code,
        }
        headers = {
            "x-device-id": self.device_id,
            "accept-language": self.language,
            "User-Agent": self.__user_agent(),
            "content-type": "application/json; charset=utf-8",

            "Accept-Encoding": "deflate, gzip"
        }

        response = self.__req_url(
            "POST", url, json=payload, headers=headers, proxies=self.proxies, verify=False)
        res_json = response.json()
        if response.status_code == 200:
            self.verification_id = res_json.get("verification_token")
            self.mail_code = code
            logger.debug(f"设置邮箱的验证码:\n{res_json}")
        else:
            logger.debug(f"设置邮箱的验证码 ERROR:\n{res_json}")
            self.inviseError = res_json.get("error")
            raise Exception(self.inviseError)

    def __signup(self):
        url = "https://user.mypikpak.com/v1/auth/signup"
        payload = {
            "client_id": self.client_id,
            "captcha_token": self.captcha_token,
            "client_secret": self.client_secret,
            "email": self.mail,
            "name": self.mail.split("@")[0],
            "password": self.pd,
            "verification_token": self.verification_id,
        }
        headers = {
            "x-device-id": self.device_id,
            "accept-language": self.language,
            "User-Agent": self.__user_agent(),
            "content-type": "application/json; charset=utf-8",

            "Accept-Encoding": "deflate, gzip"
        }

        response = self.__req_url(
            "POST", url, json=payload, headers=headers, proxies=self.proxies)
        res_json = response.json()
        if response.status_code != 200:
            logger.debug(f"注册登陆失败:\n{res_json}")
            if res_json.get("error") == "captcha_invalid":
                self.captcha_action = "POST:/v1/auth/signup"
                self.__initCaptcha()
                # self.set_mail_2_code(self.mail_code)
                self.__signup()
            elif res_json.get("error") == "already_exists":
                logger.debug(f"用户存在\n{res_json}")
                self.__login2()
            else:
                self.inviseError = res_json.get("error")
                raise Exception(self.inviseError)
        else:
            logger.debug(f"注册登陆成功:\n{res_json}")
            self.user_id = res_json.get("sub")
            self.authorization = f"{res_json.get('token_type')} {res_json.get('access_token')}"
            self.isReqMail = self.mail

    def __login2(self):
        url = "https://user.mypikpak.com/v1/auth/token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "password": self.pd,
            "username": self.mail,
            "grant_type": "password",
        }
        headers = {
            "x-device-id": self.device_id,
            "x-peer-id": self.device_id,
            "x-captcha-token": self.captcha_token,
            "x-client-version-code": "10181",
            "x-alt-capability": "3",
            "accept-language": self.language,
            "country": self.country,
            "x-user-region": "2",
            "product_flavor_name": "cha",
            "x-system-language": self.language,
            "User-Agent": self.__user_agent(),
            "content-type": "application/json; charset=utf-8",
            "Authorization": self.authorization,
            "Accept-Encoding": "deflate, gzip"
        }

        response = self.__req_url(
            "POST", url, json=payload, headers=headers, proxies=self.proxies)
        res_json = response.json()

        self.authorization = "Bearer " + res_json["access_token"]
        self.refresh_token = res_json["refresh_token"]
        self.user_id = res_json.get("sub")
        self.__refresh_access_token()

    def __refresh_access_token(self):
        url = "https://user.mypikpak.com/v1/auth/token"
        payload = {
            "client_id": self.client_id,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
        }
        headers = {
            "x-device-id": self.device_id,
            "x-peer-id": self.device_id,
            "x-captcha-token": self.captcha_token,
            "x-client-version-code": "10181",
            "x-alt-capability": "3",
            "accept-language": self.language,
            "country": self.country,
            "x-user-region": "2",
            "product_flavor_name": "cha",
            "x-system-language": self.language,
            "User-Agent": self.__user_agent(),
            "content-type": "application/json; charset=utf-8",
            "Authorization": self.authorization,
            "Accept-Encoding": "deflate, gzip"
        }

        response = self.__req_url(
            "POST", url, json=payload, headers=headers, proxies=self.proxies)
        res_json = response.json()

        self.authorization = "Bearer " + res_json["access_token"]
        self.refresh_token = res_json["refresh_token"]
        self.user_id = res_json.get("sub")

    def __login(self):
        if self.authorization:
            logger.debug("已经登陆 不用在登陆了")
            return
        url = "https://user.mypikpak.com/v1/auth/signin"
        payload = {
            "client_id": self.client_id,
            "captcha_token": self.captcha_token,
            "client_secret": self.client_secret,
            "username": self.mail,
            "password": self.pd,
        }
        headers = {
            "x-device-id": self.device_id,
            "x-peer-id": self.device_id,
            "x-captcha-token": self.captcha_token,
            "x-client-version-code": "10181",
            "x-alt-capability": "3",
            "accept-language": self.language,
            "country": self.country,
            "x-user-region": "2",
            "product_flavor_name": "cha",
            "x-system-language": self.language,
            "User-Agent": self.__user_agent(),
            "content-type": "application/json; charset=utf-8",
            "Authorization": self.authorization,
            "Accept-Encoding": "deflate, gzip"
        }

        response = self.__req_url(
            "POST", url, json=payload, headers=headers, proxies=self.proxies)
        res_json = response.json()
        if response.status_code == 200:
            logger.debug(f"登陆成功{res_json}")
            self.user_id = res_json.get("sub")
            self.authorization = f"{res_json.get('token_type')} {res_json.get('access_token')}"
        else:
            if res_json.get("error") == "captcha_required":
                self.captcha_action = "POST:/v1/auth/signin"
                self.__initCaptcha()
                self.__login()
                return
            logger.debug(f"登陆失败{res_json}")
            self.inviseError = res_json.get("error")
            raise Exception(self.inviseError)

    def __get_active_invite(self):
        url = f"https://api-drive.mypikpak.com/vip/v1/activity/invite"
        payload = {
            "data": {
                "sdk_int": "25",
                "uuid": self.device_id,
                "userType": "1",
                "userid": self.user_id,
                "userSub": "",
                "product_flavor_name": "cha",
                "language_system": self.language,
                "language_app": self.language,
                "build_version_release": "7.1.2",
                "phoneModel": self.phone_model,
                "build_manufacturer": self.phone_name.upper(),
                "build_sdk_int": "25",
                "channel": "official",
                "versionCode": "10182",
                "versionName": self.client_version,
                "installFrom": "other",
                "country": self.country,
            },
            "apk_extra": {
                "channel": "official",
            },
        }
        headers = {
            "x-system-language": self.language,
            "x-device-id": self.device_id,
            "x-client-version-code": "10182",
            "x-peer-id": self.device_id,
            "x-alt-capability": "3",
            "x-captcha-token": self.captcha_token,
            "user-agent": self.__user_agent(),
            "country": self.country,
            "x-user-region": "2",
            "product_flavor_name": "cha",
            "accept-language": self.language,
            "authorization": self.authorization,
            "accept-encoding": "gzip",
        }

        response = self.__req_url(
            "POST", url, json=payload, headers=headers, proxies=self.proxies)
        res_json = response.json()
        if response.status_code != 200:
            if res_json.get("error") == "captcha_invalid":
                self.captcha_action = "POST:/vip/v1/activity/invite"
                self.captcha_token = ""
                self.__initCaptcha()
                self.__get_active_invite()
            else:
                logger.debug(f"vip邀请信息返回 Error \n{res_json}")
                self.inviseError = res_json.get("error")
                raise Exception(self.inviseError)
            return
        logger.debug(f"vip邀请信息返回:\n{res_json}")

    def set_activation_code(self, code):
        """设置需要填写的邀请码
        Args:
            code (_type_): _description_
        """
        self.__activation_code = code

    # 设置邀请
    def __set_activation_code(self):
        url = "https://api-drive.mypikpak.com/vip/v1/order/activation-code"
        payload = {
            "activation_code": str(self.__activation_code),
            "page": "invite",
        }
        headers = {
            "x-device-id": self.device_id,
            "x-peer-id": self.device_id,
            "x-captcha-token": self.captcha_token,
            "x-client-version-code": "10181",
            "x-alt-capability": "3",
            "accept-language": self.language,
            "country": self.country,
            "x-user-region": "2",
            "product_flavor_name": "cha",
            "x-system-language": self.language,
            "User-Agent": self.__user_agent(),
            "content-type": "application/json; charset=utf-8",
            "Authorization": self.authorization,
            "Accept-Encoding": "deflate, gzip"
        }

        response = self.__req_url(
            "POST", url, json=payload, headers=headers, proxies=self.proxies)
        res_json = response.json()
        if response.status_code != 200:
            if res_json.get("error") == "captcha_invalid":
                self.captcha_action = "POST:/vip/v1/order/activation-code"
                self.__initCaptcha()
                self.__set_activation_code()
            else:
                self.inviseError = res_json.get("error")
            logger.debug(f"填写邀请结果返回 Error \n{res_json}")
            return
        error = res_json.get("error")
        if not error or error == "":
            self.isInvise = True
        else:
            self.inviseError = res_json.get("error")
            raise Exception(self.inviseError)
        logger.debug(f"填写邀请结果返回:\n{res_json}")

    # 获取当前设备
    def __access_controller(self):
        url = "https://access.mypikpak.com/access_controller/v1/area_accessible"
        payload = {}
        headers = {
            "Channel-Id": "official",
            "Version-Code": "10182",
            "Version-Name": self.client_version,
            "System-Version": "25",
            "Mobile-Type": "android",
            "App-Type": "android",
            "Platform-Version": "7.1.2",
            "Sdk-Int": "25",
            "Language-System": self.language,
            "X-System-Language": self.language,
            "Build-Version-Release": "7.1.2",
            "Phone-Model": self.phone_model,
            "Build-Manufacturer": self.phone_name.upper(),
            "Build-Sdk-Int": "25",
            "Country": self.country,
            "Product_Flavor_Name": "cha",
            "X-Device-Id": self.device_id,
            "Language-App": self.language,
            "X-Client-Id": self.client_id,
            "X-Client-Version": self.client_version,
            "x-client-id": self.client_id,
            "accept-language": self.language,
            "x-device-id": self.device_id,
            "x-client-version": self.client_version,
            "Host": "access.mypikpak.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "User-Agent": "okhttp/4.8.0",
        }

        response = self.__req_url(
            "GET", url, json=payload, headers=headers, proxies=self.proxies)
        res_json = response.json()
        if response.status_code != 200:
            if res_json.get("error") == "captcha_invalid":
                self.captcha_action = "POST:/access_controller/v1/area_accessible"
                self.__initCaptcha()
                self.__access_controller()
            else:
                logger.debug(f"当前设备打印消息 Error \n{res_json}")
                self.inviseError = res_json.get("error")
                raise Exception(self.inviseError)
            return
        logger.debug(f"当前设备打印消息\n{res_json}")

    # global_config
    def __global_config(self):
        url = "https://config.mypikpak.com/config/v1/globalConfig"
        payload = {
            "data": {
                "version": self.client_version,
                "versioncode": "10182",
                "install_from": "other",
                "device_id": self.device_id,
                "language_system": self.language,
                "language_app": self.language,
                "country": self.country,
                "channel_id": "official",
                "product_flavor_name": "cha",
                "user_id": self.user_id,
            },
            "client": "android"
        }
        headers = {
            "channel-id": "official",
            "version-code": "10182",
            "version-name": self.client_version,
            "system-version": "25",
            "mobile-type": "android",
            "app-type": "android",
            "platform-version": "7.1.2",
            "sdk-int": "25",
            "language-system": self.language,
            "x-system-language": self.language,
            "build-version-release": "7.1.2",
            "phone-model": self.phone_model,
            "build-manufacturer": self.phone_name.upper(),
            "build-sdk-int": "25",
            "country": self.country,
            "product_flavor_name": "cha",
            "x-device-id": self.device_id,
            "language-app": self.language,
            "x-client-id": self.client_id,
            "x-client-version": self.client_version,
            "x-user-id": self.user_id,
            "content-type": "application/json; charset=utf-8",
            "accept-encoding": "gzip",
            "user-agent": "okhttp/4.8.0",
        }

        response = self.__req_url(
            "POST", url, json=payload, headers=headers, proxies=self.proxies)
        res_json = response.json()
        if response.status_code != 200:
            if res_json.get("error") == "captcha_invalid":
                self.captcha_action = "POST:/config/v1/globalConfig"
                self.__initCaptcha()
                self.__global_config()
            else:
                logger.debug(f"当前设备global_config打印消息 Error \n{res_json}")
                self.inviseError = res_json.get("error")
                raise Exception(self.inviseError)
            return
        logger.debug(f"当前设备global_config打印消息\n{res_json}")

    def __operating(self):
        url = "https://api-drive.mypikpak.com/operating/v1/content"
        payload = {
            "data": {
                "version": self.client_version,
                "versioncode": "10182",
                "install_from": "other",
                "device_id": self.device_id,
                "language_system": self.language,
                "language_app": self.language,
                "country": self.country,
                "channel_id": "official",
                "product_flavor_name": "cha",
                "user_id": self.user_id,
            },
            "client": "android"
        }
        headers = {
            "x-system-language": self.language,
            "x-device-id": self.device_id,
            "x-client-version-code": "10182",
            "x-peer-id": self.device_id,
            "x-alt-capability": "3",
            "x-captcha-token": self.captcha_token,
            "user-agent": self.__user_agent(),
            "country": self.country,
            "x-user-region": "2",
            "product_flavor_name": "cha",
            "accept-language": self.language,
            "authorization": self.authorization,
            "accept-encoding": "gzip",
        }

        response = self.__req_url(
            "POST", url, json=payload, headers=headers, proxies=self.proxies)
        res_json = response.json()
        if response.status_code != 200:
            if res_json.get("error") == "captcha_invalid":
                self.captcha_action = "POST:/operating/v1/content"
                self.__initCaptcha()
                self.__operating()
            else:
                logger.debug(f"当前设备operating打印消息 Error \n{res_json}")
                self.inviseError = res_json.get("error")
                raise Exception(self.inviseError)
            return
        logger.debug(f"当前设备operating打印消息\n{res_json}")

    def __logReportSwitch(self):
        url = "https://config.mypikpak.com/config/v1/logReportSwitch"
        payload = {
            "data": {
                "sdk_int": "25",
                "uuid": self.device_id,
                "userType": "1",
                "userid": self.user_id,
                "userSub": "regional",
                "language_system": self.language,
                "build_version_release": "7.1.2",
                "phoneModel": self.phone_model,
                "build_manufacturer": self.phone_name.upper(),
                "build_sdk_int": "25",
                "channel": "official",
                "versionCode": "10182",
                "versionName": self.client_version,
                "country": self.country,
                "language": self.language,
            }
        }
        headers = {
            "content-type": "application/json",
            "x-system-language": self.language,
            "x-device-id": self.device_id,
            "x-client-version-code": "10182",
            "x-peer-id": self.device_id,
            "x-alt-capability": "3",
            "x-captcha-token": self.captcha_token,
            "user-agent": self.__user_agent(),
            "country": self.country,
            "x-user-region": "2",
            "product_flavor_name": "cha",
            "accept-language": self.language,
            "authorization": self.authorization,
            "accept-encoding": "gzip",
        }

        response = self.__req_url(
            "POST", url, json=payload, headers=headers, proxies=self.proxies)
        res_json = response.json()
        if response.status_code != 200:
            if res_json.get("error") == "captcha_invalid":
                self.captcha_action = "POST:/config/v1/logReportSwitch"
                self.__initCaptcha()
                self.__logReportSwitch()
            else:
                logger.debug(f"当前设备operating打印消息 Error \n{res_json}")
                self.inviseError = res_json.get("error")
                raise Exception(self.inviseError)
            return
        logger.debug(f"当前设备operating打印消息\n{res_json}")

    def __operating_report(self):
        url = "https://api-drive.mypikpak.com/operating/v1/report"
        payload = {
            "data": {
                "version": self.client_version,
                "versioncode": "10182",
                "install_from": "other",
                "device_id": self.device_id,
                "language_system": self.language,
                "language_app": self.language,
                "country": self.country,
                "channel_id": "official",
                "product_flavor_name": "cha",
                "user_id": self.user_id,
            },
            "client": "android",
            "id": "m20230322001",
            "attr": "REPORT_ATTR_TITLE"
        }
        headers = {
            "x-detection-time": "dl-a10b-0858:389,dl-a10b-0859:397,dl-a10b-0860:395,dl-a10b-0867:401,dl-a10b-0861:431,dl-a10b-0876:421,dl-a10b-0868:556,dl-a10b-0886:505,dl-a10b-0865:575,dl-a10b-0862:603,dl-a10b-0872:569,dl-a10b-0880:658,dl-a10b-0878:662,dl-a10b-0624:636,dl-a10b-0877:685,dl-a10b-0621:654,dl-a10b-0885:666,dl-a10b-0622:656,dl-a10b-0623:657,dl-a10b-0625:655,dl-a10b-0881:691,dl-a10b-0879:699,dl-a10b-0864:779,dl-a10b-0884:722,dl-a10b-0882:742,dl-a10b-0875:752,dl-a10b-0883:768,dl-a10b-0869:814,dl-a10b-0873:801,dl-a10b-0887:763,dl-a10b-0874:800,dl-a10b-0866:826,dl-a10b-0870:815,dl-a10b-0871:846,dl-a10b-0863:938",
            "content-type": "application/json",
            "x-system-language": self.language,
            "x-device-id": self.device_id,
            "x-client-version-code": "10182",
            "x-peer-id": self.device_id,
            "x-alt-capability": "3",
            "x-captcha-token": self.captcha_token,
            "user-agent": self.__user_agent(),
            "country": self.country,
            "x-user-region": "2,3",
            "product_flavor_name": "cha",
            "accept-language": self.language,
            "authorization": self.authorization,
            "accept-encoding": "gzip",
        }

        response = self.__req_url(
            "POST", url, json=payload, headers=headers, proxies=self.proxies)
        res_json = response.json()
        if response.status_code != 200:
            if res_json.get("error") == "captcha_invalid":
                self.captcha_action = "POST:/operating/v1/report"
                self.__initCaptcha()
                self.__operating_report()
            else:
                logger.debug(f"当前设备__operating_report打印消息 Error \n{res_json}")
                self.inviseError = res_json.get("error")
                raise Exception(self.inviseError)
            return
        logger.debug(f"当前设备__operating_report打印消息\n{res_json}")

    def __urlsOnInstall(self):
        url = "https://config.mypikpak.com/config/v1/urlsOnInstall"
        payload = {
            "data": {
                "x-detection-time": "dl-a10b-0858:389,dl-a10b-0859:397,dl-a10b-0860:395,dl-a10b-0867:401,dl-a10b-0861:431,dl-a10b-0876:421,dl-a10b-0868:556,dl-a10b-0886:505,dl-a10b-0865:575,dl-a10b-0862:603,dl-a10b-0872:569,dl-a10b-0880:658,dl-a10b-0878:662,dl-a10b-0624:636,dl-a10b-0877:685,dl-a10b-0621:654,dl-a10b-0885:666,dl-a10b-0622:656,dl-a10b-0623:657,dl-a10b-0625:655,dl-a10b-0881:691,dl-a10b-0879:699,dl-a10b-0864:779,dl-a10b-0884:722,dl-a10b-0882:742,dl-a10b-0875:752,dl-a10b-0883:768,dl-a10b-0869:814,dl-a10b-0873:801,dl-a10b-0887:763,dl-a10b-0874:800,dl-a10b-0866:826,dl-a10b-0870:815,dl-a10b-0871:846,dl-a10b-0863:938",
                "sdk_int": "25",
                "uuid": self.device_id,
                "userType": "1",
                "userid": self.user_id,
                "userSub": "regional",
                "language_system": self.language,
                "language_app": self.language,
                "build_version_release": "7.1.2",
                "phoneModel": self.phone_model,
                "build_manufacturer": self.phone_name.upper(),
                "build_sdk_int": "25",
                "channel": "official",
                "versionCode": "10182",
                "versionName": self.client_version,
                "country": self.country,
                "install_from": "other",
            }
        }
        headers = {
            "x-detection-time": "dl-a10b-0858:389,dl-a10b-0859:397,dl-a10b-0860:395,dl-a10b-0867:401,dl-a10b-0861:431,dl-a10b-0876:421,dl-a10b-0868:556,dl-a10b-0886:505,dl-a10b-0865:575,dl-a10b-0862:603,dl-a10b-0872:569,dl-a10b-0880:658,dl-a10b-0878:662,dl-a10b-0624:636,dl-a10b-0877:685,dl-a10b-0621:654,dl-a10b-0885:666,dl-a10b-0622:656,dl-a10b-0623:657,dl-a10b-0625:655,dl-a10b-0881:691,dl-a10b-0879:699,dl-a10b-0864:779,dl-a10b-0884:722,dl-a10b-0882:742,dl-a10b-0875:752,dl-a10b-0883:768,dl-a10b-0869:814,dl-a10b-0873:801,dl-a10b-0887:763,dl-a10b-0874:800,dl-a10b-0866:826,dl-a10b-0870:815,dl-a10b-0871:846,dl-a10b-0863:938",
            "content-type": "application/json",
            "x-system-language": self.language,
            "x-device-id": self.device_id,
            "x-client-version-code": "10182",
            "x-peer-id": self.device_id,
            "x-alt-capability": "3",
            "x-captcha-token": self.captcha_token,
            "user-agent": self.__user_agent(),
            "country": self.country,
            "x-user-region": "2,3",
            "product_flavor_name": "cha",
            "accept-language": self.language,
            "authorization": self.authorization,
            "accept-encoding": "gzip",
        }

        response = self.__req_url(
            "POST", url, json=payload, headers=headers, proxies=self.proxies)
        res_json = response.json()
        if response.status_code != 200:
            if res_json.get("error") == "captcha_invalid":
                self.captcha_action = "POST:/config/v1/urlsOnInstall"
                self.__initCaptcha()
                self.__operating_report()
            else:
                logger.debug(f"当前设备__urlsOnInstall打印消息 Error \n{res_json}")
                self.inviseError = res_json.get("error")
                raise Exception(self.inviseError)
            return
        logger.debug(f"当前设备__urlsOnInstall打印消息\n{res_json}")

    # 注册并登陆增加邀请
    def run_req_2invite(self):
        if self.isReqMail:
            self.run_login_2invite()
            return
        self.__send_code()
        self.__set_mail_2_code()
        self.__signup()
        time.sleep(5)
        self.__get_active_invite()
        time.sleep(1)
        self.__access_controller()
        time.sleep(1)
        self.__global_config()
        time.sleep(1)
        self.__operating()
        time.sleep(1)
        self.__logReportSwitch()
        time.sleep(1)
        self.__operating_report()
        time.sleep(1)
        self.__urlsOnInstall()
        time.sleep(1)
        self.__set_activation_code()

    # 直接登陆增加邀请
    def run_login_2invite(self):
        self.__login2()
        time.sleep(5)
        self.__get_active_invite()
        time.sleep(1)
        self.__access_controller()
        time.sleep(1)
        self.__global_config()
        time.sleep(1)
        self.__operating()
        time.sleep(1)
        self.__logReportSwitch()
        time.sleep(1)
        self.__operating_report()
        time.sleep(1)
        self.__urlsOnInstall()
        time.sleep(1)
        self.__set_activation_code()

    def __get_pikpak_share_passcode(self, share_id):
        # share_url = "https://mypikpak.com/s/VNxHRUombIy7SWJs5Oyw-TDxo1"
        url = f"https://api-drive.mypikpak.com/drive/v1/share?share_id={share_id}&pass_code=&page_token=&pass_code_token={self.pass_code_token or ''}&thumbnail_size=SIZE_LARGE&limit=100"
        payload = {}
        headers = {
            "x-detection-time": "dl-a10b-0858:389,dl-a10b-0859:397,dl-a10b-0860:395,dl-a10b-0867:401,dl-a10b-0861:431,dl-a10b-0876:421,dl-a10b-0868:556,dl-a10b-0886:505,dl-a10b-0865:575,dl-a10b-0862:603,dl-a10b-0872:569,dl-a10b-0880:658,dl-a10b-0878:662,dl-a10b-0624:636,dl-a10b-0877:685,dl-a10b-0621:654,dl-a10b-0885:666,dl-a10b-0622:656,dl-a10b-0623:657,dl-a10b-0625:655,dl-a10b-0881:691,dl-a10b-0879:699,dl-a10b-0864:779,dl-a10b-0884:722,dl-a10b-0882:742,dl-a10b-0875:752,dl-a10b-0883:768,dl-a10b-0869:814,dl-a10b-0873:801,dl-a10b-0887:763,dl-a10b-0874:800,dl-a10b-0866:826,dl-a10b-0870:815,dl-a10b-0871:846,dl-a10b-0863:938",
            "content-type": "application/json",
            "x-system-language": self.language,
            "x-device-id": self.device_id,
            "x-client-version-code": "10182",
            "x-peer-id": self.device_id,
            "x-alt-capability": "3",
            "x-captcha-token": self.captcha_token,
            "user-agent": self.__user_agent(),
            "country": self.country,
            "x-user-region": "2,3",
            "product_flavor_name": "cha",
            "accept-language": self.language,
            "authorization": self.authorization,
            "accept-encoding": "gzip",
        }

        response = self.__req_url(
            "GET", url, json=payload, headers=headers, proxies=self.proxies)
        res_json = response.json()
        if response.status_code != 200:
            if res_json.get("error") == "captcha_invalid":
                self.captcha_action = f"GET:/vip/v1/vip/info"
                self.__initCaptcha()
                self.__get_pikpak_share_passcode(share_id)
            else:
                logger.debug(
                    f"当前 pikpak_share_passcode 打印消息 Error \n{res_json}")
                self.inviseError = res_json.get("error")
                raise Exception(self.inviseError)
            return
        logger.debug(f"当前 pikpak_share_passcode 打印消息\n{res_json}")
        self.pass_code_token = res_json.get("pass_code_token")

    def __save_pikpak_2_self(self, share_id):
        # share_url = "https://mypikpak.com/s/VNxHRUombIy7SWJs5Oyw-TDxo1"
        if not self.pass_code_token:
            self.__get_pikpak_share_passcode(share_id)
        url = "https://api-drive.mypikpak.com/drive/v1/share/restore"
        payload = {
            "folder_type": "",
            "share_id": share_id,
            "pass_code_token": self.pass_code_token,
            "file_ids": [],
            "ancestor_ids": [],
            "params": {
                "trace_file_ids": "*",
            },
        }
        headers = {
            "x-detection-time": "dl-a10b-0858:389,dl-a10b-0859:397,dl-a10b-0860:395,dl-a10b-0867:401,dl-a10b-0861:431,dl-a10b-0876:421,dl-a10b-0868:556,dl-a10b-0886:505,dl-a10b-0865:575,dl-a10b-0862:603,dl-a10b-0872:569,dl-a10b-0880:658,dl-a10b-0878:662,dl-a10b-0624:636,dl-a10b-0877:685,dl-a10b-0621:654,dl-a10b-0885:666,dl-a10b-0622:656,dl-a10b-0623:657,dl-a10b-0625:655,dl-a10b-0881:691,dl-a10b-0879:699,dl-a10b-0864:779,dl-a10b-0884:722,dl-a10b-0882:742,dl-a10b-0875:752,dl-a10b-0883:768,dl-a10b-0869:814,dl-a10b-0873:801,dl-a10b-0887:763,dl-a10b-0874:800,dl-a10b-0866:826,dl-a10b-0870:815,dl-a10b-0871:846,dl-a10b-0863:938",
            "content-type": "application/json",
            "x-system-language": self.language,
            "x-device-id": self.device_id,
            "x-client-version-code": "10182",
            "x-peer-id": self.device_id,
            "x-alt-capability": "3",
            "x-captcha-token": self.captcha_token,
            "user-agent": self.__user_agent(),
            "country": self.country,
            "x-user-region": "2,3",
            "product_flavor_name": "cha",
            "accept-language": self.language,
            "authorization": self.authorization,
            "accept-encoding": "gzip",
        }

        response = self.__req_url(
            "POST", url, json=payload, headers=headers, proxies=self.proxies)
        res_json = response.json()
        if response.status_code != 200:
            if res_json.get("error") == "captcha_invalid":
                self.captcha_action = f"GET:/drive/v1/files/{share_id}"
                self.__initCaptcha()
                self.__save_pikpak_2_self(share_id)
            else:
                logger.debug(f"当前设备__保存分享文件 打印消息 Error \n{res_json}")
                self.inviseError = res_json.get("error")
                raise Exception(self.inviseError)
            return
        logger.debug(f"当前设备__保存分享文件 打印消息\n{res_json}")

    def save_share(self, share_id):
        self.__login2()
        self.__save_pikpak_2_self(share_id)

    # 获取自己的邀请码
    def __req_self_invite_code(self):
        url = "https://api-drive.mypikpak.com/vip/v1/activity/inviteCode"
        payload = {}
        headers = {
            "x-detection-time": "dl-a10b-0858:389,dl-a10b-0859:397,dl-a10b-0860:395,dl-a10b-0867:401,dl-a10b-0861:431,dl-a10b-0876:421,dl-a10b-0868:556,dl-a10b-0886:505,dl-a10b-0865:575,dl-a10b-0862:603,dl-a10b-0872:569,dl-a10b-0880:658,dl-a10b-0878:662,dl-a10b-0624:636,dl-a10b-0877:685,dl-a10b-0621:654,dl-a10b-0885:666,dl-a10b-0622:656,dl-a10b-0623:657,dl-a10b-0625:655,dl-a10b-0881:691,dl-a10b-0879:699,dl-a10b-0864:779,dl-a10b-0884:722,dl-a10b-0882:742,dl-a10b-0875:752,dl-a10b-0883:768,dl-a10b-0869:814,dl-a10b-0873:801,dl-a10b-0887:763,dl-a10b-0874:800,dl-a10b-0866:826,dl-a10b-0870:815,dl-a10b-0871:846,dl-a10b-0863:938",
            "content-type": "application/json",
            "x-system-language": self.language,
            "x-device-id": self.device_id,
            "x-client-version-code": "10182",
            "x-peer-id": self.device_id,
            "x-alt-capability": "3",
            "x-captcha-token": self.captcha_token,
            "user-agent": self.__user_agent(),
            "country": self.country,
            "x-user-region": "2,3",
            "product_flavor_name": "cha",
            "accept-language": self.language,
            "authorization": self.authorization,
            "accept-encoding": "gzip",
        }

        response = self.__req_url(
            "GET", url, json=payload, headers=headers, proxies=self.proxies)
        res_json = response.json()
        if response.status_code != 200:
            if res_json.get("error") == "captcha_invalid":
                self.captcha_action = f"GET:/vip/v1/vip/info"
                self.__initCaptcha()
                return self.__req_self_invite_code()
            else:
                logger.debug(f"当前 获取自己的邀请码 打印消息 Error \n{res_json}")
                self.inviseError = res_json.get("error")
                raise Exception(self.inviseError)
            return
        logger.debug(f"当前 获取自己的邀请码 打印消息\n{res_json}")
        return res_json.get("code")

    def get_self_invite_code(self):
        self.__login2()
        return self.__req_self_invite_code()

    def __req_self_vip_info2(self):
        url = "https://api-drive.mypikpak.com/drive/v1/privilege/vip"
        payload = {}
        headers = {
            "x-detection-time": "dl-a10b-0858:389,dl-a10b-0859:397,dl-a10b-0860:395,dl-a10b-0867:401,dl-a10b-0861:431,dl-a10b-0876:421,dl-a10b-0868:556,dl-a10b-0886:505,dl-a10b-0865:575,dl-a10b-0862:603,dl-a10b-0872:569,dl-a10b-0880:658,dl-a10b-0878:662,dl-a10b-0624:636,dl-a10b-0877:685,dl-a10b-0621:654,dl-a10b-0885:666,dl-a10b-0622:656,dl-a10b-0623:657,dl-a10b-0625:655,dl-a10b-0881:691,dl-a10b-0879:699,dl-a10b-0864:779,dl-a10b-0884:722,dl-a10b-0882:742,dl-a10b-0875:752,dl-a10b-0883:768,dl-a10b-0869:814,dl-a10b-0873:801,dl-a10b-0887:763,dl-a10b-0874:800,dl-a10b-0866:826,dl-a10b-0870:815,dl-a10b-0871:846,dl-a10b-0863:938",
            "content-type": "application/json",
            "x-system-language": self.language,
            "x-device-id": self.device_id,
            "x-client-version-code": "10182",
            "x-peer-id": self.device_id,
            "x-alt-capability": "3",
            "x-captcha-token": self.captcha_token,
            "user-agent": self.__user_agent(),
            "country": self.country,
            "x-user-region": "2,3",
            "product_flavor_name": "cha",
            "accept-language": self.language,
            "authorization": self.authorization,
            "accept-encoding": "gzip",
        }

        response = self.__req_url(
            "GET", url, json=payload, headers=headers, proxies=self.proxies)
        res_json = response.json()
        if response.status_code != 200:
            if res_json.get("error") == "captcha_invalid":
                self.captcha_action = f"GET:/vip/v1/vip/info"
                self.__initCaptcha()
                return self.__req_self_vip_info2()
            else:
                logger.debug(f"当前 获取自己的邀请码 打印消息 Error \n{res_json}")
                self.inviseError = res_json.get("error")
                raise Exception(self.inviseError)
            return
        logger.debug(f"当前 获取自己的邀请码 打印消息\n{res_json}")
        return res_json

    def __req_self_vip_info(self):
        url = "https://api-drive.mypikpak.com/vip/v1/vip/info"
        payload = {}
        headers = {
            "x-detection-time": "dl-a10b-0858:389,dl-a10b-0859:397,dl-a10b-0860:395,dl-a10b-0867:401,dl-a10b-0861:431,dl-a10b-0876:421,dl-a10b-0868:556,dl-a10b-0886:505,dl-a10b-0865:575,dl-a10b-0862:603,dl-a10b-0872:569,dl-a10b-0880:658,dl-a10b-0878:662,dl-a10b-0624:636,dl-a10b-0877:685,dl-a10b-0621:654,dl-a10b-0885:666,dl-a10b-0622:656,dl-a10b-0623:657,dl-a10b-0625:655,dl-a10b-0881:691,dl-a10b-0879:699,dl-a10b-0864:779,dl-a10b-0884:722,dl-a10b-0882:742,dl-a10b-0875:752,dl-a10b-0883:768,dl-a10b-0869:814,dl-a10b-0873:801,dl-a10b-0887:763,dl-a10b-0874:800,dl-a10b-0866:826,dl-a10b-0870:815,dl-a10b-0871:846,dl-a10b-0863:938",
            "content-type": "application/json",
            "x-system-language": self.language,
            "x-device-id": self.device_id,
            "x-client-version-code": "10182",
            "x-peer-id": self.device_id,
            "x-alt-capability": "3",
            "x-captcha-token": self.captcha_token,
            "user-agent": self.__user_agent(),
            "country": self.country,
            "x-user-region": "2,3",
            "product_flavor_name": "cha",
            "accept-language": self.language,
            "authorization": self.authorization,
            "accept-encoding": "gzip",
        }

        response = self.__req_url(
            "GET", url, json=payload, headers=headers, proxies=self.proxies)
        res_json = response.json()
        if response.status_code != 200:
            if res_json.get("error") == "captcha_invalid":
                self.captcha_action = f"GET:/vip/v1/vip/info"
                self.__initCaptcha()
                return self.__req_self_vip_info()
            else:
                logger.debug(f"当前 获取自己的邀请码 打印消息 Error \n{res_json}")
                self.inviseError = res_json.get("error")
                raise Exception(self.inviseError)
            return
        logger.debug(f"当前 获取自己的邀请码 打印消息\n{res_json}")
        return res_json

    def get_self_vip_info(self):
        self.__login2()
        vip_data = self.__req_self_vip_info()
        return vip_data

    def get_vip_day_time_left(self, is_update: bool = False) -> int:
        """获取剩余的VIP时间

        Returns:
            int: 剩余天数
        """
        if self.vip_day_num and not is_update:
            return self.vip_day_num
        try:
            vip_data = self.get_self_vip_info()
            self.vip_day_num = vip_data.get('data').get("vipItem")[
                0].get("surplus_day", 0)
        except:
            self.vip_day_num = 0
        return self.vip_day_num


# 创建一个新的账号并填写邀请码


def crete_invite(invite) -> PikPak:
    try:
        _mail = create_one_mail()
        pik_go = PikPak(
            mail=_mail,
            pd=config.def_password,
        )
        pik_go.set_activation_code(invite)
        logger.info("获取代理地址中。。。。。")
        ip, proxy_type = pop_prxy_pikpak()
        logger.info(f"获取到的代理:{ip}")
        # ip, proxy_type = __proxy
        pik_go.set_proxy(ip, proxy_type)
        pik_go.run_req_2invite()
        if pik_go.isInvise:
            logger.info(f"{_mail}:注册成功 并邀请{invite}VIP")
            return pik_go
        else:
            logger.info(f"{invite} 注册失败！重新注册")
            return crete_invite(invite)
    except Exception as e:
        logger.error(f"{invite} 注册失败！ Error{e}")
        # if "empty list" in e.__str__():
        #     return None
        # if not pik_go.inviseError:
        logger.error(f"开始重新注册")
        return crete_invite(invite)


if __name__ == "__main__":
    # # email = "zlyezm5338@cevipsa.com"
    # email = "hamidan206@otemdi.com"
    # password = "098poi"
    # pikpak_ = PikPak(email, password, run=False)
    # # pikpak_.set_proxy("114.132.202.246:8080")
    # # pikpak_.set_activation_code(98105081)
    # # pikpak_.run_req_2invite()
    # # pikpak_.save_share("VNxHRUombIy7SWJs5Oyw-TDxo1")
    # # pikpak_.get_self_invite_code()
    # pikpak_.get_self_vip_info()

    crete_invite(98105081)
