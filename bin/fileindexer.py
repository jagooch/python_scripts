#Template for Python Scripts
import os
import sys
import argparse
import re
import logging
import asys

#special case modules
import time
import string
import traceback

#@Version: 1.0 
#@Author: John Gooch
#@Created: 20131106
#@Updated: 20131113
#@Name: File Indexer
#@Description: Creates an index of files in the specified folders.
#@ Tasks


def initCLI():
	parser = argparse.ArgumentParser(description='Python Script Template v1.0')
	parser.add_argument('-i', action="store", dest="input_file_path", required=True, help="Path to the searchDirs input file.")
	parser.add_argument('-o', action="store", dest="output_file_path", required=True, help="Path to the searchDirs output index file.")
	parser.add_argument('-l', action="store", dest="level", required=False, default="INFO",help="Debug level. Default is INFO")
	args = parser.parse_args()
	return args

	
def initLogging( level):
	global logger
	logger = logging.getLogger()
	if not level:
		logger.setLevel(logging.WARNING)
	elif ( level == "DEBUG" ):
		logger.setLevel( logging.DEBUG )
	elif ( level == "INFO" ):
		logger.setLevel( logging.INFO )
	elif ( level == "WARNING" ):
		logger.setLevel( logging.WARNING )
	elif ( level == "ERROR" ):
		logger.setLevel( logging.ERROR )
	elif ( level == "CRITICAL" ):
		logger.setLevel( logging.CRITICAL )
	formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
	ch = logging.StreamHandler()
	ch.setFormatter(formatter)
	logger.addHandler(ch)
	return logger

def loadSearchDirs(input_file_path):
	searchDirs = []
	f = open( input_file_path, 'r' )
	for i,line in enumerate(f):
		line = line.strip()
		if line.startswith("#"):
			logger.debug( "Skipping comment line %s" % ( line ) )
			continue
		else:
			field_count = line.count(",") + 1
			if ( field_count != 4 ): 
				raise Exception( "Invalid field count %d on line %d: %s."  % ( field_count,i, line ) )
			else:
				search_directory = {}
				( search_directory['uc'],search_directory['path'], search_directory['incl'],search_directory['excl'] ) = line.split(',')    
				if re.match( search_directory['incl'], "^$" ):
					search_directory['incl'] = ".*"
				if re.match( search_directory['excl'], "^$" ):
					search_directory['excl'] = "a^"
				searchDirs.append( search_directory )
	f.close()
	return searchDirs

def searchDirs(search_directories):
	indexed_files = []
	for search_directory in search_directories:
		path = os.path.realpath(search_directory['path'])
		logger.info( "Indexing %s" % (  path ) )
		if not os.path.exists(path ):
			raise Exception( "Exception: Search path %s does not exist or is not accessible." % ( path  ) ) 
		new_file_index = indexFiles( search_directory['uc'], search_directory['path'],search_directory['incl'],search_directory['excl'] )
		logger.info( "%d files indexed in directory %s." % ( len(new_file_index), path ) )
		indexed_files.extend( new_file_index )
	return indexed_files
	
#returns an arrary of file with uc,file name, size, modified time
def indexFiles( search_uc, search_path, search_include, search_exclude ):
	indexed_files = []
	files = [f for f in os.listdir(search_path) if re.match( search_include, f) and not re.match( search_exclude, f ) and os.path.isfile( os.path.join( search_path, f) )  ]
	logger.debug( "%d files found in directory %s matching include %s and not matching exclude %s." % ( len(files), search_path, search_include, search_exclude ) )
	str_index_date = time.strftime( "%Y%m%d %H%M%S", time.localtime() )
	for file in files:
		file_path = os.path.join( search_path, file ) 
		stats = os.stat( file_path )
		logger.debug( "Adding " + "%s,%s,%s,%s,%s,%s"  % ( str_index_date, search_uc, search_path, file, stats.st_size,  time.strftime( "%Y%m%d %H%M%S", time.localtime( stats.st_mtime ) ) ) ) 
		indexed_files.append( "%s,%s,%s,%s,%s,%s"  % ( str_index_date,search_uc, search_path, file, stats.st_size,  time.strftime( "%Y%m%d %H%M%S", time.localtime( stats.st_mtime ) ) ) )   
	logger.debug( "%d files indexed." % ( len(indexed_files ) ) )
	return indexed_files
		
# tuple items in order are:
# 0 st_mode (protection bits), 
# 1 st_ino (inode number), 
# 2 st_dev (device),
# 3 st_nlink (number of hard links),
# 4 st_uid (user id of owner),
# 5 st_gid (group id of owner),
# 6 st_size (size of file, in bytes),
# 7 st_atime (time of most recent access),
# 8 st_mtime (time of most recent content modification),
# 9 st_ctime (platform dependent; time of most recent metadata change on Unix, or the time of creation on Windows)
	
	
def writeIndexFile( indexed_files , index_file_path ):
	f = open( index_file_path, 'w' ) 
	#f.write( "index_date, uc,file_path,file_name,file_size,file_modified\n" )
	for indexed_file in indexed_files:
		f.write( "%s\n" % ( indexed_file ) )
	f.flush()
	f.close()
	
	
def main():
	global logger
	global conf
	#global args
	#global indexed_files
	#global search_directories
	args = None # command line arguments
	search_directories = None #array of data dictionaries for uc,path, include, exclude settings
	indexed_files = None # array of file indexes. each index includes uc,path,file name, file size, file modified time
	try:
		args = initCLI()
	except argparse.ArgumentError, err:
		print "Invalid command line syntax. Reason: %s" % ( str(err) ) 
		traceback.print_exc()
		return 2
	except Exception, err:
		print "Failed to parse command line arguments. Reason: %s" % ( str(err) ) 
		traceback.print_exc()
		return 2
	
	try:
		logger = initLogging(args.level)
	except Exception, err:
		print "Failed to initialize logging. Reason: %s" % ( str(err) ) 
		traceback.print_exc()
		return 2

	try:
		search_directories = loadSearchDirs(args.input_file_path)
		logger.info( "Search directory information successfully loaded from %s." %( args.input_file_path ) )
	except Exception, err:
		print "Failed to search directories. Reason: %s" % ( str(err) ) 
		traceback.print_exc()
		return 2
	
	try:
		indexed_files = searchDirs(search_directories)
		logger.info( "%d files successfully indexed." %( len(indexed_files ) ) )
	except Exception, err:
		print "Failed to indexFiles. Reason: %s" % ( str(err) ) 
		traceback.print_exc()
		return 2
		
	try:
		writeIndexFile( indexed_files, args.output_file_path )
		logger.info( "Index file %s successfully created." % ( args.output_file_path ) )
	except Exception, err:
		print "Failed to indexFiles. Reason: %s" % ( str(err) ) 
		traceback.print_exc()
		return 2

	return 0


if __name__ == "__main__":
	sys.exit(main());





