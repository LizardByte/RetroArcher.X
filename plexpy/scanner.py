import os

import plexpy
from plexpy import logger


def scan():
    logger.debug("RetroArcher Scanner :: Scan Task Initiated")

    plexpy.emulators.update_mapping()  # update the platform to core mapping dictionary

    rom_folder = plexpy.CONFIG.ROM_DIR

    if os.path.isdir(rom_folder):
        logger.debug("RetroArcher Scanner :: Found rom folder %s" % (rom_folder))
        return True
    else:
        logger.error("RetroArcher Scanner :: Failed to find rom folder %s" % (rom_folder))
        return False


def generate():
    logger.debug("RetroArcher Scanner :: Generate Task Initiated")


def clean():
    logger.debug("RetroArcher Scanner :: Clean Task Initiated")
