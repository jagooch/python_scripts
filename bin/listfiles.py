#Template for Python Scripts
import argparse
import logging
import os
import re
import sys

import asys
#special case modules
import time
import traceback

logging.basicConfig(level=logging.INFO)
global logger
logger = logging.getLogger(__name__)


#@Version: 1.3 
#@Author: John Gooch
#@Created: 20130523
#@Updated: 20150626
#@Name: List Files
#@Description:  Lists files in the specified directory. May store the list in specified file. 
#@ Tasks
#20150626 1.3 Add csv output, verbose output switch , and updated various function to current standard. 
#20140417 1.2 Added negative logic and imported findFiles from asys module. 
#20130523 1.1 Fixed file write, integrated with Asys module, adding better error handling and output. 

levels =  { "DEBUG":logging.DEBUG, 
			"INFO":logging.INFO,
			"WARNING":logging.WARNING,
			"ERROR":logging.ERROR,
			"CRITICAL":logging.CRITICAL
			}

def initCLI():
	parser = argparse.ArgumentParser(description='List Files v1.0. Lists file that meet criteria. Can store output in a text file.')
	parser.add_argument('-s', action="store", dest="src_dir_path", required=False, default=".", help="Source file directory paths.")
	parser.add_argument('-m', action="store", dest="mask",  required=False, default=".*", help="File name pattern.")
	parser.add_argument('-o', action="store", dest="output_file_path", required=False, default=None, help="Path to output file list file")
	parser.add_argument('-g', action="store", dest="global_variable", required=False, default=None, help="Global variable to store file count.")
	parser.add_argument('-e', action="store_true", dest="error", required=False, default=False, help="Error flag.")
	parser.add_argument('-n', action="store_true", dest="negative_logic", required=False, default=False, help="Negative logic flag. Returns matched for files that do not matchin file name mask.")
	parser.add_argument('-v', action="store_true", dest="verbose", required=False, default=False, help="Enable verbose output. File name, size, modified time.")
	parser.add_argument('-l', action="store", dest="level", required=False, default="INFO",help="Debug level. Default is INFO")
	args = parser.parse_args()
	return vars(args)

	
def initLogging(level):
	logger.setLevel( levels[level] ) 
	return
	
	
def findFiles( src_dir_path, file_mask, negative_logic ):
	target_files = [] 
	src_dir_path = os.path.realpath( src_dir_path )
	if not os.path.exists( src_dir_path):
		raise Exception( "Source directory path %s is not accessible or does not exist." % (src_dir_path) )
	elif not os.path.isdir( src_dir_path ):
		raise Exception( "Source directory path %s is not a directory." % (src_dir_path))
	else:
		files = os.listdir(src_dir_path)
		for file in files:
			logger.debug( "Processing file %s" % ( file ) ) 
			src_file_path = os.path.join( src_dir_path, file )
			if not os.path.isfile( src_file_path ):
				logger.debug("%s is not a file.Skipping." % ( src_file_path ) )
				continue
			else:
				if re.match( file_mask, file, re.I ):
					target_files.append( src_file_path )
				else:
					logger.debug("%s does not match file name mask %s. Skipping." % ( src_file_path, file_mask ) )
					continue
		return target_files

def writeFileList( file_path, files ):
	dir_path = os.path.realpath( os.path.dirname( file_path ) )
	filename = os.path.basename( file_path )
	if not os.path.exists( dir_path):
		raise Exception( "Cannot access directory %s. Check path and permissions." % ( dir_path ) ) 
	with open( file_path, 'w' ) as f:
		logger.debug( "File %s opened for writing %d files" % ( file_path, len(files) ) )
		#writer file header 
		f.write( "#file_name,file+_mtime,file_size\n")
		for file in files:
			line = ",".join( [ file['file_name'], file['file_mtime'], str(file['file_size']) ]) 	
			f.write( "%s\n" % ( line ) )
			logger.debug( "line %s written." % ( line ) )
		logger.debug( "All files written." )
		f.flush()
		f.close()
		logger.debug( "File %s closed.written." % ( file_path ) )
	return 0
		
def main():
	global logger
	# global args
	file_list = []
	mc = {}
	files = []
	file_count = 0
	try:
		mc.update(initCLI() )
	except argparse.ArgumentError, err:
		print "Invalid command line syntax. Reason: %s" % ( str(err) ) 
		traceback.print_exc()
		return 2
	except Exception, err:
		print "Failed to parse command line arguments. Reason: %s" % ( str(err) ) 
		traceback.print_exc()
		return 2
	
	try:
		initLogging( mc["level"])
	except Exception, err:
		print "Failed to initialize logging. Reason: %s" % ( str(err) ) 
		traceback.print_exc()
		return 2
		
	try:
		files = asys.findFiles(mc["src_dir_path"], mc["mask"], -1, mc["negative_logic"])
		if files:
			file_count = len(files)
		else:
			file_count = 0
		src_file_path = os.path.realpath( mc["src_dir_path"] )
		file_paths = []
		for file in files:
			file_paths.append( os.path.join( src_file_path, file ) )
	except Exception, err:
		print "Failed to initialize logging. Reason: %s" % ( str(err) ) 
		traceback.print_exc()
		return 2
	
	# file_count = len(file_list)
	# logger.debug( "%d files found in path %s matching file name pattern %s" % ( file_count, args.src_dir_path, args.mask ) ) 
	
	for file in file_paths:
		file_name = os.path.basename( file )
		logger.debug( "Full File path is %s. File name is %s." % ( file, file_name  ) )    
		file_mtime = time.strftime( "%Y%m%d %H%M%S", time.localtime( os.stat( file ).st_mtime ) )
		file_size = os.stat( file ).st_size
		file_list.append( { 'file_name':file_name, 'file_mtime':file_mtime, 'file_size':file_size } )
	
	if len(file_list):
		line = None
		for file in file_list:
			if mc["verbose"]:
				line =  ",".join( [ file['file_name'], file['file_mtime'], str(file['file_size']) ]) 	
			else:
				line = "%s" % ( file['file_name'] ) 	
			print line
	
		if mc["output_file_path"]:
			try:
				logger.info("Writing file list to %s." % ( mc["output_file_path"] ) )
				writeFileList( mc["output_file_path"], file_list )
				logger.info("%d files written to list to %s." % (len(file_list),  mc["output_file_path"] ) )
			except Exception, err:
				logger.error( "Failed to write file list to %s. Reason: %s." % ( mc["output_file_path"], str(err) ) )
				traceback.print_exc()
		else:
			logger.debug( "Output file path is %s. No file will be written." %( mc["output_file_path"] ) ) 

	try:
		if mc["global_variable"]:
			asys.setGV(mc["global_variable"], file_count)
	except Exception, err:
		print "Failed to set global variable. Reason: %s" % ( str(err) ) 
		traceback.print_exc()
		return 2

	if mc["error"] and not len(file_list):
		logger.error( "%d files found and error flag is set. Returning Exit Code 1." % ( len(file_list) ) )
		return 1
	else:
		return 0

if __name__ == "__main__":
	sys.exit(main());





