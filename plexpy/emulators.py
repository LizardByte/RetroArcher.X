import platform
import os
import re

import requests
import shutil
import subprocess

import plexpy
from plexpy import logger
from plexpy import download_helper


class RetroArch:
    """functions related to retroarch"""

    def get_current_version(self):
        """return the current version of retroarch"""
        retroarch_dir = plexpy.CONFIG.RETROARCH_DIR

        try:
            version_full = subprocess.run([os.path.join(retroarch_dir, 'retroarch'), '--version'], capture_output=True)
        except FileNotFoundError:
            return False

        current = re.search(r"(v(\d+)\.(\d+)\.\d+)", str(version_full.stderr)).group(0)[1:]
        logger.debug("RetroArcher Emulators :: Current version of RetroArch is %s" % (current))

        return current

    def get_latest_version(self):
        """return the latest version from github"""
        url = 'https://api.github.com/repos/libretro/retroarch/releases'

        try:
            response = requests.get(url)
        except requests.RequestException as e:
            logger.error("RetroArcher Emulators :: Download error: %s" % (e))
            return False

        releases = response.json()

        for release in releases:
            if not release['prerelease'] and not release['draft']:
                #latest = value['tag_name'][1:]  # example result "v1.9.7" before stripping off the v
                latest = re.search(r"(v(\d+)\.(\d+)\.\d+)", release['tag_name']).group(0)[1:]
                logger.info("RetroArcher Emulators :: Latest RetroArch version: %s" % (latest))
                return latest

        logger.error("RetroArcher Emulators :: Unable to find release of RetroArch")
        return False

    def get_os_build(self):
        """return the os build needed to build the download url"""
        retroarch_platform_map = {
            'Darwin': 'apple',
            'Linux': 'linux',
            'Windows': 'windows'
        }

        retroarch_machine_map = {
            'AMD64': 'x86_64'
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
            else:
                try:
                    sub_platform = '%s/RetroArch.7z' % (retroarch_machine_map[os_machine])
                except KeyError:
                    pass

        try:
            logger.debug("RetroArcher Emulators :: Sub platform for RetroArch is %s" % (sub_platform))
            return os_platform, sub_platform
        except NameError:
            logger.error("RetroArcher Emulators :: Could not detect sub platform for RetroArch")
            return os_platform, False

    def launch_emu(self, core, game):
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

        latest_version = self.get_latest_version()

        if current_version != latest_version:
            os_platform, sub_platform = self.get_os_build()

            if not sub_platform:
                return False

            retroarch_os_build = '%s/%s' % (os_platform, sub_platform)

            download_url = 'https://buildbot.libretro.com/stable/%s/%s' % (latest_version, retroarch_os_build)

            temp_dir = os.path.join(plexpy.CONFIG.TEMP_DIR, 'retroarch')

            download = download_helper.download_file(download_url, temp_dir)

            if not download:  # cannot continue
                logger.error("RetroArcher Emulators :: Cannot install/update RetroArch")
                return False

            root_dir = download_helper.extract_archive(download, temp_dir)

            updated = download_helper.merge_update(os.path.join(temp_dir, root_dir), plexpy.CONFIG.RETROARCH_DIR)

            shutil.rmtree(temp_dir)

            return updated

        else:
            logger.debug(
                "RetroArcher Emulators :: The latest supported version of RetroArch is already added to RetroArcher")
            return True
