# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from io import open

import os

import plexpy
if plexpy.PYTHON2:
    import helpers
    import logger
else:
    from plexpy import helpers
    from plexpy import logger


def get_log_tail(window=20, parsed=True, log_type="server"):

    if plexpy.CONFIG.PMS_LOGS_FOLDER:
        log_file = ""
        if log_type == "server":
            log_file = os.path.join(plexpy.CONFIG.PMS_LOGS_FOLDER, 'Plex Media Server.log')
        elif log_type == "scanner":
            log_file = os.path.join(plexpy.CONFIG.PMS_LOGS_FOLDER, 'Plex Media Scanner.log')
    else:
        return []

    try:
        logfile = open(log_file, "r", encoding="utf-8")
    except IOError as e:
        logger.error('Unable to open Plex Log file. %s' % e)
        return []

    log_lines = tail(logfile, window)

    if parsed:
        line_error = False
        clean_lines = []
        for i in log_lines:
            try:
                log_time = i.split(' [')[0]
                log_level = i.split('] ', 1)[1].split(' - ', 1)[0]
                log_msg = i.split('] ', 1)[1].split(' - ', 1)[1]
                full_line = [log_time, log_level, log_msg]
                clean_lines.append(full_line)
            except:
                line_error = True
                full_line = ['', '', 'Unable to parse log line.']
                clean_lines.append(full_line)

        if line_error:
            logger.error('RetroArcher was unable to parse some lines of the Plex Media Server log.')

        return clean_lines
    else:
        raw_lines = []
        for i in log_lines:
            raw_lines.append(helpers.latinToAscii(i))

        return raw_lines

    return log_lines

# http://stackoverflow.com/a/13790289/2405162
def tail(f, lines=1, _buffer=4098):
    """Tail a file and get X lines from the end"""
    # place holder for the lines found
    lines_found = []

    # block counter will be multiplied by buffer
    # to get the block size from the end
    block_counter = -1

    # loop until we find X lines
    while len(lines_found) < lines:
        try:
            f.seek(block_counter * _buffer, os.SEEK_END)
        except IOError:  # either file is too small, or too many lines requested
            f.seek(0)
            lines_found = f.readlines()
            break

        lines_found = f.readlines()

        # we found enough lines, get out
        if len(lines_found) > lines:
            break

        # decrement the block counter to get the
        # next X bytes
        block_counter -= 1

    return lines_found[-lines:]