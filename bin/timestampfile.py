import os
import zipfile
import sys
import argparse
import os
import glob
import zlib
import re
import logging
import ConfigParser
import glob
import datetime 
import time

#@Author: John Gooch
#@Created: 20120828
#@Updated:
#@Version: 1.0
#@Name: Timestamp File Utility
#@Description: Renames specified file with current date/timestamp

def initCLI():
	parser = argparse.ArgumentParser(description='Timestamp File Utiliy')
	parser.add_argument('--version', action='version', version='%(prog)s 1.0')
	parser.add_argument('-s', action="store", dest="src_file_path", required=True, help='Path to the target file to rename with timestamp.,')
	parser.add_argument( '-l', action="store", dest="level", default="INFO", required=False, help="Sets the logging level for the script. Default is INFO")

	try:
		args = parser.parse_args()
		return args
	except Exception, error:
		print "Failed to parse the command line arguments. Reason: %s" % ( error )
		return None

def timestampFile( src_file_path ):
	if os.path.exists(src_file_path) == False:
		logger.error( "Target file %s is not accessible. Please check path and permissions." % ( src_file_path )) 
		return 1
	src_file_name = os.path.basename( src_file_path)
	src_file_dir = os.path.dirname( src_file_path)
	dst_file_name = "%s-%s"  % ( src_file_name, time.strftime("%Y%m%d_%H%M%S" ) )
	dst_file_path = "/".join( [ src_file_dir, dst_file_name  ] )
	try:
		os.rename( src_file_path, dst_file_path )
	except Exception, err:
		logger.error("Failed to rename file %s to %s. Reason: %s." % ( src_file_path, dst_file_path, str(err)   ))
		return 1
	if os.path.exists( dst_file_path ):
		logger.debug( "successfully renamed file %s to %s." % ( src_file_path, dst_file_path    ) )
		return 0
	else:
		logger.error("Failed to rename file %s to %s. Reason: %s." % ( src_file_path, dst_file_path, str(err)   ))
		return 1
	return 0
def initLogging(args):
	logger = logging.getLogger()
	if args.level is False:
		logger.setLevel(logging.WARNING)
	elif ( args.level == "DEBUG" ):
		logger.setLevel( logging.DEBUG )
	elif ( args.level == "INFO" ):
		logger.setLevel( logging.INFO )
	elif ( args.level == "WARNING" ):
		logger.setLevel( logging.WARNING )
	elif ( args.level == "ERROR" ):
		logger.setLevel( logging.ERROR )
	elif ( args.level == "CRITICAL" ):
		logger.setLevel( logging.CRITICAL )
	formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
	ch = logging.StreamHandler()
	ch.setFormatter(formatter)
	logger.addHandler(ch)
	return logger
		
		
	
def main():
	global logger
	args = initCLI()
	if ( args is None ):
		print "Exiting..."
		return 1
	logger = initLogging(args)
	if logger is None:
		print "Failed to initialize logging.Quitting..."
		return 1;
	#conf = loadConfig(args.config_file_path)
	if timestampFile( args.src_file_path ) != 0:
		return 1
	return 0


if __name__ == "__main__":
	sys.exit(main());