import plexpy
from plexpy import common
from plexpy import helpers
import pygame
from PyQt6.QtMultimedia import QMediaDevices
from PyQt6.QtCore import QStringDecoder
from screeninfo import get_monitors
import subprocess

if common.PLATFORM == 'Windows':
    from win32api import EnumDisplayDevices
    import pywintypes

if helpers.is_tool('pacmd'):  # if pulseaudio is installed
    import pulsectl


def get_display_resolutions():
    """returns a list of available display resolutions on the default display"""
    display_resolutions = []

    pygame.display.init()
    pygame_display_resolutions = pygame.display.list_modes()

    for resolution in pygame_display_resolutions:
        temp_resolution = f'{resolution[0]}x{resolution[-1]}'
        if temp_resolution not in display_resolutions:
            display_resolutions.append(temp_resolution)

    return display_resolutions


def get_checked_resolution(resolution):
    """return 'Checked' if resolution is in allowed resolutions config option"""
    if resolution in plexpy.CONFIG.SUNSHINE_ALLOWED_RESOLUTIONS.replace('"', '').split(','):
        return 'Checked'
    else:
        return ''


def get_fps_modes():
    """returns a list of available display resolutions on the default display"""
    modes = ['10', '30', '60', '90', '120']

    return modes


def get_checked_fps(fps):
    """return 'Checked' if fps is in allowed fps config option"""
    if fps in plexpy.CONFIG.SUNSHINE_ALLOWED_FPS.replace('"', '').split(','):
        return 'Checked'
    else:
        return ''


def get_monitor_devices():
    """returns a dictionary of monitor devices"""

    device_map = {}

    if common.PLATFORM == 'Windows':
        x = 0
        while True:
            try:
                adapter = EnumDisplayDevices(DevNum=x)
            except pywintypes.error:
                break

            try:
                monitor = EnumDisplayDevices(Device=adapter.DeviceName)
            except pywintypes.error:
                x += 1
                continue

            device_map[x] = {
                'adapter_name': adapter.DeviceString,
                'output_name': adapter.DeviceName,
                'monitor_name': monitor.DeviceString
            }

            x += 1

    else:  # need to verify for non windows OS
        devices = get_monitors()

        x = 1
        for device in devices:
            index = x

            if device.is_primary:
                index = 0

            device_map[index] = {
                'adapter_name': str(device),
                'output_name': str(index),
                'monitor_name': device.name
            }
            if index != 0:
                x += 1

    return device_map


def get_sound_devices():
    """returns a dictionary of audio devices"""
    device_map = {}

    if helpers.is_tool('pacmd'):  # if pulseaudio is installed
        pulse = pulsectl.Pulse()
        devices = pulse.sink_list()

        x = 0
        for device in devices:
            index = x

            device_map[index] = {
                'description': device.description,
                'id': device.name
            }

            x += 1

    else:
        devices = QMediaDevices.audioOutputs()
        default_device = QMediaDevices.defaultAudioOutput()

        x = 1
        for device in devices:
            index = x

            if device == default_device:
                index = 0

            device_map[index] = {
                'description': device.description(),
                'id': convert_qt_bytes(device.id())
            }
            if index != 0:
                x += 1

    return device_map


def get_vaapi_devices():
    """returns a dictionary of va-api capable devices"""
    if common.PLATFORM != 'Linux':
        return False

    command = 'vainfo'

    if not helpers.is_tool(command):  # if vainfo is not installed
        return False
    else:
        proc = subprocess.Popen([command], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result = proc.communicate()
        returncode = proc.returncode

        if returncode != 0:
            return {
                'error': result[-1].decode(),
                'returncode': returncode
            }

    device_map = {'error': None}

    return device_map


def convert_qt_bytes(byte_array):
    to_utf_16 = QStringDecoder('Utf8')

    return to_utf_16(byte_array)
