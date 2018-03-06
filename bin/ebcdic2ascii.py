import argparse
import logging
import os
import sys
import traceback

import asys

version = "1.0"
#@Author: John Gooch
#@Created: 20140616
#@Updated: 
#@Name: File Tracking System capture file data script 
#@Description: Captures file names and other properties, and stores them in an Oracle DB table
#@ Tasks

global logger
logging.basicConfig()
logger = logging.getLogger('ebcdic2ascii')
logger.setLevel(logging.ERROR)


def initCLI():
	parser = argparse.ArgumentParser(description='EBCDIC to ASCII converter v1.0')
	parser.add_argument('-s', action="store", dest="src_dir_path", required=True, help="Source folder path for input ebcdic files.")
	parser.add_argument('-d', action="store", dest="dst_dir_path", required=True, help="Destination folder path for ascii files.")
	parser.add_argument('-m', action="store", dest="mask", required=False, default=".*", help="File name match pattern.")
	parser.add_argument( '-b', action="store", dest="buffer_size" , required=False, default=16384, type=int, help="Read Buffer size in bytes." )
	parser.add_argument( '-e', action="store_true", dest="error" , required=False, default=False, help="Set error flag." )
	parser.add_argument('--delete-original', action="store_true", dest="delete_original", required=False, default=False, help="Enable deletion of original file after conversion.")
	parser.add_argument('-l', action="store", dest="level", required=False, default="INFO", help="Logging level.")
	args = parser.parse_args()
	return vars(args)


def initLogging(level):
	levels = { 
		"DEBUG":logging.DEBUG, 
		"INFO" :logging.INFO,
		"WARNING":logging.WARNING,
		"ERROR":logging.ERROR ,
		"CRITICAL":logging.CRITICAL
	}
	logger.setLevel( levels[level.upper()] )
	return


def ebcdic2ascii( src_file_path , dst_file_path, buffer_size ):
	with open( dst_file_path, 'wb' ) as output_file:
		with open( src_file_path, 'r' ) as input_file:
			while True:
				buffer = input_file.read( buffer_size )
				if not buffer:
					break
				else:
					ansi = buffer.decode( 'ibm500' )
					ascii = ansi.encode( 'ascii','replace' )
					output_file.write( ascii )
	return

def main():
	mc = {}
	ebcdic_files = []
	processed_files = []
	deleted_files = []
	try:
		#append command line arguments to master configuration 
		mc.update( initCLI() )
	except argparse.ArgumentError, err:
		logger.error( "Invalid command line syntax. Reason: %s" % ( str(err) )  )
		traceback.print_exc()
		return 2
	except Exception, err:
		logger.error( "Failed to parse command line arguments. Reason: %s" % ( str(err) ) )
		traceback.print_exc()
		return 2
	
	try:
		initLogging( mc['level'])
	except Exception, err:
		logger.error( "Failed to initialize logging. Reason: %s" % ( str(err) ) )
		traceback.print_exc()
		return 2
	#normalize directory paths
	mc["src_dir_path"] = os.path.realpath( mc["src_dir_path"] )
	mc["dst_dir_path"] = os.path.realpath( mc["dst_dir_path"] )

	try:
		ebcdic_files.extend(asys.findFiles(mc["src_dir_path"], mc["mask"]))
	except Exception, err:
		logger.error( "Exception listing files in %s. Reason: %s" % ( mc["src_dir_path"], str(err) ) )
		traceback.print_exc()
		return 2

	try:
		for ebcdic_file in ebcdic_files:
			ebcdic_file_path = os.path.join( mc["src_dir_path"], ebcdic_file )
			ascii_file_name = ebcdic_file + ".ascii" 
			ascii_file_path = os.path.join( mc["dst_dir_path"], ascii_file_name ) 
			logger.info( "Converting %s from ebcdic to ascii." % ( ebcdic_file_path ) )
			ebcdic2ascii( ebcdic_file_path, ascii_file_path, mc["buffer_size"] )
			processed_files.append( ebcdic_file_path )
			logger.info( "%s converted from ebcdic to ascii." % ( ebcdic_file_path ) )
			if mc["delete_original"]:
				logger.info( "Original file deletion enabled." ) 
				os.remove( ebcdic_file )
				deleted_files.append( ebcdic_file ) 
				logger.info( "Original file %s deleted."  % ( ebcdic_file ))
			
	except Exception, err:
		logger.error( "Exception listing files in %s. Reason: %s" % ( mc["src_dir_path"], str(err) ))
		traceback.print_exc()
		return 2
			
	if mc["error"] and len(processed_files) == 0:
		logg.error( "0 ebcdic files processed and error flag set." )
		return 2
	else:
		logger.info( "%d files converted from ebcdic to ascii." % ( len(processed_files) ) )
		logger.info( "%d original files deleted after conversion." % ( len(deleted_files) ) )
		return 0

if __name__ == "__main__":
	sys.exit(main());

