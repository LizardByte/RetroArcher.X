﻿# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from future.builtins import str

import requests
import threading

import plexpy
if plexpy.PYTHON2:
    import database
    import helpers
    import logger
else:
    from plexpy import database
    from plexpy import helpers
    from plexpy import logger


_ONESIGNAL_APP_ID = '3b4b666a-d557-4b92-acdf-e2c8c4b95357'
_ONESIGNAL_DISABLED = 'onesignal-disabled'

TEMP_DEVICE_TOKENS = {}


def set_temp_device_token(token=None, remove=False, add=False, success=False):
    global TEMP_DEVICE_TOKENS

    if token in TEMP_DEVICE_TOKENS and success:
        if isinstance(TEMP_DEVICE_TOKENS[token], threading.Timer):
            TEMP_DEVICE_TOKENS[token].cancel()
        TEMP_DEVICE_TOKENS[token] = True

    elif token in TEMP_DEVICE_TOKENS and remove:
        if isinstance(TEMP_DEVICE_TOKENS[token], threading.Timer):
            TEMP_DEVICE_TOKENS[token].cancel()
        del TEMP_DEVICE_TOKENS[token]

    elif token not in TEMP_DEVICE_TOKENS and add:
        invalidate_time = 5 * 60  # 5 minutes
        TEMP_DEVICE_TOKENS[token] = threading.Timer(invalidate_time, set_temp_device_token, args=[token, True])
        TEMP_DEVICE_TOKENS[token].start()
        logger._BLACKLIST_WORDS.add(token)


def get_temp_device_token(token=None):
    return TEMP_DEVICE_TOKENS.get(token)


def get_mobile_devices(device_id=None, device_token=None):
    where = where_id = where_token = ''
    args = []

    if device_id or device_token:
        where = 'WHERE '
        if device_id:
            where_id += 'device_id = ?'
            args.append(device_id)
        if device_token:
            where_token = 'device_token = ?'
            args.append(device_token)
        where += ' AND '.join([w for w in [where_id, where_token] if w])

    db = database.MonitorDatabase()
    result = db.select('SELECT * FROM mobile_devices %s' % where, args=args)

    return result


def get_mobile_device_by_token(device_token=None):
    if not device_token:
        return None

    return get_mobile_devices(device_token=device_token)


def add_mobile_device(device_id=None, device_name=None, device_token=None, friendly_name=None, onesignal_id=None):
    db = database.MonitorDatabase()

    keys = {'device_id': device_id}
    values = {'device_name': device_name,
              'device_token': device_token,
              'onesignal_id': onesignal_id}

    if friendly_name:
        values['friendly_name'] = friendly_name

    try:
        result = db.upsert(table_name='mobile_devices', key_dict=keys, value_dict=values)
        blacklist_logger()
    except Exception as e:
        logger.warn("RetroArcher MobileApp :: Failed to register mobile device in the database: %s." % e)
        return

    if result == 'insert':
        logger.info("RetroArcher MobileApp :: Registered mobile device '%s' in the database." % device_name)
    else:
        logger.debug("RetroArcher MobileApp :: Re-registered mobile device '%s' in the database." % device_name)

    threading.Thread(target=set_official, args=[device_id, onesignal_id]).start()
    return True


def get_mobile_device_config(mobile_device_id=None):
    if str(mobile_device_id).isdigit():
        mobile_device_id = int(mobile_device_id)
    else:
        logger.error("RetroArcher MobileApp :: Unable to retrieve mobile device config: invalid mobile_device_id %s." % mobile_device_id)
        return None

    db = database.MonitorDatabase()
    result = db.select_single('SELECT * FROM mobile_devices WHERE id = ?',
                              args=[mobile_device_id])

    if result['onesignal_id'] == _ONESIGNAL_DISABLED:
        result['onesignal_id'] = ''

    return result


def set_mobile_device_config(mobile_device_id=None, **kwargs):
    if str(mobile_device_id).isdigit():
        mobile_device_id = int(mobile_device_id)
    else:
        logger.error("RetroArcher MobileApp :: Unable to set exisiting mobile device: invalid mobile_device_id %s." % mobile_device_id)
        return False

    keys = {'id': mobile_device_id}
    values = {'friendly_name': kwargs.get('friendly_name', '')}

    db = database.MonitorDatabase()
    try:
        db.upsert(table_name='mobile_devices', key_dict=keys, value_dict=values)
        logger.info("RetroArcher MobileApp :: Updated mobile device agent: mobile_device_id %s." % mobile_device_id)
        blacklist_logger()
        return True
    except Exception as e:
        logger.warn("RetroArcher MobileApp :: Unable to update mobile device: %s." % e)
        return False


def delete_mobile_device(mobile_device_id=None, device_id=None):
    db = database.MonitorDatabase()

    if mobile_device_id:
        logger.debug("RetroArcher MobileApp :: Deleting mobile_device_id %s from the database." % mobile_device_id)
        result = db.action('DELETE FROM mobile_devices WHERE id = ?', args=[mobile_device_id])
        return True
    elif device_id:
        logger.debug("RetroArcher MobileApp :: Deleting device_id %s from the database." % device_id)
        result = db.action('DELETE FROM mobile_devices WHERE device_id = ?', args=[device_id])
        return True
    else:
        return False


def set_official(device_id, onesignal_id):
    db = database.MonitorDatabase()
    official = validate_onesignal_id(onesignal_id=onesignal_id)

    try:
        result = db.action('UPDATE mobile_devices SET official = ? WHERE device_id = ?',
                           args=[official, device_id])
    except Exception as e:
        logger.warn("RetroArcher MobileApp :: Failed to set official flag for device: %s." % e)
        return


def set_last_seen(device_token=None):
    db = database.MonitorDatabase()
    last_seen = helpers.timestamp()

    try:
        result = db.action('UPDATE mobile_devices SET last_seen = ? WHERE device_token = ?',
                           args=[last_seen, device_token])
    except Exception as e:
        logger.warn("RetroArcher MobileApp :: Failed to set last_seen time for device: %s." % e)
        return


def validate_onesignal_id(onesignal_id):
    if onesignal_id is None:
        return 0
    elif onesignal_id == _ONESIGNAL_DISABLED:
        return 2

    headers = {'Content-Type': 'application/json'}
    payload = {'app_id': _ONESIGNAL_APP_ID}

    logger.info("RetroArcher MobileApp :: Validating OneSignal ID")
    try:
        r = requests.get('https://onesignal.com/api/v1/players/{}'.format(onesignal_id), headers=headers, json=payload)
        status_code = r.status_code
        logger.info("RetroArcher MobileApp :: OneSignal ID validation returned status code %s", status_code)
        return int(status_code == 200)
    except Exception as e:
        logger.warn("RetroArcher MobileApp :: Failed to validate OneSignal ID: %s." % e)
        return -1


def revalidate_onesignal_ids():
    for device in get_mobile_devices():
        set_official(device['device_id'], device['onesignal_id'])


def blacklist_logger():
    devices = get_mobile_devices()
    for d in devices:
        logger.blacklist_config(d)
