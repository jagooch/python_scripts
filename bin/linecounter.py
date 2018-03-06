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
import subprocess

#@Author: John Gooch
#@Created: 20120829
#@Updated:
#@Version: 1.0
#@Name: Line Counter
#@Description: Reads the number of non-empty lines in a file and prints the count.

def initCLI():
	parser = argparse.ArgumentParser(description='File Zip utility')
	parser.add_argument('--version', action='version', version='%(prog)s 1.0')


	parser.add_argument('-s', action="store", dest="src_file_path", required=True, help='path to the files to include in the zip file.,')
	parser.add_argument('-g', action="store", dest="globalvar", default=False, help='Flatten the filesystem, so do not store the path in the filename. Turn on debugging messages')
	parser.add_argument( '-l', action="store", dest="level", default="INFO", required=False, help="Sets the logging level for the script. Default is INFO")
	try:
		args = parser.parse_args()
		return args
	except Exception, error:
		print "Failed to parse the command line arguments. Reason: %s" % ( error )
		return None

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
		
	
def setGV(gvar, value ):
	cmd = ["sendevent", "-E", "SET_GLOBAL", "-G", "%s=%s" % ( gvar,value )  ]
	logger.debug( "Executing command %s." %  ( " ".join( cmd ) ) )
	returncode = subprocess.call( cmd, shell=True ) 
	if returncode != 0:
		logger.error("Failed to execute command %s. Exit Code: %d."  % ( " ".join( cmd ), returncode ) )
		return 1
	else:
		logger.info("Successfully executed command %s with exit code %d" %  ( " ".join( cmd ), returncode ) )
		return 0
	return 0
	
	
def countlines( src_file_path, global_variable=None ):
	line_count = 0
	if os.path.exists(src_file_path) == False:
		logger.error( "Cannot access file %s. Please check path and permissions." %  ( src_file_path  ))
	try:
		f = open( src_file_path, 'r' )
		while ( 1 ):
			line = f.readline().strip()
			if not line:
				break
			else:	
				line_count = line_count + 1
	except Exception, err:
		logger.error( "Error reading file %s. Reason: %s" % ( src_file_path, str(err)  ) )
		return 1
	print line_count
	if global_variable:
		return setGV( global_variable , line_count )
	
	return 0
		

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
	return countlines( args.src_file_path, args.globalvar)


if __name__ == "__main__":
	sys.exit(main());