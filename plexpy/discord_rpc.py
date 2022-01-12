import time
import struct

import pypresence
from pypresence import Presence

from plexpy import logger
from plexpy.helpers import anon_url

client_id = '873981670204776580'  # Enter your Application ID here.


def rpc_update(platform_name, emulator_name, game_name):
    start_time = int(time.time())
    rpc = Presence(client_id=client_id)
    rpc.connect()

    try:
        rpc.update(
            state=f'Playing {game_name}',
            details=f'{platform_name} in {emulator_name}',
            large_image=platform_name.lower().replace(' ', '_'),
            large_text=platform_name,
            small_image="retroarcher",
            small_text="RetroArcher",
            start=start_time,
            buttons=[
                {'label': 'RetroArcher', 'url': anon_url('https://retroarcher.github.io/')},
                {'label': 'Support', 'url': anon_url('https://www.patreon.com/join/retroarcher')}
            ]
        )
    except pypresence.exceptions.InvalidPipe as e:
        logger.warning("RetroArcher Discord RPC :: Discord must be running: %s" % (e))
    except pypresence.exceptions.InvalidID as e:
        logger.critical("RetroArcher Discord RPC :: Invalid Client ID: %s" % (e))
    except struct.error as e:
        logger.critical("RetroArcher Discord RPC :: Invalid Client ID: %s" % (e))
    except pypresence.exceptions.ServerError as e:
        logger.warning("RetroArcher Discord RPC :: Invalid link/name/id: %s" % (e))
