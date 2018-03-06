import argparse
import logging
import os
import re
import sys
import traceback

import asys

global logger
logger = logging.getLogger('filecounter')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.DEBUG)

#@Author: John Gooch
#@Created: 20120530
#@Updated: 20150410
version = "1.5"
#@Name: File counter
#@Description: Counts the number of files in the specified directory , prints and optionally stored count in a gv
#@1.5 20150410 - Added -e error flag handling .
#@1.4 20140502 - Logging and moved common functions into asys module.
#@1.3 Import asys module to fix callproc errors
#@1.2 Fixed a ton of errors. Added -e switch. Added exceptions instead of return codes

#parse the command line
def initCLI():
	parser = argparse.ArgumentParser(description='File Counter utility')
	parser.add_argument('-v', '--version', action='version', version='%(prog)s {version}'.format( version=version ) )
	parser.add_argument('-s', action="store", dest="src_dir_path", required=False, default=".",help='Path to the files to count.,')
	parser.add_argument('-m', action="store", dest="src_file_mask", required=False, default=".*", help='File name mask for files to count.')
	parser.add_argument( '-l', action="store", dest="level", default="INFO", required=False, help="Sets the logging level for the script. Default is INFO" )
	parser.add_argument( '-g', action="store", dest="gv", required=False, help="Specify the global variable to store the count in." )
	parser.add_argument( '-e', action="store_true", dest="error", required=False, default=False, help="Error flag. Return exit code 1 if file count is zero." )

	try:
		args = parser.parse_args()
		return args
	except Exception, error:
		print "Failed to parse the command line arguments. Reason: %s" % ( error )
		raise

def initLogging( logger, level):
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
	else:
		print "Invalid logging level - %s - specified. Please check your syntax."
		return None
	return

def countFiles( src_dir_path, mask ):
	file_count = 0
	src_dir_path = os.path.realpath( src_dir_path )
	if os.path.exists( src_dir_path ) == False:
		raise Exception( "Source file path %s does not exist or is not accessible." % ( src_dir_path ) )
	os.chdir( src_dir_path )
	for file in ([name for name in os.listdir('.') if os.path.isfile(name)]):
		if re.match( mask , file, re.I ):
			file_count += 1
	return file_count

	
def main():
	global args
	try:
		args = initCLI()
	except Exception, err:
		logger.error( "Failed to parse command line. Reason: %s" % ( str(err) ) )
		traceback.print_exc(file=sys.stdout)
		return 2
	try:
		initLogging(logger, args.level)
	except Exception, err:	
		logger.error( "Failed to initialize logging. Reason: %s" %  ( str(err) ) )
		traceback.print_exc(file=sys.stdout)
		return 2

	try:
		file_count = countFiles( args.src_dir_path, args.src_file_mask )
	except Exception, err:
		logger.error( "Failed to count files with pattern %s in folder %s. Reason: %s" %(  args.src_file_mask, args.src_dir_path, str(err) ) ) 
		traceback.print_exc(file=sys.stdout)
		return 2
	try:
		if args.gv:
			asys.setGV(args.gv, file_count)
		logger.info( "%d files in %s matched file name pattern %s" % ( file_count, args.src_dir_path, args.src_file_mask ) ) 
		if args.error:
			if file_count == 0:
				return 1
		else:
			return 0
	except Exception, err:
		logger.error( "Failed to set global variable %s to value %s"  % ( args.gv , file_count) )
		traceback.print_exc(file=sys.stdout )
		return 2
	#return exit code 1 if no files were found and the error flag is set to true
	if error and file_count == 0:
		return 1
	else:	
		return 0

if __name__ == "__main__":
	sys.exit(main())