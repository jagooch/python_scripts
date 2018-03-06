import os
import sys
import argparse
import ConfigParser
import logging
import glob
import re
import traceback
import subprocess

#@Version: 1.1 
#@Author: John Gooch
#@Created: 20130110
#@Updated: 20130425
#@Name: Grep utility
#@Description: Searches files for specified text patterns
#@ Tasks
#Version 1.1 20130425 - Fixed bug with case insensitive matching. Added global variable parameter
#Version 1.0 20130122 - core functionality

def initCLI():
	parser = argparse.ArgumentParser(description='Grep Utility 1.0')
	parser.add_argument('-s', action="store", dest="src_dir_path", required=False, default=".",help="Path to directory of files to search. Default .")
	parser.add_argument('-m', action="store", dest="mask",  required=False, default=".*", help="File name pattern of files to search. Default .*")
	parser.add_argument('-p', action="store", dest="pattern",  required=True, help="Search pattern.")
	parser.add_argument('-e', action="store_true", dest="regex", required=False, default=False, help="Pattern is a regular expression.")
	parser.add_argument('-r', action="store_true", dest="recursive", required=False, default=False, help="Folder recursion on. Search files in subdirectories.")
	parser.add_argument('-q', action="store_true", dest="quiet", required=False, default=False, help="Quiet. No output. Just return exit code.")
	parser.add_argument('-i', action="store_true", dest="case_insensitive", required=False, default=False, help="Case insensitive. ignore case whem matching text vs pattern.")
	parser.add_argument('-g', action="store", dest="global_variable", required=False, default=None,help="Global variable to store match count count in. Default is None." )
	parser.add_argument('-l', action="store", dest="level", required=False, default="INFO",help="Debug level. Default is INFO" )
	args = parser.parse_args()
	return args


def initLogging(args):
	global logger
	logger = logging.getLogger()
	if not args.level:
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


def findFiles( path, file_mask, recursive ):
	records = []
	path = os.path.realpath(path)
	logger.debug( "File search path = %s" % ( path ) ) 
	if not os.path.exists( path ):
		raise Exception( "Cannot access path %s. Please check path and permissions." % ( path ) )
	elif not os.path.isdir( path ):
		raise Exception( "%s is not a directory. Please check path." % ( path ) )
	else:
		logger.debug( "Listing files in search path %s" % ( path ) )
		files = os.listdir( path )
		for f in files:
			if not os.path.isfile( os.path.join( path, f )):
				continue
			if re.match( file_mask, f, re.I ):
				records.append( os.path.join( path, f ) ) 
				logger.debug( "Added %s to the list of searchable files." % ( f ) )
	return records
        
def grep( src_dir_path, mask, pattern, recursive, regex, quiet, case_insensitive, global_variable ):
	logger.debug( "src_dir_path=%s file mask=%s pattern=%s recursive=%s regex=%s quiet=%s" % ( src_dir_path, mask, pattern, recursive, regex, quiet )  ) 
	match_count = 0
	files = None
	try:
		files = findFiles( src_dir_path, mask, recursive ) #returns a list of filepaths that match the mask
		logger.debug( "Found %d files to search for text." % ( len(files) ) )
	except Exception, err:
		logger.error( "Fatal error encountered while finding files. Reason: %s" % ( str(err) ) )
		raise
	for file in files:
		logger.debug( "Searching file %s for text %s" % ( file,  pattern ) )
		f = open( file, 'r' ) 
		lines = f.readlines()
		f.close()
		line_number = 0
		for line in lines:
			line = line.strip()
			line_number += 1
			if not regex:
				if case_insensitive:
					if pattern.upper() in line.upper():
						match_count += 1
						if not quiet:
							logger.info( "File:%s Line:%d Text:%s" % ( os.path.basename(file),line_number, line ) )
					else:
						logger.debug( "Pattern %s not in line %s" % ( pattern, line ) )
				else:
					if pattern in line:
						match_count += 1
						if not quiet:
							logger.info( "File:%s Line:%d Text:%s" % ( os.path.basename(file),line_number, line ) )
					else:
						logger.debug( "Pattern %s not in line %s" % ( pattern, line ) )
			elif regex:
				logger.debug( "Matching regex %s against line %s" % ( pattern, line ) )
				if case_insensitive:
					if re.match( pattern, line, re.I ):
						match_count += 1
						if not quiet:
							logger.info( "File:%s Line:%d Text:%s" % ( os.path.basename(file) ,line_number, line ) )
					else:
						logger.debug( "Regex %s does not match line %s because match is null." % ( pattern, line ) )
				else:
					if re.match( pattern, line ):
						match_count += 1
						if not quiet:
							logger.info( "File:%s Line:%d Text:%s" % ( os.path.basename(file) ,line_number, line ) )
					else:
						logger.debug( "Regex %s does not match line %s because match is null." % ( pattern, line ) )
				
			else:
				raise Exception( "Both normal and regex searches are disabled." ) 
	logger.debug( "%d matches found in %d files" % ( match_count, len(files) ) )
	if not quiet:
		logger.info( "%d matches found in %d files" % ( match_count, len(files) ) )

	if global_variable:
		setGV( global_variable, match_count )
			
	if match_count == 0:
		return 1
	else:
		return 0

		
def setGV(gvar, value ):
	cmd = None
	if value is not None:
		cmd = ["sendevent", "-E", "SET_GLOBAL", "-G", "%s=%s" % ( gvar,value )  ]
	else:
		cmd = ["sendevent", "-E", "SET_GLOBAL", "-G", "%s=DELETE" % ( gvar )  ]
	logger.debug( "Executing command %s." %  ( " ".join( cmd ) ) )
	returncode = None
	try:
		returncode = subprocess.call( cmd ) 
	except Exception, err:
		logger.error( "Failed to execute command %s. Reason: %s." % ( " ".join( cmd ), str(err) ) )
		raise
	if returncode != 0:
		raise Exception( "Failed to execute command %s. Exit Code: %d."  % ( " ".join( cmd ), returncode ) )
	else:
		if value:
			logger.debug("Successfully set global variable  %s = %s" %  ( gvar, value ) )
		else:
			logger.debug("Successfully DELETED global variable %s." %  ( gvar ) )
		return 0
		

		
def main():
	global logger
	global conf
	global args
	
	try:
		args = initCLI()
	except argparse.ArgumentError, err:
		print "Invalid command line syntax. Reason: %s" % ( str(err) ) 
		traceback.format_exc()
		return 2
	except Exception, err:
		print "Failed to parse command line arguments. Reason: %s" % ( str(err) ) 
		traceback.format_exc()
		return 2
	
	try:
		logger = initLogging(args)
	except Exception, err:
		print "Failed to initialize logging. Reason: %s" % ( str(err) ) 
		traceback.format_exc()
		return 2

	try:
		return grep( args.src_dir_path, args.mask, args.pattern, args.recursive, args.regex, args.quiet, args.case_insensitive, args.global_variable )
	except Exception, err:
		logger.error( "Failed to search files matching %s in/under path %s. Reason: %s" % ( args.mask, args.src_dir_path, str(err) ) )
		traceback.format_exc()
		return 2
	

if __name__ == "__main__":
	sys.exit(main());





