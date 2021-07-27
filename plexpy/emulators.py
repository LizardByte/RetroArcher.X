import platform
import os
import re
import requests
import subprocess

import plexpy
from plexpy import logger

supported_version = 'v1.9.7'


class RetroArch(object):
    """functions related to retroarch"""

    def get_current_version(self):
        """return the current version of retroarch"""
        retroarch_dir = plexpy.CONFIG.RETROARCH_DIR

        version_full = subprocess.run([os.path.join(retroarch_dir, 'retroarch'), '--version'], capture_output=True)
        version = re.search(r"(v(\d+)\.(\d+)\.\d+)", str(version_full.stderr)).group(0)

        return version

    def get_os_build(self):
        """return the os build needed to build the download url"""
        retroarch_platform_map = {
            'Darwin': 'apple',
            'Linux': 'linux',
            'Windows': 'windows'
        }

        os_platform = retroarch_platform_map[platform.system()]
        logger.debug("RetroArcher Emulators :: Platform for RetroArch is %s" % (os_platform))

        os_machine = platform.machine()
        logger.debug("RetroArcher Emulators :: Platform machine reported as %s" % (os_machine))

        if os_platform == 'apple':
            if os_machine == 'x86_64':
                sub_platform = 'osx/%s/RetroArch.dmg' % (os_machine)
            else:
                sub_platform = 'osx/universal/RetroArch.dmg'
        elif os_platform == 'linux' or os_platform == 'windows':
            if os_machine == 'x86_64' or os_machine == 'x86':
                sub_platform = '%s/RetroArch.7z' % (os_machine)

        try:
            logger.debug("RetroArcher Emulators :: Sub platform for RetroArch is %s" % (sub_platform))
            return os_platform, sub_platform
        except NameError:
            logger.error("RetroArcher Emulators :: Could not detect sub platform for RetroArch")
            return os_platform, False

    def launch_emu(self):
        """Function to launch emulator with core and game"""
        core = r"cores\mupen64plus_next_libretro.dll"
        game = r"\\archer\l\RetroArcher\roms\Nintendo 64\007 - GoldenEye (USA).zip"

        retroarch = subprocess.run(['retroarch', "-L", core, game], capture_output=True)

        if retroarch.stdout == b'' and retroarch.stderr == b'':
            logger.error("RetroArcher Emulators :: RetroArch failed to start game %s with core %s" % (game, core))
            return False
        else:
            return True

    def update_base(self):
        """Function installs/updates retroarch"""
        current_version = self.get_current_version()

        if current_version != supported_version:
            logger.debug("RetroArcher Emulators :: Current version of RetroArch is %s" % (current_version))
            logger.debug("RetroArcher Emulators :: Latest supported version of RetroArch is %s" % (supported_version))

            os_platform, sub_platform = self.get_os_build()

            if not sub_platform:
                return False

            retroarch_os_build = '%s/%s' % (os_platform, sub_platform)

            download_url = 'https://buildbot.libretro.com/stable/%s/%s' % (supported_version, retroarch_os_build)

        else:
            logger.debug(
                "RetroArcher Emulators :: The latest supported version of RetroArch is already added to RetroArcher")
