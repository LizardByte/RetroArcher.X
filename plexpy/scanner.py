import os

import plexpy
from plexpy import logger


def scan():
    rom_folder = plexpy.CONFIG.ROM_DIR

    logger.debug("RetroArcher Scanner :: Scan Task Initiated")
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
