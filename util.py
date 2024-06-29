from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def is_cookie_expired(cookie: Dict[str, Any]) -> bool:
    expires = cookie.get('expires')
    if expires is None:
        return False
    return expires < datetime.now()


def update_cookies(src_cookies: List[Dict[str, Any]], dst_cookies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    existed_cookies: Dict[str, Dict[str, Any]] = {}

    for ck in dst_cookies:
        if is_cookie_expired(ck):
            logger.debug(f"delete expired cookie: {ck['name']}")
            continue
        existed_cookies[ck['name']] = ck

    for ck in src_cookies:
        old_ck = existed_cookies.get(ck['name'])
        if is_cookie_expired(ck):
            if old_ck:
                logger.debug(f"delete existed cookie: {ck['name']}")
                del existed_cookies[ck['name']]
            continue
        if not old_ck:
            logger.debug(f"add new cookie: {ck['name']}={ck['value']}")
        elif ck['value'] != old_ck['value']:
            logger.debug(f"update cookie: {ck['name']}={old_ck['value']} => {ck['value']}")
        existed_cookies[ck['name']] = ck

    return list(existed_cookies.values())
