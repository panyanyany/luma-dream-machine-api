import os
import json
import logging
import mimetypes
import requests
from urllib.parse import urljoin, urlparse, urlencode, urlunparse
from requests.structures import CaseInsensitiveDict

from api_types import GenerationItem
from util import update_cookies

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ErrCodes:
    NotLogin = 401
    UnknownError = 500


class MyError(Exception):
    def __init__(self, code, message=None):
        self.code = code
        self.message = message


class Sdk:
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'referrer-Policy': 'no-referrer-when-downgrade',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        "origin": "https://lumalabs.ai",
        "referer": "https://lumalabs.ai",
    }

    LOGIN_RE_CAPTCHA_KEY = ''
    SITE_KEY = ''
    API_BASE = os.getenv('LUMA_API_BASE', 'https://internal-api.virginia.labs.lumalabs.ai')

    def __init__(self, cookies=None, username=None, password=None, profile_root=None):
        self.cookies = cookies or []
        self.username = username
        self.password = password
        self.profile_root = profile_root
        if not os.path.exists(profile_root):
            os.makedirs(profile_root, exist_ok=True)
        self.cookies_file = os.path.join(profile_root, 'cookies.json')
        self.after_cookies_updated_callback = self.save_cookies

        if os.path.exists(self.cookies_file):
            with open(self.cookies_file, 'r', encoding='utf8') as f:
                self.cookies = json.load(f)


    def save_cookies(self, cookies):
        with open(self.cookies_file, 'w', encoding='utf8') as f:
            json.dump(cookies, f, indent=2)

    def extend(self, video_id, params):
        url = f'{self.API_BASE}/api/photon/v1/generations/{video_id}/extend'
        resp = self.send_post_json(url, params)
        return resp.json()

    def add_access_token(self, access_token):
        cookie = {'name': 'access_token', 'value': access_token, 'domain': 'internal-api.virginia.labs.lumalabs.ai', 'path': '/', 'secure': True, 'httpOnly': True, 'sameSite': 'None'}
        self.cookies.append(cookie)

    def get_generations(self):
        url = f'{self.API_BASE}/api/photon/v1/user/generations/'
        query = {"offset": "0", "limit": "10"}
        u = urlparse(url)
        u = u._replace(query=urlencode(query))
        resp = self.send_get(urlunparse(u))
        items = resp.json()

        # GenerationItem
        gi_list: list[GenerationItem] = []
        for item in items:
            gi = GenerationItem(**item)
            gi_list.append(gi)

        return gi_list

    def prepare_generate(self, prompt, file_path=None, expand_prompt=True):
        url = f'{self.API_BASE}/api/photon/v1/generations/'
        payload = {
            "user_prompt": prompt,
            "aspect_ratio": "16:9",
            "expand_prompt": expand_prompt
        }
        if file_path:
            payload['image_url'] = self.upload_image(file_path)
        return payload

    def generate(self, prompt, file_path=None, expand_prompt=True):
        url = f'{self.API_BASE}/api/photon/v1/generations/'
        payload = self.prepare_generate(prompt, file_path, expand_prompt)
        logger.info(f'generate payload={json.dumps(payload, indent=2)}')
        resp = self.send_post_json(url, payload)
        return resp.json()[0]["id"]

    def upload_image(self, file_path):
        signed_upload = self.get_signed_upload(os.path.basename(file_path))
        pre_signed_url = signed_upload['presigned_url']
        public_url = signed_upload['public_url']
        content_type = mimetypes.guess_type(file_path)[0] or 'image/jpeg'
        headers = {'Content-Type': content_type, 'Content-Length': str(os.path.getsize(file_path))}

        with open(file_path, 'rb') as f:
            resp = requests.put(pre_signed_url, data=f, headers=headers)
        if resp.status_code != 200:
            raise Exception(f'Failed to upload image: {resp.status_code}')
        return public_url

    def get_signed_upload(self, filename):
        url = f'{self.API_BASE}/api/photon/v1/generations/file_upload'
        params = {'file_type': 'image', 'filename': 'file.jpg'}
        u = urlparse(url)
        u = u._replace(query=urlencode(params))
        resp = self.send_post(urlunparse(u))
        return resp.json()

    def is_login(self):
        try:
            self.get_generations()
            return True
        except MyError as e:
            if e.code == ErrCodes.NotLogin:
                return False
            raise e

    def send_post_json(self, url, body=None, headers=None):
        headers = headers or {}
        headers['Content-Type'] = 'application/json'
        return self.send_post(url, headers=headers, body=json.dumps(body))

    def send_post(self, url, headers=None, body=None, method='POST'):
        headers = {**self.headers, **headers}
        headers['cookie'] = self.get_cookie_str()
        logger.info(f'sendPost url={url}')
        resp = requests.request(method, url, headers=headers, data=body)
        logger.debug(f'sendPost response({resp.status_code}), url={url}')
        self.check_resp(resp)
        cookies = resp.cookies.get_dict()
        self.update_cookies(cookies)
        return resp

    def send_get(self, url, headers=None):
        headers = headers or {}
        headers = {**self.headers, **headers}
        headers['cookie'] = self.get_cookie_str()
        logger.info(f'sendGet url={url}')
        resp = requests.get(url, headers=headers)
        logger.debug(f'sendGet response({resp.status_code}), url={url}')
        self.check_resp(resp)
        # cookies = resp.cookies.get_dict()
        self.update_cookies(resp.cookies)
        return resp

    def update_cookies(self, cookies: dict):
        cookies = [
            {'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path}
            for c in cookies
        ]
        # cookies_list = [{'name': k, 'value': v} for k, v in cookies.items()]
        # print(cookies)
        self.cookies = update_cookies(self.cookies, cookies)
        self.after_cookies_updated_callback(self.cookies)

    def get_cookie_str(self):
        return '; '.join([f'{ck["name"]}={ck["value"]}' for ck in self.cookies])

    def get_filename(self, url):
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        filename = filename.replace(' ', '_')
        return filename

    def check_resp(self, resp):
        if not resp.ok:
            logger.debug(f'headers: {resp.headers}')
            if resp.status_code == 401:
                text = resp.text
                logger.info(f'checkResp status=401, text={text}')
                raise MyError(ErrCodes.NotLogin)
            else:
                self.throw_resp_error(resp)

    def throw_resp_error(self, resp):
        text = resp.text
        logger.info(f'checkResp status={resp.status_code} text={text[:1024]}')
        raise MyError(ErrCodes.UnknownError, f'HTTP {resp.status_code} {resp.reason}, body={text}')

    def usage(self):
        url = f'{self.API_BASE}/api/photon/v1/subscription/usage'
        resp = self.send_get(url)
        return resp.json()
