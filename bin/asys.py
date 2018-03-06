# move_asys
from datetime import datetime
import argparse
import glob
import logging
import os
import re
import subprocess
import sys
import time
import time
import traceback

global logger
logger = logging.getLogger("asys")
# logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.DEBUG)

# @Author: John Gooch
# @Created: 20140422
# @Updated: 20140430
version = "1.2"


# 1.2 20140619 Added fileLockCheck
# 1.1 20140403 created
# @Name: Autosys Function module
# @Description: Module of commonly used functions for the autosys package.

# returns connection to Oracle database session
def oraConn(db_alias, db_user, db_pwd):
    logger.debug("Connecting to database alias %s as %s." % (db_alias, db_user))
    conn = cx_Oracle.connect("%s/%s@%s" % (db_user, db_pwd, db_alias))
    logger.debug("Successfully connected to database alias %s as %s." % (db_alias, db_user))
    return conn


# select and returns matching records from oracle database
def oraSelect(conn, sql):
    rows = []
    curs = None
    fields = None
    curs = conn.cursor()  # get reference to the cursor
    logger.debug("Executing select statement %s" % (sql))
    curs.execute(sql)
    logger.debug("%d rows returned." % (curs.rowcount))
    records = curs.fetchall()
    curs.close()
    return records


# returns the path to the newest or oldest file in a folder that matches the search mask. Returns None if no files are found matching the file name mask
def findFile(src_dir_path, mask, sort_order):
    logger.debug("Watching directory %s for file name matching %s" % (src_dir_path, mask))

    try:
        os.chdir(src_dir_path)
    except Exception as err:
        logger.error("Failed to change directory to %s." % (src_dir_path))
        raise

    files = glob.glob("*")
    if not files:
        logger.info("No files found in directory %s." % (src_dir_path))
        return None
    selected_file = None
    selected_time = None
    src_file_path = None
    for filename in files:
        src_file_path = os.path.join(src_dir_path, filename)
        if not os.path.isfile(src_file_path):
            continue
        elif not re.match(mask, filename, re.I):
            logger.debug("File %s name does not match file mask %s" % (filename, mask))
            continue
        else:
            logger.debug(
                "Processing Filename is %s . File path is %s." % (filename, os.path.join(src_dir_path, filename)))
            mtime = os.path.getmtime(src_file_path)
            mtime_string = datetime.strftime(datetime.fromtimestamp(mtime), "%Y%m%d %H%M%S")
            if selected_time == None:
                selected_time = mtime
                selected_file = src_file_path
                logger.debug("Selected file set to %s . Selected modified time: %s." % (src_file_path, mtime_string))
            # sort oldest modification time first
            elif sort_order == 0:
                if selected_time >= mtime:
                    selected_time = mtime
                    selected_file = src_file_path
                    logger.debug(
                        "Selected file set to %s . Selected modified time: %s." % (src_file_path, mtime_string))
            # sort newest modification time first
            elif sort_order == 1:
                if selected_time <= mtime:
                    selected_time = mtime
                    selected_file = src_file_path
                    logger.debug(
                        "Selected file set to %s . Selected modified time: %s." % (src_file_path, mtime_string))
            else:
                logger.error("Sort order %d not recognized. Please check syntax." % (sort_order))
                raise Exception("Invalid sort order value exception.")
    if not selected_file:
        logger.info("No file matching %s\%s found." % (src_dir_path, mask))
        return None
    else:
        logger.info("File %s matching %s\%s found." % (selected_file, src_dir_path, mask))
        # , mtime_string - modified time string
        return selected_file


def fileLockCheck(file_path, interval, retry_limit):
    retry_counter = 0
    while True:
        try:
            with open(file_path, 'a') as f:
                logger.debug("lockcheck: %s is not locked." % (file_path))
                return
        except Exception as err:
            logger.debug("lockcheck: File %s is locked. Waiting for release. Reason: %s" % (file_path, str(err)))
            traceback.print_exc()
            pass
        time.sleep(interval)
        retry_counter += 1
        if retry_counter > retry_limit:
            raise Exception("FileLockedException: File %s is locked by another process." % (file_path))
    return


