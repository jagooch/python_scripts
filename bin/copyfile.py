import argparse
import logging
import os
import shutil
import sys
import traceback
from datetime import datetime

import asys

global logger
logger = logging.getLogger('copyfile')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.DEBUG)

#@Author: John Gooch
#@Created: 20120618
#@Updated: 20140502
version = "2.4"
#
#@Name: File copy Script
#@Description: Copies file(s) from one folder to another, optionally adding a timestamp.
#@2.4 20140403 - Logging and moved common functions into asys module.
#@2.3 20140403 - Fixed zero files with -e switch error reporting.
#@2.2 20140326 - Added prepend switch to enable timestamp at beginning of file. Modified append to be at end of file.
#@2.1 20131121 - removed references to zipfile and zlib
#@2.0 20130711 - Added the -T switch to specify the delete mode ( eg NEWEST, OLDEST, ALL ). updated findFiles and move files functions
#v1.3 20130403 changed does match to does not match, removed invalid check for false on re.match. removed duplicate copying messages. added "successfully copied output"
#Add -f parameter for formatting the timestamp
#v1.2 20121215 
#changed does match to does not match, removed invalid check for false on re.match. removed duplicate copying messages. added "successfully copied output"


def initCLI():
	parser = argparse.ArgumentParser(description='File Copy utility')
	parser.add_argument('-v', '--version', action='version', version='%(prog)s {version}'.format( version=version ) )
	parser.add_argument('-s', action="store", dest="src_dir_path", required=True, help='path of the files to move.')
	parser.add_argument('-d', action="store", dest="dst_dir_path", required=True, help='path of the folder to move files to')
	parser.add_argument('-m', action="store", dest="mask", required=True, help='File name mask for files to include in the zip file. Default is .*')
	parser.add_argument('-t', action="store_true", dest="timestamp", help='Flag to append current data and time to file name between basename and extension.')
	parser.add_argument('-e', action="store_true", dest="error", default=False, help='Flag to throw an error if no files are copied. Default is off ie no error.')
	parser.add_argument('-p', action="store_true", dest="prepend", default=False, help='Prepend timestamp to source file name.')
	parser.add_argument('-T', action="store", dest="type", required=False, default="ALL", help='Specifies processing mode for files. Default is ALL. Other options are OLDEST(single), NEWEST(single)')
	parser.add_argument('-f', action="store", dest="format", default="%Y%m%d", required=False, help='Format for timestamp, if timestamp is enabled.')
	parser.add_argument('-o', action="store_true", dest="overwrite", default=False, required=False, help="Enable overwriting files of the same name. Default is off." )
	parser.add_argument('-g', action="store", dest="global_variable", default=False, required=False, help="Global variable name to store number of files copied." )
	parser.add_argument('-l', action="store", dest="level", default="INFO", required=False, help="Sets the logging level for the script. Default is INFO" )

	try:
		args = parser.parse_args()
		return args
	except Exception, error:
		print "Failed to parse the command line arguments. Reason: %s" % ( str(error) )
		raise

def initLogging( level):
	if level is None:
		raise Exception( "level not initialized.") 
	elif ( level == "DEBUG" ):
		logger.setLevel( logging.DEBUG )
		logging.getLogger("asys").setLevel(logging.DEBUG)
	elif ( level == "INFO" ):
		logger.setLevel( logging.INFO )
		logging.getLogger("asys").setLevel(logging.INFO)
	elif ( level == "WARNING" ):
		logger.setLevel( logging.WARNING )
		logging.getLogger("asys").setLevel(logging.WARNING)
	elif ( level == "ERROR" ):
		logger.setLevel( logging.ERROR )
		logging.getLogger("asys").setLevel(logging.ERROR)
	elif ( level == "CRITICAL" ):
		logger.setLevel( logging.CRITICAL )
		logging.getLogger("asys").setLevel(logging.CRITICAL)
	else:
		raise Exception( "Invalid logging level %s specified." % ( level ) ) 
	return




