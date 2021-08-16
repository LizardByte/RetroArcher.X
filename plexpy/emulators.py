import platform
import os
import re

from bs4 import BeautifulSoup
import requests
import subprocess
import configparser
import itertools

import plexpy
from plexpy import logger
from plexpy import download_helper
from plexpy import platforms


class RetroArch:
    """functions related to retroarch"""

    def get_current_version(self):
        """return the current version of retroarch"""
        emulator_dir = plexpy.CONFIG.RETROARCH_DIR

        try:
            version_full = subprocess.run([os.path.join(emulator_dir, 'retroarch'), '--version'], capture_output=True)
        except FileNotFoundError:
            return False

        current = re.search(r"(v((\d+)\.(\d+)\.(\d+)))", str(version_full.stderr)).group(2)
        logger.debug("RetroArcher Emulators :: Current version of RetroArch is %s" % (current))

        return current

    def get_latest_version(self):
        """return the latest version from github"""
        url = 'https://api.github.com/repos/libretro/retroarch/releases'

        try:
            response = requests.get(url)
        except requests.RequestException as e:
            logger.error("RetroArcher Emulators :: Requests error: %s" % (e))
            return False

        releases = response.json()

        for release in releases:
            if not release['prerelease'] and not release['draft']:
                #latest = value['tag_name'][1:]  # example result "v1.9.7" before stripping off the v
                latest = re.search(r"(v((\d+)\.(\d+)\.(\d+)))", release['tag_name']).group(2)
                logger.info("RetroArcher Emulators :: Latest RetroArch version: %s" % (latest))
                return latest

        logger.error("RetroArcher Emulators :: Unable to find release of RetroArch")
        return False

    def get_os_build(self):
        """return the os build needed to build the download url"""
        emulator_platform_map = {
            'Darwin': 'apple',
            'Linux': 'linux',
            'Windows': 'windows'
        }

        emulator_machine_map = {
            'AMD64': 'x86_64'
        }

        os_platform = emulator_platform_map[platform.system()]
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
                    sub_platform = emulator_machine_map[os_machine]
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

        emulator = subprocess.run(['retroarch', "-L", core, game], capture_output=True)

        if emulator.stdout == b'' and emulator.stderr == b'':
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

            emulator_os_build = '%s/%s/%s' % (os_platform, sub_platform, base_file)

            download_url = 'https://buildbot.libretro.com/stable/%s/%s' % (latest_version, emulator_os_build)

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

        emulator_os_build = '%s/%s/%s' % (os_platform, sub_platform, core_file)

        if plexpy.CONFIG.RETROARCH_NIGHTLY_ASSETS == 0:  # get stable cores from time of app release
            latest_version = self.get_latest_version()
            download_url = 'https://buildbot.libretro.com/stable/%s/%s' % (latest_version, emulator_os_build)
        else:  # get nightly cores
            download_url = 'https://buildbot.libretro.com/nightly/%s' % (emulator_os_build)

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

    def update_mapping(self, mapping):
        """update mapping dictionary"""
        core_folder = os.path.join(plexpy.CONFIG.RETROARCH_DIR, 'cores')
        info_folder = os.path.join(plexpy.CONFIG.RETROARCH_DIR, 'info')

        for core in os.listdir(core_folder):
            core_name = core.split('.')[0]
            info_file = os.path.join(info_folder, f'{core_name}.info')

            core_info = configparser.ConfigParser(interpolation=None)
            # interpolation set to None to prevent issues with strings that contain "%"

            try:
                with open(info_file, 'r') as f:
                    try:
                        core_info.read_file(itertools.chain(['[CORE_INFO]'], f))
                    except configparser.DuplicateOptionError as e:
                        logger.error("RetroArcher Emulators :: RetroArch core info file %s contains duplicate options" % (info_file))
                        logger.error("RetroArcher Emulators :: Duplicate option error %s" % (e))
                        continue
            except FileNotFoundError:
                logger.warning("RetroArcher Emulators :: RetroArch core info file %s not found" % (info_file))
                continue

            for core_info_key, core_info_value in core_info['CORE_INFO'].items():
                if core_info_value.strip().startswith('"') and core_info_value.strip().endswith('"'):
                    # strip off first and last double quotes
                    core_info['CORE_INFO'][core_info_key] = core_info_value.strip()[1:-1]

            strict_matching = plexpy.CONFIG.RETROARCH_STRICT_CORE_MATCHING

            for mapping_key, mapping_value in mapping.items():
                # set these for each loop cycle
                fallback = False
                matched = False

                # mapping_key is retroarcher platform name
                try:
                    databases = core_info['CORE_INFO']['database'].split('|')
                    for database in databases:
                        if database in mapping_value['systemIds']['retroarch']['databases']:
                            matched = True
                except KeyError:
                    fallback = True  # force checking system_id when database is not in info file

                if (matched and strict_matching) or fallback:
                    try:
                        if core_info['CORE_INFO']['systemid'] in mapping_value['systemIds']['retroarch']['ids']:
                            matched = True
                        else:
                            matched = False
                    except KeyError:
                        if matched:  # continue because there is no systemid in info file
                            pass
                        else:  # database and systemid missing from info file
                            matched = False

                if matched:
                    try:
                        mapping[mapping_key]['emulators']['retroarch']['cores'][core] = {}

                        forced_list_keys = ['supported_extensions', 'database', 'authors']

                        for core_info_key, core_info_value in core_info['CORE_INFO'].items():
                            if '|' in core_info_value or core_info_key in forced_list_keys:
                                # convert values with pipes "|" to list
                                # ensure keys in force_list_keys are always list
                                core_info_value = core_info_value.split('|')

                                if core_info_key == 'supported_extensions':
                                    # add core extensions to platform extensions list
                                    for extension in core_info_value:
                                        if extension not in mapping[mapping_key]['romExtensions']:
                                            mapping[mapping_key]['romExtensions'].append(extension)

                            # set the core_info_value for each core_info_key
                            mapping[mapping_key]['emulators']['retroarch']['cores'][core][core_info_key] = core_info_value

                    except KeyError as e:
                        pass


