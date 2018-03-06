import argparse
import datetime
import logging
import os
import shutil
import sys
import traceback
import asys

global version
global logger

logger = logging.getLogger('movefile')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

# @Author: John Gooch
# @Created: 20120613
# @Updated: 20130911
version = "3.4"


# @Name: File Move Script
# @Description: Move file(s) from one folder to another, optionally adding a timestamp or throwing an error if no files are moved.
# 20120904 - Added "-o" overwrite switch to permit overwriting existing files of the same name/path as the source.
# 2.3 20121231 File output file name when timestamp is used. replaced string join with os.path.join when creating file paths.
# 2.4 20130106
# Fixed spelling errors in output messages..
# 2.5 20130404
# Replaced exit codes for failurs with exceptions. replaced os.rename with shutil.move , added timestamp formatting option
# 3.0 20130710
# Added Type option to specify special single file processing modes, such as NEWEST, OLDEST, etc. added findfiles to create list
# of files to move, and removed file selection logic from the movefiles function
# 3.1 20130904
# Added -n negative logic to tell the script to move files that do not match the pattern.
# 3.2 20130906
# Remove local setGV function and replaced it with one imported from asys module. move error checking and setgv to top of main function from movefile
# 3.3 20140326 #added prepend function and changed location of appended timestamp
# @3.4 20140502 - Logging and moved common functions into asys module.

def initCLI():
    parser = argparse.ArgumentParser(description='File Move utility')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s {version}'.format(version=version))
    parser.add_argument('-s', action="store", dest="src_file_path", required=True, help='path of the files to move.')
    parser.add_argument('-d', action="store", dest="dst_file_path", required=True,
                        help='path of the folder to move files to')
    parser.add_argument('-m', action="store", dest="src_file_mask", required=True,
                        help='File name mask for files to move.')
    parser.add_argument('-l', action="store", dest="level", default="INFO", required=False,
                        help="Sets the logging level for the script. Default is INFO")
    parser.add_argument('-o', action="store_true", dest="overwrite", required=False, default=False,
                        help="Cause existing file of the same name/path to be overwritten.")
    parser.add_argument('-t', action="store_true", dest="timestamp", required=False, default=False,
                        help='Flag to append current data and time to file name')
    parser.add_argument('-T', action="store", dest="type", required=False, default="ALL",
                        help='Specifies processing mode for files. Default is ALL. Other options are OLDEST(single) NEWEST(single)')
    parser.add_argument('-e', action="store_true", dest="error", required=False, default=False,
                        help='Flag to throw an error if no files are moved.')
    parser.add_argument('-f', action="store", dest="format", default="%Y%m%d", required=False,
                        help='Format for timestamp, if timestamp is enabled.')
    parser.add_argument('-n', action="store_true", dest="negativelogic", default=False, required=False,
                        help='Work on filenames that do not match pattern.')
    parser.add_argument('-p', action="store_true", dest="prepend", default=False,
                        help='Prepend timestamp to source file name.')
    args = parser.parse_args()
    return args


def initLogging(level):
    if not level:
        logger.setLevel(logging.WARNING)
    elif (level == "DEBUG"):
        logger.setLevel(logging.DEBUG)
    elif (level == "INFO"):
        logger.setLevel(logging.INFO)
    elif (level == "WARNING"):
        logger.setLevel(logging.WARNING)
    elif (level == "ERROR"):
        logger.setLevel(logging.ERROR)
    elif (level == "CRITICAL"):
        logger.setLevel(logging.CRITICAL)
    else:
        raise Exception("Exception setting logging level. Unrecognised level %s was specified" % (level))
    return


