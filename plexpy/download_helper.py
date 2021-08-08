import os
import platform
import requests
import shutil
import subprocess

import zipfile
import py7zr

import plexpy
from plexpy import logger

sevenzip_version = '7z1900-x64'


def download_7z():
    url = f'https://www.7-zip.org/a/{sevenzip_version}.exe'

    temp_dir = os.path.join(plexpy.CONFIG.TEMP_DIR, '7zip')

    download_file(url, temp_dir)

    installer_path = os.path.join(temp_dir, f'{sevenzip_version}.exe')
    temp_path = os.path.join(temp_dir, '7zip')

    extract_archive(installer_path, temp_path)  # cannot extract exe

    """ # this requires elevated permissions
    command_args = [installer_path, '/S', f'/D="{temp_path}"']
    try:
        proc = subprocess.run(command_args, check=True)
    except subprocess.CalledProcessError as cpe:
        # error handling
        logger.error('RetroArcher Download Helper :: Error during extraction of 7z installer %s' % (installer_path))
        logger.error('RetroArcher Download Helper :: Called Process Error: %s' % (cpe))
        return False
    """

    destination_path = os.path.join(plexpy.CONFIG.RESOURCE_DIR, '7zip')
    merged = merge_update(temp_path, destination_path)

    return merged


def download_file(url, save_dir):
    logger.debug("RetroArcher Download Helper :: Download started for %s" % (url))
    try:
        response = requests.get(url, stream=True)
    except requests.RequestException as e:
        logger.error("RetroArcher Download Helper :: Download error: %s" % (e))
        return False

    make_dir(save_dir)

    save_path = os.path.join(save_dir, url.rsplit('/')[-1])

    with open(save_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

    logger.debug("RetroArcher Download Helper :: Download finished for %s" % (url))

    return save_path


def extract_archive(archive_file, destination_folder):
    extension = archive_file.rsplit('.', 1)[-1].lower()

    if extension == 'zip':
        with zipfile.ZipFile(archive_file, 'r') as archive:
            root_folder = archive.getinfo()[0]
            archive.extractall(path=destination_folder)
    elif extension == '7z' or extension == 'exe':
        with py7zr.SevenZipFile(archive_file, 'r') as archive:
            root_folder = archive.getnames()[0]
            methods = archive.archiveinfo().method_names

            if 'bcj2' not in methods.lower():  # methods is a string... will actually have BCJ2*
                archive.extractall(path=destination_folder)

            else:
                if platform.system().lower() == 'windows':
                    logger.info("RetroArcher Download Helper :: Attempting to extract using 7z.exe")
                    seven_zip_dir = os.path.join(plexpy.CONFIG.RESOURCE_DIR, '7zip')
                    seven_zip_binary = os.path.join(seven_zip_dir, '7z')

                    sevenzip = True
                    if not os.path.isfile(f'{seven_zip_binary}.exe'):
                        logger.critical("RetroArcher Download Helper :: File not found %s" % (seven_zip_binary))
                        # sevenzip = download_7z()  # how to extract 7z installer (self extracting archive)?
                        return False

                    if sevenzip:
                        command_args = [seven_zip_binary, 'x', archive_file, f'-o{destination_folder}', '-aoa', '-bd', '-y']
                        try:
                            proc = subprocess.run(command_args, check=True)
                        except subprocess.CalledProcessError as cpe:
                            # error handling
                            logger.error('RetroArcher Download Helper :: Error during extraction of archive %s' % (archive_file))
                            logger.error('RetroArcher Download Helper :: Called Process Error: %s' % (cpe))
                            return False
                else:
                    logger.error("RetroArcher Download Helper :: Cannot extract file %s" % (archive_file))

    try:
        return root_folder
    except NameError:
        return False


def make_dir(directory):
    try:
        os.mkdir(directory, mode=0o777)
        logger.info('RetroArcher Download Helper :: Successfully created directory: %s' % (directory))
    except FileExistsError:
        pass
    except:
        logger.critical('RetroArcher Download Helper :: Failed to create directory %s' % (directory))


def merge_update(source_dir, destination_dir):
    error = []
    try:
        shutil.copytree(source_dir, destination_dir, dirs_exist_ok=True)
    except shutil.Error as e:
        error.append(1)
        logger.error("RetroArcher Download Helper :: Error merging update source %s into destination %s :: Error: %s"
                     % (source_dir, destination_dir, e))

    try:
        shutil.rmtree(source_dir)
    except shutil.Error as e:
        error.append(2)
        logger.error("RetroArcher Download Helper :: Error removing temp directory %s" % (source_dir))

    if 1 in error:
        return False
    else:
        return True