class RPCS3:
    """functions related to rpcs3"""

    def get_current_version(self):
        """return the current version of rpcs3"""
        emulator_dir = plexpy.CONFIG.RPCS3_DIR

        try:
            version_full = subprocess.run([os.path.join(emulator_dir, 'rpcs3'), '--version'], capture_output=True)
        except FileNotFoundError:
            return False

        current = re.search(r"((RPCS3 )((\d+)\.(\d+)\.(\d+)-(\d+)))", str(version_full.stdout)).group(3)
        logger.debug("RetroArcher Emulators :: Current version of RPCS3 is %s" % (current))

        return current

    def get_latest_version(self, sub_platform, base_file_ends_with):
        """return the latest version from github"""
        url = f'https://api.github.com/repos/rpcs3/{sub_platform}/releases'

        try:
            response = requests.get(url)
        except requests.RequestException as e:
            logger.error("RetroArcher Emulators :: Requests error: %s" % (e))
            return False

        releases = response.json()

        for release in releases:
            if not release['prerelease'] and not release['draft']:
                latest = release['name']
                logger.info("RetroArcher Emulators :: Latest RPCS3 version: %s" % (latest))

                for asset in release['assets']:
                    if asset['name'].endswith(base_file_ends_with):
                        base_file = asset['browser_download_url']

                try:
                    return latest, base_file
                except NameError:
                    pass

        logger.error("RetroArcher Emulators :: Unable to find release of RPCS3")
        return False

    def get_os_build(self):
        """return the os build needed to build the download url"""
        emulator_platform_map = {
            'Darwin': 'mac',
            'Linux': 'linux',
            'Windows': 'win'
        }

        os_platform = emulator_platform_map[platform.system()]
        logger.debug("RetroArcher Emulators :: Platform for RPCS3 is %s" % (os_platform))

        sub_platform = 'rpcs3-binaries-%s' % (os_platform)

        if os_platform == 'mac':
            base_file_ends_with = '_mac64.dmg'  # no releases for this repository yet
        elif os_platform == 'linux':
            base_file_ends_with = '_linux64.AppImage'
        elif os_platform == 'win':
            base_file_ends_with = '_win64.7z'
        else:
            base_file_ends_with = None

        logger.debug("RetroArcher Emulators :: Sub platform for RPCS3 is %s" % (sub_platform))
        return os_platform, sub_platform, base_file_ends_with

    def launch_emu(self, game):
        """Function to launch emulator with core and game"""
        game = r"\\archer\l\RetroArcher\roms\Sony Playstation 3\..."

        emulator = subprocess.run(['rpcs3', "-L", game], capture_output=True)

        if emulator.stdout == b'' and emulator.stderr == b'':
            logger.error("RetroArcher Emulators :: RPCS3 failed to start game %s" % (game))
            return False
        else:
            return True

    def update_base(self):
        """Function installs/updates rpcs3"""
        current_version = self.get_current_version()

        os_platform, sub_platform, base_file_ends_with = self.get_os_build()

        if os_platform == 'mac':
            return False

        latest_version, base_file = self.get_latest_version(sub_platform, base_file_ends_with)

        if current_version != latest_version:

            download_url = base_file

            temp_dir = os.path.join(plexpy.CONFIG.TEMP_DIR, 'rpcs3')

            download = download_helper.download_file(download_url, temp_dir)

            if not download:  # cannot continue
                logger.error("RetroArcher Emulators :: Cannot install/update RPCS3")
                return False

            root_dir = download_helper.extract_archive(download, temp_dir)
            destination_dir = plexpy.CONFIG.RPCS3_DIR

            updated = download_helper.merge_update(temp_dir, destination_dir)

            # shutil.rmtree(temp_dir)

            return updated

        else:
            logger.debug(
                "RetroArcher Emulators :: The latest supported version of RPCS3 is already added to RetroArcher")
            return True

    def update_mapping(self, mapping):
        """update mapping dictionary"""

        supported_extensions = ['bin']
        emulator = 'rpcs3'

        for mapping_key, value_key in mapping.items():
            try:
                mapping[mapping_key]['emulators'][emulator]

                # add core extensions to platform extensions list
                for extension in supported_extensions:
                    if extension not in mapping[mapping_key]['romExtensions']:
                        mapping[mapping_key]['romExtensions'].append(extension)

            except KeyError:
                continue