def moveFiles(src_path, files, dst_path, timestamp, error, overwrite, format, prepend):
    logger.debug("original src_path=%s" % (src_path))
    logger.debug("original dst_path=%s" % (dst_path))
    moved_files = []  # list of source files moved
    skipped_files = []
    src_path = os.path.realpath(src_path)
    dst_path = os.path.realpath(dst_path)
    logger.debug("real src_path=%s" % (src_path))
    logger.debug("real dst_path=%s" % (dst_path))
    if os.path.exists(src_path) == False:
        logger.error("Source path %s is not accessible. Check path and permissions." % (src_path))
        raise Exception("Source path %s is not accessible. Check path and permissions." % (src_path))
    else:
        logger.debug("Source path %s exists." % (src_path))

    if os.path.exists(dst_path) == False:
        logger.error("Destination path %s is not accessible. Check path and permissions." % (dst_path))
        raise Exception("Destination path %s is not accessible. Check path and permissions." % (dst_path))
    else:
        logger.debug("Destination path %s exists." % (dst_path))
    logger.debug("Current working directory is %s" % (os.getcwd()))
    logger.debug("Found %s files in %s " % (len(files), src_path))
    for file in files:
        src_file_path = os.path.join(src_path, file)
        # if os.path.isfile(src_file_path) == False:
        # logger.debug( "%s is not a regular file. Skipping." % ( src_file_path ) )
        # continue
        dst_filename = file
        if timestamp == True:
            (first_part, extension) = os.path.splitext(dst_filename)
            logger.debug("Result of splitext command on filename %s is basename %s extension %s" % (
            dst_filename, first_part, extension))
            current_time = getTimestamp(format)
            if prepend:
                dst_filename = "%s%s%s" % (current_time, first_part, extension)
            else:
                dst_filename = "%s%s%s" % (first_part, extension, current_time)
        dst_file_path = os.path.join(dst_path, dst_filename)
        # if a file with the same name exists at the destination and overwrite is disabled, skip file
        if os.path.exists(dst_file_path) and not overwrite:
            logger.debug("Destination file %s already exists and overwrite is disabled. Skipping..." % (dst_file_path))
            skipped_files.append(src_file_path)
            continue
        elif os.path.exists(dst_file_path) and overwrite:
            logger.debug("Overwriting destination file %s." % (dst_file_path))
        # move the file
        try:
            shutil.move(src_file_path, dst_file_path)
            logger.debug("Moved %s to %s" % (src_file_path, dst_file_path))
            moved_files.append(src_file_path)
        except Exception:
            logger.error("Failed to moved file %s to %s" % (src_file_path, dst_file_path))
            raise

    return (moved_files, skipped_files)


def getTimestamp(format):
    now = datetime.datetime.now()
    current_time = now.strftime(format)
    return current_time


def printReport(moved_files, skipped_files, dst_dir_path):
    dst_dir_path = os.path.realpath(dst_dir_path)
    logger.info("%d files moved to %s" % (len(moved_files), dst_dir_path))
    for file in moved_files:
        logger.info("%s moved to %s" % (file, dst_dir_path))
    logger.info("%d files skipped." % (len(skipped_files)))
    for file in skipped_files:
        logger.info("%s skipped." % (file))

    return 0


def main():
    global logger
    global moved_files
    global skipped_files
    global files
    global args
    print("%s version %s".format(os.path.basename(sys.argv[0]), version))
    try:
        args = initCLI()
    except Exception as err:
        print("Failed to initialize the command line parameters. Reason %s".format(str(err)))
        traceback.print_exc()
        return 2
    try:
        initLogging(args.level)
    except Exception as err:
        print("Failed to initialize logger. Reason: %s".format(str(err)))
        traceback.print_exc()
        return 2

    try:
        if args.type in "ALL":
            files = asys.findFiles(args.src_file_path, args.src_file_mask, -1, args.negativelogic)
        elif args.type in "OLDEST":
            files = asys.findFiles(args.src_file_path, args.src_file_mask, 0, args.negativelogic)
        elif args.type in "NEWEST":
            files = asys.findFiles(args.src_file_path, args.src_file_mask, 1, args.negativelogic)
        else:
            logger.error("Exception. Operation type %s not recognized." % (type))
            return 2
    except Exception as err:
        logger.error("Exception finding files in %s. Reason: %s." % (args.src_file_path, str(err)))
        traceback.print_exc()
        return 2

    try:
        (moved_files, skipped_files) = moveFiles(args.src_file_path, files, args.dst_file_path, args.timestamp,
                                                 args.error, args.overwrite, args.format, args.prepend)
    except Exception as err:
        logger.error("Failed to move files matching pattern %s from %s to %s. Reason: %s" % (
        args.src_file_mask, args.src_file_path, args.dst_file_path, str(err)))
        traceback.print_exc()
        return 2


    try:
        printReport(moved_files, skipped_files, args.dst_file_path)
    except Exception as err:
        logger.error("Exception printing file move report. Reason: %s" % (str(err)))
        traceback.print_exc()
        return 2

    if args.error == True and len(moved_files) == 0:
        logger.info("%d files found and the error flag is set. Returning 0." % (len(moved_files)))
        return 1
    else:
        return 0


if __name__ == "__main__": main()