def copyFiles( src_path, files, dst_path, timestamp, format, error, overwrite, global_variable, prepend ):
	copied_files = []
	src_dir_path = os.path.realpath( src_path )
	dst_dir_path = os.path.realpath( dst_path )
	if os.path.exists(src_dir_path) == False:
		logger.error( "Source path is %s not accessible. Check path and permissions." % ( src_dir_path ) )
		raise Exception( "Source path is %s not accessible. Check path and permissions." % ( src_dir_path ) )
	if os.path.exists(dst_dir_path) == False:
		logger.error( "Destination path is %s not accessible. Check path and permissions." % ( dst_dir_path ) )
		raise Exception( "Destination path is %s not accessible. Check path and permissions." % ( dst_dir_path ) )

	logger.debug( "Copying %s files from %s to %s" % ( len(files), src_dir_path, dst_dir_path ) )  
	for file_name in files:
		src_file_path = os.path.join( src_dir_path, file_name )
		if os.path.isfile(src_file_path) == False:
			logger.debug( "%s is not a regular file. Skipping." % ( src_file_path ) )
			continue
		else:
			dst_filename = file_name
			if timestamp:
				( first_part, extension ) = os.path.splitext(dst_filename)
				logger.debug("%s split into basename %s and extension %s" % ( dst_filename, first_part, extension )  )
				current_time = getTimestamp(format)
				if prepend:
					dst_filename = "%s%s%s" % ( current_time,first_part, extension )
				else:
					dst_filename = "%s%s%s" % ( first_part, extension, current_time )
			dst_file_path = os.path.join( dst_path, dst_filename )
			if os.path.exists( dst_file_path ):
				if not overwrite:
					logger.info( "Destination file %s already exists and overwriting is disabled. Skipping file."  % ( dst_file_path  )  )
					continue
				else:
					logger.info( "Destination file %s already exists and overwriting is enabled. Overwriting existing file."  % ( dst_file_path  )  )
			logger.debug( "Copying file %s to %s" % ( src_file_path, dst_file_path ) ) 
			try:
				shutil.copy2(  src_file_path, dst_file_path ) 
				logger.info( "Copied file %s to %s" % ( src_file_path, dst_file_path ) ) 
				copied_files.append( file_name )
			except Exception, err:
				logger.error( "Failed to copy file %s to %s. Reason: %s" % ( src_file_path, dst_file_path, err ) )
				raise
	return copied_files
	
def getTimestamp(format):
	now = datetime.now()
	current_time= now.strftime(format)
	return current_time
		
		
def main():
	global args
	files = []
	copied_files = None
	try:
		args = initCLI()
	except Exception, err:
		print "Exception encountered while parsing command line arguments. Reason: %s" % ( str(err) )
		traceback.print_exc()
		return 2

	try:
		initLogging( args.level)
	except Exception, err:
		print "Exception encountered while initializing the logging facility. Reason: %s" % ( str(err) )
		traceback.print_exc()
		return 2

	try:
		if args.type in "ALL":
			files = asys.findFiles(args.src_dir_path, args.mask, -1)
		elif args.type in "OLDEST":
			files = asys.findFiles(args.src_dir_path, args.mask, 0)
		elif args.type in "NEWEST":
			files = asys.findFiles(args.src_dir_path, args.mask, 1)
		else:
			logger.error( "Exception. Operation type %s not recognized." % ( type ) )
			return 2
	except Exception, err:
		logger.error( "Exception finding files in %s. Reason: %s." % ( args.src_dir_path, str(err) ) )
		traceback.print_exc()
		return 2
	
	try:
		copied_files = copyFiles( args.src_dir_path, files, args.dst_dir_path, args.timestamp, args.format, args.error, args.overwrite,args.global_variable, args.prepend )
	except Exception, err:
		logger.error( "Exception encountered while copying files. Reason: %s" % ( str(err) ) )
		traceback.print_exc()
		return 2

	try:	
		if args.global_variable:
			asys.setGV(global_variable, len(copied_files))
	except Exception, err:
		logger.error( "Exception encountered setting global variable.Reason: %s" % ( str(err) ) )
		traceback.print_exc()
		return 2
			
			
	if len(copied_files) == 0 and args.error:
		logger.error( "Error: %d files were copied from \"%s\" to \"%s\". and error flag was set." % ( len(copied_files), os.path.realpath( args.src_dir_path ), os.path.realpath( args.dst_dir_path ) ) )
		return 1
	else:
		for file in copied_files:
			logger.info( "%s was successfully copied from \"%s\" to \"%s\"."  % ( file, os.path.realpath( args.src_dir_path ), os.path.realpath( args.dst_dir_path ) ) )
		logger.info( "%d files were copied from \"%s\" to \"%s\"." % ( len(copied_files), os.path.realpath( args.src_dir_path ), os.path.realpath( args.dst_dir_path ) ) )
		return 0
		
if __name__ == "__main__":
	sys.exit(main())