class Cemu:
    """functions related to cemu"""

    def get_current_version(self):
        """return the current version of cemu"""
        emulator_dir = plexpy.CONFIG.CEMU_DIR

        file_info = plexpy.helpers.get_file_properties(os.path.join(emulator_dir, 'cemu.exe'))
        current = file_info['StringFileInfo']['ProductVersion']
        logger.debug("RetroArcher Emulators :: Current version of Cemu is %s" % (current))

        return current

    def get_latest_version(self):
        """return the latest version from cemu website"""
        url = 'https://cemu.info'

        try:
            response = requests.get(url)
        except requests.RequestException as e:
            logger.error("RetroArcher Emulators :: Requests error: %s" % (e))
            return False

        soup = BeautifulSoup(response.content, "lxml")

        for item in soup.find_all('p', class_='font-big custom'):
            latest = False
            try:
                latest = re.search(r"(Cemu ((\d+)\.(\d+)\.(\d+\w*)) \(((\d{4})\-(\d{2})\-(\d{2}))\))",
                                   item.string.strip()).group(2)
            except AttributeError:
                pass

            try:
                if latest:
                    logger.info("RetroArcher Emulators :: Latest Cemu version: %s" % (latest))
                    break
            except NameError:
                pass

        for item in soup.find_all('a', class_='btn btn-info btn-lg btn-block'):
            base_file = item.get('href')
            if base_file.endswith('.zip'):
                return latest, base_file

        logger.error("RetroArcher Emulators :: Unable to find release of Cemu")
        return False

    def get_os_build(self):
        """return the os build, cemu only supports windows"""
        emulator_platform_map = {
            'Darwin': 'mac',
            'Linux': 'linux',
            'Windows': 'windows'
        }

        os_platform = emulator_platform_map[platform.system()]

        if os_platform == 'mac':
            logger.debug("RetroArcher Emulators :: Platform %s not supported by Cemu" % (os_platform))
            return False
        elif os_platform == 'linux':
            logger.debug("RetroArcher Emulators :: Platform %s not supported by Cemu" % (os_platform))
            return False
        elif os_platform == 'windows':
            logger.debug("RetroArcher Emulators :: Platform for Cemu is %s" % (os_platform))
            return True
        else:
            logger.debug("RetroArcher Emulators :: Platform not supported by Cemu")
            return False

    def launch_emu(self, game):
        """Function to launch emulator"""
        game = r"\\archer\l\RetroArcher\roms\Nintendo WiiU\..."

        emulator = subprocess.run(['cemu', "-L", game], capture_output=True)

        if emulator.stdout == b'' and emulator.stderr == b'':
            logger.error("RetroArcher Emulators :: Cemu failed to start game %s" % (game))
            return False
        else:
            return True

    def update_base(self):
        """Function installs/updates cemu"""
        current_version = self.get_current_version()

        supported = self.get_os_build()

        if not supported:
            return False

        latest_version, base_file = self.get_latest_version()

        if current_version != latest_version:

            download_url = base_file

            temp_dir = os.path.join(plexpy.CONFIG.TEMP_DIR, 'cemu')

            download = download_helper.download_file(download_url, temp_dir)

            if not download:  # cannot continue
                logger.error("RetroArcher Emulators :: Cannot install/update Cemu")
                return False

            root_dir = download_helper.extract_archive(download, temp_dir)
            destination_dir = plexpy.CONFIG.CEMU_DIR

            updated = download_helper.merge_update(os.path.join(temp_dir, root_dir), destination_dir)

            # shutil.rmtree(temp_dir)

            return updated

        else:
            logger.debug(
                "RetroArcher Emulators :: The latest supported version of Cemu is already added to RetroArcher")
            return True

    def update_mapping(self, mapping):
        """update mapping dictionary"""

        supported_extensions = ['rpx', 'wud']
        emulator = 'cemu'

        for mapping_key, value_key in mapping.items():
            try:
                mapping[mapping_key]['emulators'][emulator]

                # add core extensions to platform extensions list
                for extension in supported_extensions:
                    if extension not in mapping[mapping_key]['romExtensions']:
                        mapping[mapping_key]['romExtensions'].append(extension)

            except KeyError:
                continue


def update_emulators():
    emulators = [RetroArch, RPCS3, Cemu]

    for emulator in emulators:
        emulator().update_base()


def update_mapping():
    emulators = [RetroArch, RPCS3, Cemu]

    mapping = platforms.mapping

    for emulator in emulators:
        emulator().update_mapping(mapping)