def findFiles(src_dir_path, mask, mode=-1, negativelogic=False):
    # mode -1 return all matching files, 0 return oldest matching file , 1 return newest matching file
    matching_files = []
    logger.debug("Searching directory %s for file names matching %s" % (src_dir_path, mask))
    src_dir_path = os.path.realpath(src_dir_path)
    if not os.path.exists(src_dir_path):
        raise Exception("Cannot access source directory %s. Check path and permissions." % (src_dir_path))
    files = os.listdir(src_dir_path)
    if not files:
        logger.debug("No files found in directory %s." % (src_dir_path))
        return matching_files
    selected_file = None
    selected_time = None
    src_file_path = None
    for filename in files:
        src_file_path = os.path.join(src_dir_path, filename)
        if not os.path.isfile(src_file_path):
            continue
        elif not negativelogic and not re.match(mask, filename, re.I):
            logger.debug("File %s name does not match file mask %s and positive logic is enabled." % (filename, mask))
            continue
        elif negativelogic and re.match(mask, filename, re.I):
            logger.debug("File %s name does matches file mask %s and negative logic is enabled." % (filename, mask))
            continue
        else:
            if mode == -1:
                matching_files.append(filename)
            else:
                logger.debug("Check mtime for file is %s . File path is %s." % (filename, src_file_path))
                mtime = os.path.getmtime(src_file_path)
                mtime_string = datetime.strftime(datetime.fromtimestamp(mtime), "%Y%m%d %H%M%S")
                if selected_time == None:
                    selected_time = mtime
                    selected_file = filename
                    logger.debug(
                        "Selected file set to %s . Selected modified time: %s." % (src_file_path, mtime_string))
                # sort oldest modification time first
                elif mode == 0:
                    if selected_time >= mtime:
                        selected_time = mtime
                        selected_file = filename
                        logger.debug(
                            "Selected file set to %s . Selected modified time: %s." % (src_file_path, mtime_string))
                # sort newest modification time first
                elif mode == 1:
                    if selected_time <= mtime:
                        selected_time = mtime
                        selected_file = filename
                        logger.debug(
                            "Selected file set to %s . Selected modified time: %s." % (src_file_path, mtime_string))
                else:
                    logger.error("Sort order %d not recognized. Please check syntax." % (mode))
                    raise Exception("Invalid sort order value exception.")
    if mode == -1:
        return matching_files
    elif not selected_file:
        logger.debug("Did not find any file names matching %s in folder." % (mask, src_dir_path))
        return matching_files
    else:
        matching_files.append(selected_file)
        return matching_files


def findFiles2(src_dir_path, include=".*", exclude="a^", recursive=True):
    file_list = []
    logger.debug(
        "Searching directory %s for file names matching %s and not matching %s." % (src_dir_path, include, exclude))
    for directory, subdirectories, files in os.walk(src_dir_path, topdown=False):
        dir_path = os.path.realpath(directory)
        if not recursive:
            subdirectories[:]
        logger.debug("Processing directory %s" % dir_path)
        for file in files:
            file_path = os.path.join(dir_path, file)
            if re.match(include, file, re.I) and not re.match(exclude, file, re.I):
                # add the full file path to the file list
                file_list.append(file_path)
                logger.debug("File %s added to list." % (file_path))
        logger.debug("%s processed.\n\n" % directory)
    return file_list


# Converts text file size to float integer - input format ddddu where d is digits and u is unites (m or g or none )
def getBytes(size):
    # logger.debug( "Size paramater is %s" % ( size ) )
    bytes = None
    matches = re.match("(\d+)([a-zA-Z]?)", size)
    # logger.debug( "%s matches found for size %s" % ( matches.groups(), size ) )
    if not matches:
        # logger.debug( "Size parameter %s does not match the expected input pattern. Matches:%s " % ( size, matches ) )
        raise Exception("invalid size format %s." % (size))
    # logger.debug( "%d matches found is size string %s" % ( len(matches.groups()), size ) )
    digits = matches.group(1)
    units = matches.group(2)
    if not units:
        bytes = int(digits)
    elif units in 'b':
        bytes = int(digits)
    elif units in 'k':
        bytes = int(digits) * 1024
    elif units in 'm':
        bytes = int(digits) * 1048576
    elif units in 'g':
        bytes = int(digits) * 1073741824
    else:
        raise Exception("Invalid size format %s." % (size))
    # logger.debug( "Units is %s, bytes is %d" % ( units, bytes ))
    return bytes


def getSeconds(seconds_string):
    seconds = 0
    try:
        int(seconds_string)
        return int(seconds_string)
    except:
        pass
    matches = re.match('(\d+)([A-Za-z])', seconds_string)
    if matches:
        number = int(matches.group(1))
        units = matches.group(2)
        # logger.debug( "numbers is %d. units is %s" % ( number, units ) )
        if units.upper() in "S":
            seconds = number
        elif units.upper() in "M":
            seconds = number * 60
        elif units.upper() in "H":
            seconds = number * 60 * 60
        elif units.upper() in "D":
            seconds = number * 60 * 60 * 24
        elif units.upper() in "W":
            seconds = number * 60 * 60 * 24 * 7
        else:
            raise Exception("Exception: Invalid units %s." % (units))
        return seconds
    else:
        raise Exception("Exception. Unrecognised time format.")


def main():
    return 0


if __name__ == "__main__":
    sys.exit(main())
