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
                sub_platform = 'osx/%s' % (os_machine)
            else:
                sub_platform = 'osx/universal'
            base_file = 'RetroArch.dmg'
            core_file = None
        elif os_platform == 'linux' or os_platform == 'windows':
            if os_machine == 'x86_64' or os_machine == 'x86':
                sub_platform = os_machine
            else:
                try:
                    sub_platform = retroarch_machine_map[os_machine]
                except KeyError:
                    pass
            base_file = 'RetroArch.7z'
            core_file = 'RetroArch_cores.7z'

        try:
            logger.debug("RetroArcher Emulators :: Sub platform for RetroArch is %s" % (sub_platform))
            return os_platform, sub_platform, base_file, core_file
        except NameError:
            logger.error("RetroArcher Emulators :: Could not detect sub platform for RetroArch")
            return os_platform, False, base_file, core_file

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
            os_platform, sub_platform, base_file, core_file = self.get_os_build()

            if not sub_platform:
                return False

            retroarch_os_build = '%s/%s/%s' % (os_platform, sub_platform, base_file)

            download_url = 'https://buildbot.libretro.com/stable/%s/%s' % (latest_version, retroarch_os_build)

            temp_dir = os.path.join(plexpy.CONFIG.TEMP_DIR, 'retroarch')

            download = download_helper.download_file(download_url, temp_dir)

            if not download:  # cannot continue
                logger.error("RetroArcher Emulators :: Cannot install/update RetroArch")
                return False

            root_dir = download_helper.extract_archive(download, temp_dir)
            destination_dir = plexpy.CONFIG.RETROARCH_DIR

            updated = download_helper.merge_update(os.path.join(temp_dir, root_dir), destination_dir)

            # shutil.rmtree(temp_dir)

            self.update_assets(['cheats'])

            return updated

        else:
            logger.debug(
                "RetroArcher Emulators :: The latest supported version of RetroArch is already added to RetroArcher")
            return True

    def update_assets(self, list_assets='*'):
        """Update Core info files and individual core files"""
        assets = {
            'assets': os.path.join(plexpy.CONFIG.RETROARCH_DIR, 'assets'),
            'autoconfig': os.path.join(plexpy.CONFIG.RETROARCH_DIR, 'autoconfig'),
            'cheats': os.path.join(plexpy.CONFIG.RETROARCH_DIR, 'cheats'),
            'database-cursors': os.path.join(plexpy.CONFIG.RETROARCH_DIR, 'database', 'cursors'),
            'database-rdb': os.path.join(plexpy.CONFIG.RETROARCH_DIR, 'database', 'rdb'),
            'info': os.path.join(plexpy.CONFIG.RETROARCH_DIR, 'info'),
            'overlays': os.path.join(plexpy.CONFIG.RETROARCH_DIR, 'overlays'),
            'shaders_cg': os.path.join(plexpy.CONFIG.RETROARCH_DIR, 'shaders', 'shaders_cg'),
            'shaders_glsl': os.path.join(plexpy.CONFIG.RETROARCH_DIR, 'shaders', 'shaders_glsl'),
            'shaders_slang': os.path.join(plexpy.CONFIG.RETROARCH_DIR, 'shaders', 'shaders_slang')
        }

        for key, value in assets.items():
            if key in list_assets or list_assets == '*':
                download_url = f'https://buildbot.libretro.com/assets/frontend/{key}.zip'
                temp_dir = os.path.join(plexpy.CONFIG.TEMP_DIR, 'retroarch')
                destination_dir = value

                if not os.path.isdir(destination_dir):
                    self.update_base()

                # updated = self.update(download_url, temp_dir, destination_dir)

                download = download_helper.download_file(download_url, temp_dir)

                if not download:  # cannot continue
                    logger.error("RetroArcher Emulators :: Cannot update RetroArch asset %s" % (key))
                    return False

                extracted_dir = os.path.join(temp_dir, key)
                root_dir = download_helper.extract_archive(download, extracted_dir)

                updated = download_helper.merge_update(extracted_dir, destination_dir)

                # shutil.rmtree(temp_dir)

        self.update_cores()

        return updated

    def update_cores(self):
        """Update individual core files"""

        os_platform, sub_platform, base_file, core_file = self.get_os_build()

        if not sub_platform:
            return False

        retroarch_os_build = '%s/%s/%s' % (os_platform, sub_platform, core_file)

        if plexpy.CONFIG.RETROARCH_NIGHTLY_ASSETS == 0:  # get stable cores from time of app release
            latest_version = self.get_latest_version()
            download_url = 'https://buildbot.libretro.com/stable/%s/%s' % (latest_version, retroarch_os_build)
        else:  # get nightly cores
            download_url = 'https://buildbot.libretro.com/nightly/%s' % (retroarch_os_build)

        temp_dir = os.path.join(plexpy.CONFIG.TEMP_DIR, 'retroarch')

        download = download_helper.download_file(download_url, temp_dir)

        if not download:  # cannot continue
            logger.error("RetroArcher Emulators :: Cannot install/update RetroArch cores")
            return False

        root_dir = download_helper.extract_archive(download, temp_dir)
        destination_dir = plexpy.CONFIG.RETROARCH_DIR

        updated = download_helper.merge_update(os.path.join(temp_dir, root_dir), destination_dir)

        # shutil.rmtree(temp_dir)

        return updated
