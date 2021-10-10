import platform
import os
import re

import requests
import subprocess

import plexpy
from plexpy import logger
from plexpy import download_helper


class Sunshine:
    """functions related to sunshine"""

    def get_current_version(self):
        """return the current version of sunshine"""
        streamer_dir = plexpy.CONFIG.SUNSHINE_DIR

        return False  # cannot get version of Sunshine yet

    def get_latest_version(self, base_file_ends_with):
        """return the latest version from github"""
        url = 'https://api.github.com/repos/loki-47-6F-64/sunshine/releases'

        try:
            response = requests.get(url)
        except requests.RequestException as e:
            logger.error("RetroArcher Streamer :: Requests error: %s" % (e))
            return False

        releases = response.json()

        for release in releases:
            if not release['prerelease'] and not release['draft']:
                latest = release['name']
                logger.info("RetroArcher Streamer :: Latest Sunshine version: %s" % (latest))

                for asset in release['assets']:
                    if asset['name'].lower().endswith(base_file_ends_with):
                        base_file = asset['browser_download_url']

                try:
                    return latest, base_file
                except NameError:
                    pass

        logger.error("RetroArcher Streamer :: Unable to find release of Sunshine")
        return False

    def get_os_build(self):
        """return the os build needed to build the download url"""
        if platform.system() == 'Darwin':
            base_file_ends_with = 'mac.dmg'  # no releases for mac yet
        elif platform.system() == 'Linux':
            if 'ubuntu' in platform.version().lower():
                ubuntu_version = re.search(r"#([0-9]*)~(([0-9]*)\.([0-9]*))\.([0-9]*)\-(Ubuntu)|(ubuntu)",
                                           str(platform.version())).group(2)

                base_file_ends_with = f"{ubuntu_version.replace('.', '')}.deb"  # possible to return non existing file
            else:
                base_file_ends_with = 'debian.deb'  # lazy method, assume debian if not ubuntu
        elif platform.system() == 'Windows':
            base_file_ends_with = 'windows.zip'
        else:
            base_file_ends_with = None

        return platform.system(), base_file_ends_with

    def launch_streamer(self):
        """Function to launch streamer"""
        streamer = subprocess.run(['sunshine'], capture_output=True)

        if streamer.stdout == b'' and streamer.stderr == b'':
            logger.error("RetroArcher Streamer :: Sunshine failed to start")
            return False
        else:
            return True

    def update_base(self):
        """Function installs/updates sunshine"""
        current_version = self.get_current_version()

        os_platform, base_file_ends_with = self.get_os_build()

        if os_platform == 'Darwin' or base_file_ends_with is None:
            return False

        latest_version, base_file = self.get_latest_version(base_file_ends_with)

        if current_version != latest_version:

            download_url = base_file

            temp_dir = os.path.join(plexpy.CONFIG.TEMP_DIR, 'sunshine')

            download = download_helper.download_file(download_url, temp_dir)

            if not download:  # cannot continue
                logger.error("RetroArcher Streamer :: Cannot install/update Sunshine")
                return False

            if os_platform == 'Windows':
                root_dir = download_helper.extract_archive(download, temp_dir)
                destination_dir = plexpy.CONFIG.SUNSHINE_DIR

                updated = download_helper.merge_update(temp_dir, destination_dir)

                # shutil.rmtree(temp_dir)

            return updated

        else:
            logger.debug(
                "RetroArcher Streamer :: The latest supported version of Sunshine is already added to RetroArcher")
            return True


def update_streamer():
    streamers = [Sunshine]

    for streamer in streamers:
        streamer().update_base()
